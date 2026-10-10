# --- load_tester.py ---
import asyncio
import aiohttp
import time
import argparse
import signal
import sys
import logging
import json
from dataclasses import dataclass, field
from collections import deque
from urllib.parse import urlparse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("load_tester")


@dataclass
class Config:
    target: str
    concurrency: int = 50
    rate_limit: int = 100        # requests per second
    duration: int = 30           # seconds
    timeout: float = 5.0
    method: str = "GET"
    headers: dict = field(default_factory=dict)
    body: str | None = None
    verify_ssl: bool = True


@dataclass
class Stats:
    sent: int = 0
    success: int = 0
    failed: int = 0
    timeouts: int = 0
    latencies: deque = field(default_factory=lambda: deque(maxlen=10000))
    status_codes: dict = field(default_factory=dict)
    start_time: float = field(default_factory=time.monotonic)

    def record(self, status: int, latency: float) -> None:
        self.sent += 1
        self.latencies.append(latency)
        self.status_codes[status] = self.status_codes.get(status, 0) + 1
        if 200 <= status < 400:
            self.success += 1
        else:
            self.failed += 1

    def record_timeout(self) -> None:
        self.sent += 1
        self.timeouts += 1
        self.failed += 1

    def percentile(self, p: float) -> float:
        if not self.latencies:
            return 0.0
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * p / 100)
        return sorted_lat[min(idx, len(sorted_lat) - 1)]

    def rps(self) -> float:
        elapsed = time.monotonic() - self.start_time
        return self.sent / elapsed if elapsed > 0 else 0.0

    def summary(self) -> dict:
        return {
            "total_requests": self.sent,
            "successful": self.success,
            "failed": self.failed,
            "timeouts": self.timeouts,
            "rps": round(self.rps(), 2),
            "latency_ms": {
                "p50": round(self.percentile(50) * 1000, 2),
                "p90": round(self.percentile(90) * 1000, 2),
                "p95": round(self.percentile(95) * 1000, 2),
                "p99": round(self.percentile(99) * 1000, 2),
                "max": round(max(self.latencies, default=0) * 1000, 2),
            },
            "status_codes": self.status_codes,
        }


class RateLimiter:
    """Token bucket — drains at `rate` tokens/sec, capacity = rate."""

    def __init__(self, rate: int) -> None:
        self.rate = rate
        self.tokens = float(rate)
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
            self.last_refill = now

            if self.tokens < 1:
                wait = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait)
                self.tokens = 0
            else:
                self.tokens -= 1


class LoadTester:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.stats = Stats()
        self.limiter = RateLimiter(config.rate_limit)
        self._stop = asyncio.Event()
        self._active_tasks: set[asyncio.Task] = set()

    def _validate_target(self) -> None:
        parsed = urlparse(self.config.target)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Invalid scheme '{parsed.scheme}' — http/https only")
        if not parsed.netloc:
            raise ValueError("No host in target URL")
        # Refuse RFC-1918 ranges — this tool is for your infrastructure only
        import ipaddress
        try:
            host = parsed.hostname or ""
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                raise ValueError(
                    f"Target resolves to private/loopback address {ip} — "
                    "run this against your own infra, not internal networks"
                )
        except ValueError as e:
            if "private" in str(e) or "loopback" in str(e):
                raise
            # Hostname, not a bare IP — allow it; DNS resolution is the operator's responsibility

    async def _send(self, session: aiohttp.ClientSession) -> None:
        await self.limiter.acquire()
        if self._stop.is_set():
            return

        t0 = time.monotonic()
        try:
            async with session.request(
                method=self.config.method,
                url=self.config.target,
                headers=self.config.headers,
                data=self.config.body,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                ssl=self.config.verify_ssl,
            ) as resp:
                await resp.read()
                latency = time.monotonic() - t0
                self.stats.record(resp.status, latency)
        except asyncio.TimeoutError:
            self.stats.record_timeout()
        except aiohttp.ClientError as e:
            log.debug("Client error: %s", e)
            self.stats.record_timeout()

    async def _worker(self, session: aiohttp.ClientSession) -> None:
        while not self._stop.is_set():
            task = asyncio.create_task(self._send(session))
            self._active_tasks.add(task)
            task.add_done_callback(self._active_tasks.discard)
            await asyncio.sleep(0)

    async def _reporter(self) -> None:
        interval = 2.0
        while not self._stop.is_set():
            await asyncio.sleep(interval)
            s = self.stats
            log.info(
                "RPS: %.1f | Sent: %d | OK: %d | Fail: %d | Timeout: %d | "
                "p50: %.1fms | p95: %.1fms",
                s.rps(), s.sent, s.success, s.failed, s.timeouts,
                s.percentile(50) * 1000,
                s.percentile(95) * 1000,
            )

    async def run(self) -> dict:
        self._validate_target()
        log.info(
            "Starting load test → %s | concurrency=%d | rate=%d rps | duration=%ds",
            self.config.target,
            self.config.concurrency,
            self.config.rate_limit,
            self.config.duration,
        )

        connector = aiohttp.TCPConnector(
            limit=self.config.concurrency,
            ttl_dns_cache=60,
            force_close=False,
            enable_cleanup_closed=True,
        )
        async with aiohttp.ClientSession(connector=connector) as session:
            workers = [
                asyncio.create_task(self._worker(session))
                for _ in range(self.config.concurrency)
            ]
            reporter = asyncio.create_task(self._reporter())

            await asyncio.sleep(self.config.duration)
            self._stop.set()

            for w in workers:
                w.cancel()
            reporter.cancel()

            if self._active_tasks:
                await asyncio.gather(*self._active_tasks, return_exceptions=True)

        summary = self.stats.summary()
        log.info("Test complete.\n%s", json.dumps(summary, indent=2))
        return summary


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="HTTP load tester — authorized targets only")
    parser.add_argument("target", help="Target URL (https://your-service.example.com)")
    parser.add_argument("-c", "--concurrency", type=int, default=50, help="Concurrent workers (default 50)")
    parser.add_argument("-r", "--rate", type=int, default=100, help="Max requests/sec (default 100)")
    parser.add_argument("-d", "--duration", type=int, default=30, help="Test duration in seconds (default 30)")
    parser.add_argument("-t", "--timeout", type=float, default=5.0, help="Per-request timeout seconds (default 5.0)")
    parser.add_argument("-m", "--method", default="GET", choices=["GET", "POST", "PUT", "PATCH", "HEAD"])
    parser.add_argument("-H", "--header", action="append", default=[], metavar="Key:Value")
    parser.add_argument("-b", "--body", default=None, help="Request body string")
    parser.add_argument("--no-verify-ssl", action="store_true", help="Skip TLS verification (staging environments)")
    args = parser.parse_args()

    headers = {}
    for h in args.header:
        if ":" not in h:
            parser.error(f"Malformed header '{h}' — use Key:Value format")
        k, v = h.split(":", 1)
        headers[k.strip()] = v.strip()

    return Config(
        target=args.target,
        concurrency=args.concurrency,
        rate_limit=args.rate,
        duration=args.duration,
        timeout=args.timeout,
        method=args.method,
        headers=headers,
        body=args.body,
        verify_ssl=not args.no_verify_ssl,
    )


async def main() -> None:
    config = parse_args()
    tester = LoadTester(config)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, tester._stop.set)

    await tester.run()


if __name__ == "__main__":
    asyncio.run(main())