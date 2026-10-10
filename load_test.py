"""
═════════════════════════════════════════════════════════════════════════════
HTTP LOAD & STRESS TESTING SUITE (KIỂM THỬ TẢI & HIỆU NĂNG MÁY CHỦ)
Đo lường độ chịu tải, RPS (Requests/giây), độ trễ (Latency) & tỷ lệ lỗi.
═════════════════════════════════════════════════════════════════════════════
"""

import sys
import time
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import statistics
import requests
from urllib.parse import urljoin

# Ensure UTF-8 output encoding on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ANSI Color codes for clean terminal output
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


class LoadTester:
    def __init__(self, base_url, concurrency=10, total_requests=None, duration=None, timeout=5.0, scenario="single"):
        self.base_url = base_url.rstrip("/")
        self.concurrency = concurrency
        self.total_requests = total_requests
        self.duration = duration
        self.timeout = timeout
        self.scenario = scenario

        # Thread safety & telemetry
        self.lock = threading.Lock()
        self.latencies = []
        self.status_codes = Counter()
        self.errors = Counter()
        self.total_bytes = 0
        self.requests_sent = 0
        self.running = False
        self.start_time = 0

        # Define scenario endpoints
        self.endpoints = {
            "single": ["/"],
            "api": ["/api/system/status", "/api/files"],
            "mix": [
                "/",
                "/static/js/app.js",
                "/api/system/status",
                "/api/files",
            ]
        }

    def _worker(self, worker_id):
        session = requests.Session()
        # Custom User-Agent to identify load test requests
        session.headers.update({"User-Agent": f"VideoProMax-LoadTester/1.0 (Worker-{worker_id})"})
        
        endpoint_list = self.endpoints.get(self.scenario, ["/"])
        ep_index = worker_id % len(endpoint_list)

        while self.running:
            # Check stopping conditions
            with self.lock:
                if self.total_requests and self.requests_sent >= self.total_requests:
                    break
                if self.duration and (time.time() - self.start_time) >= self.duration:
                    break
                self.requests_sent += 1
                req_num = self.requests_sent

            target_path = endpoint_list[ep_index % len(endpoint_list)]
            target_url = urljoin(self.base_url + "/", target_path.lstrip("/"))
            ep_index += 1

            t_start = time.perf_counter()
            try:
                resp = session.get(target_url, timeout=self.timeout)
                t_latency = (time.perf_counter() - t_start) * 1000.0  # ms
                body_len = len(resp.content)

                with self.lock:
                    self.latencies.append(t_latency)
                    self.status_codes[resp.status_code] += 1
                    self.total_bytes += body_len
            except requests.exceptions.Timeout:
                with self.lock:
                    self.errors["Timeout (>5s)"] += 1
            except requests.exceptions.ConnectionError:
                with self.lock:
                    self.errors["Connection Refused/Reset"] += 1
            except Exception as e:
                with self.lock:
                    self.errors[type(e).__name__] += 1

        session.close()

    def _print_live_ticker(self):
        while self.running:
            time.sleep(0.1)
            with self.lock:
                done = len(self.latencies) + sum(self.errors.values())
                elapsed = max(time.time() - self.start_time, 0.001)
                rps = done / elapsed
                err_cnt = sum(self.errors.values())
                avg_lat = statistics.mean(self.latencies) if self.latencies else 0.0

            if self.total_requests:
                pct = min(100.0, (done / self.total_requests) * 100)
                sys.stdout.write(
                    f"\r{CYAN}⚡ [Đang test]{RESET} Hoàn tất: {done}/{self.total_requests} ({pct:5.1f}%) | "
                    f"RPS: {GREEN}{rps:6.1f}{RESET} req/s | "
                    f"Độ trễ TB: {YELLOW}{avg_lat:5.1f} ms{RESET} | "
                    f"Lỗi: {RED if err_cnt > 0 else GREEN}{err_cnt}{RESET}   "
                )
            elif self.duration:
                rem = max(0.0, self.duration - elapsed)
                sys.stdout.write(
                    f"\r{CYAN}⚡ [Đang test]{RESET} Thời gian: {elapsed:4.1f}s / {self.duration}s (còn {rem:3.0f}s) | "
                    f"RPS: {GREEN}{rps:6.1f}{RESET} req/s | "
                    f"Độ trễ TB: {YELLOW}{avg_lat:5.1f} ms{RESET} | "
                    f"Lỗi: {RED if err_cnt > 0 else GREEN}{err_cnt}{RESET}   "
                )
            sys.stdout.flush()

    def run(self):
        print(f"\n{BOLD}{'═' * 65}{RESET}")
        print(f"{BOLD}{CYAN}🚀 BẮT ĐẦU KIỂM THỬ HIỆU NĂNG & ĐỘ CHỊU TẢI (LOAD TEST){RESET}")
        print(f"{BOLD}{'═' * 65}{RESET}")
        print(f"  • Mục tiêu (Target):       {BOLD}{self.base_url}{RESET}")
        print(f"  • Luồng đồng thời (Users): {GREEN}{self.concurrency}{RESET} concurrent threads")
        print(f"  • Kịch bản (Scenario):     {YELLOW}{self.scenario.upper()}{RESET} ({', '.join(self.endpoints.get(self.scenario, ['/']))})")
        if self.duration:
            print(f"  • Chế độ kiểm thử:        Thời gian cố định = {BOLD}{self.duration} giây{RESET}")
        else:
            print(f"  • Chế độ kiểm thử:        Tổng số requests = {BOLD}{self.total_requests}{RESET}")
        print(f"  • Timeout tối đa:          {self.timeout} giây / request")
        print(f"{DIM}{'─' * 65}{RESET}\n")

        self.running = True
        self.start_time = time.time()

        # Start live ticker in background thread
        ticker_thread = threading.Thread(target=self._print_live_ticker, daemon=True)
        ticker_thread.start()

        # Execute load with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = [executor.submit(self._worker, i) for i in range(self.concurrency)]
            for f in futures:
                f.result()

        self.running = False
        total_time = max(time.time() - self.start_time, 0.001)

        # Clear ticker line
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()

        # Generate Detailed Report
        self._print_report(total_time)

    def _print_report(self, total_time):
        total_success = len(self.latencies)
        total_errors = sum(self.errors.values())
        total_all = total_success + total_errors
        rps = total_all / total_time
        success_rate = (total_success / total_all * 100.0) if total_all > 0 else 0.0

        print(f"\n{BOLD}{'═' * 65}{RESET}")
        print(f"{BOLD}{GREEN}📊 BÁO CÁO KẾT QUẢ KIỂM THỬ HIỆU NĂNG MÁY CHỦ (BENCHMARK REPORT){RESET}")
        print(f"{BOLD}{'═' * 65}{RESET}\n")

        # 1. Overview Summary
        print(f"{BOLD}1. Tổng quan lưu lượng (Throughput & Traffic):{RESET}")
        print(f"   ├─ Thời gian kiểm thử:      {BOLD}{total_time:.2f} giây{RESET}")
        print(f"   ├─ Tổng số request gửi:    {BOLD}{total_all}{RESET}")
        print(f"   ├─ Số request thành công:  {GREEN}{total_success} ({success_rate:.1f}%){RESET}")
        print(f"   ├─ Số request lỗi/timeout: {RED if total_errors > 0 else GREEN}{total_errors}{RESET}")
        print(f"   ├─ Lưu lượng máy chủ (RPS):{BOLD}{CYAN} {rps:.2f} requests/giây{RESET}")
        print(f"   └─ Băng thông chuyển giao: {BOLD}{self.total_bytes / (1024 * 1024):.2f} MB{RESET} ({self.total_bytes / 1024 / total_time:.1f} KB/s)")

        # 2. Latency Analysis
        print(f"\n{BOLD}2. Phân tích độ trễ phản hồi (Response Latency):{RESET}")
        if self.latencies:
            sorted_lat = sorted(self.latencies)
            min_lat = sorted_lat[0]
            max_lat = sorted_lat[-1]
            avg_lat = statistics.mean(sorted_lat)
            med_lat = statistics.median(sorted_lat)

            def get_percentile(data, p):
                idx = int(len(data) * p)
                idx = min(idx, len(data) - 1)
                return data[idx]

            p90 = get_percentile(sorted_lat, 0.90)
            p95 = get_percentile(sorted_lat, 0.95)
            p99 = get_percentile(sorted_lat, 0.99)

            print(f"   ├─ Nhanh nhất (Fastest):   {GREEN}{min_lat:7.2f} ms{RESET}")
            print(f"   ├─ Trung bình (Average):   {CYAN}{avg_lat:7.2f} ms{RESET}")
            print(f"   ├─ Trung vị (Median / P50):{CYAN}{med_lat:7.2f} ms{RESET}")
            print(f"   ├─ 90% lượt khách (P90):   {YELLOW}{p90:7.2f} ms{RESET}")
            print(f"   ├─ 95% lượt khách (P95):   {YELLOW}{p95:7.2f} ms{RESET}")
            print(f"   ├─ 99% lượt khách (P99):   {RED if p99 > 500 else YELLOW}{p99:7.2f} ms{RESET}")
            print(f"   └─ Chậm nhất (Slowest):    {RED if max_lat > 1000 else YELLOW}{max_lat:7.2f} ms{RESET}")
        else:
            print(f"   └─ {RED}Không có request nào hoàn tất thành công.{RESET}")

        # 3. Status Codes Breakdown
        print(f"\n{BOLD}3. Chi tiết mã phản hồi HTTP (HTTP Status Breakdown):{RESET}")
        if self.status_codes:
            for code, cnt in sorted(self.status_codes.items()):
                pct = (cnt / total_all) * 100.0
                color = GREEN if code < 400 else (YELLOW if code < 500 else RED)
                print(f"   ├─ HTTP {color}{code}{RESET}: {cnt:6d} requests ({pct:5.1f}%)")
        else:
            print(f"   ├─ (Không có mã phản hồi)")

        if self.errors:
            print(f"\n{BOLD}4. Chi tiết các lỗi phát sinh (Errors Encountered):{RESET}")
            for err_msg, cnt in self.errors.items():
                print(f"   ├─ {RED}{err_msg}{RESET}: {cnt} lần")

        # 4. System Rating & Evaluation
        print(f"\n{BOLD}5. Đánh giá sức tải máy chủ (Performance Grade):{RESET}")
        if total_errors == 0 and rps >= 100 and avg_lat < 50:
            print(f"   └─ {GREEN}{BOLD}HẠNG S+ (XUẤT SẮC){RESET}: Máy chủ phản hồi cực nhanh, không lỗi, sẵn sàng chịu tải lớn.")
        elif total_errors == 0 and rps >= 30 and avg_lat < 150:
            print(f"   └─ {GREEN}{BOLD}HẠNG A (RẤT TỐT){RESET}: Máy chủ ổn định, đáp ứng mượt mà nhu cầu người dùng thông thường.")
        elif total_errors < (total_all * 0.05):
            print(f"   └─ {YELLOW}{BOLD}HẠNG B (TRUNG BÌNH){RESET}: Máy chủ chịu tải ở mức vừa phải, có hiện tượng nghẽn nhẹ khi nhiều luồng.")
        else:
            print(f"   └─ {RED}{BOLD}HẠNG C (CẦN TỐI ƯU){RESET}: Tỷ lệ lỗi hoặc độ trễ cao, nên tăng worker thread hoặc bổ sung cache.")

        print(f"{BOLD}{'═' * 65}{RESET}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Tool Kiểm Thử Tải & Đánh Giá Hiệu Năng Máy Chủ Web (HTTP Load & Stress Benchmark)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  1. Kiểm tra nhanh (10 người dùng, 200 request):
     py load_test.py

  2. Kiểm tra áp lực cao (50 luồng đồng thời trong 15 giây):
     py load_test.py --concurrency 50 --duration 15

  3. Kiểm tra kịch bản hỗn hợp (Vừa tải giao diện, vừa gọi API):
     py load_test.py --scenario mix --concurrency 25 --requests 500

  4. Kiểm tra máy chủ từ xa (khi đã mở Cloudflare tunnel / IP LAN):
     py load_test.py --url https://your-domain.com --concurrency 20 --duration 10
        """
    )
    parser.add_argument("--url", default="http://localhost:5000", help="Địa chỉ URL gốc máy chủ cần test (Mặc định: http://localhost:5000)")
    parser.add_argument("-c", "--concurrency", type=int, default=15, help="Số người dùng / luồng truy cập đồng thời (Mặc định: 15)")
    parser.add_argument("-n", "--requests", type=int, default=300, help="Tổng số request cần gửi (Mặc định: 300)")
    parser.add_argument("-d", "--duration", type=int, default=None, help="Chạy liên tục trong N giây (thay vì giới hạn số request)")
    parser.add_argument("-t", "--timeout", type=float, default=5.0, help="Thời gian chờ tối đa cho mỗi request tính bằng giây (Mặc định: 5.0)")
    parser.add_argument(
        "-s", "--scenario",
        choices=["single", "api", "mix"],
        default="mix",
        help="Kịch bản test: 'single' (trang chủ), 'api' (các endpoint JSON), 'mix' (tổng hợp trang chủ + static + api)"
    )

    args = parser.parse_args()

    # Pre-flight check target availability
    try:
        r = requests.get(args.url, timeout=3.0)
        print(f"{GREEN}[OK] Kết nối máy chủ {args.url} thành công (HTTP {r.status_code}){RESET}")
    except Exception as e:
        print(f"{RED}[ERROR] Không thể kết nối tới {args.url} ({e}){RESET}")
        print(f"{YELLOW}Hãy đảm bảo máy chủ web đang chạy trước khi bắt đầu test (ví dụ: py web_app.py --port 5000){RESET}")
        sys.exit(1)

    tester = LoadTester(
        base_url=args.url,
        concurrency=args.concurrency,
        total_requests=args.requests if not args.duration else None,
        duration=args.duration,
        timeout=args.timeout,
        scenario=args.scenario
    )
    tester.run()


if __name__ == "__main__":
    main()
