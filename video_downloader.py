# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║   TOOL TẢI VIDEO PRO v2.14.0 — © Bản quyền: An Nguyễn               ║
║   YouTube • TikTok • Facebook • Instagram • Douyin • 1000+ nền tảng  ║
║   Tải video KHÔNG logo / watermark • Tự động chuẩn hóa MP4           ║
╚══════════════════════════════════════════════════════════════════════╝
Cách dùng:
    py video_downloader.py            -> mở giao diện tương tác CLI (hoặc: python video_downloader.py)
    py video_downloader.py --gui      -> mở giao diện đồ họa GUI
    py video_downloader.py <link>     -> tải nhanh (chất lượng tốt nhất)
"""

import io
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile

# Bật màu ANSI trên Windows console
if sys.platform == "win32":
    os.system("")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Thư mục gốc dự án
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(ROOT_DIR, "bin")
SETTINGS_PATH = os.path.join(ROOT_DIR, "settings.json")

# Kiểm tra thư viện rich
try:
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import (
        BarColumn, DownloadColumn, Progress, SpinnerColumn,
        TextColumn, TimeElapsedColumn, TimeRemainingColumn,
        TransferSpeedColumn,
    )
    from rich.prompt import Confirm, IntPrompt, Prompt
    from rich.rule import Rule
    from rich.table import Table
    from rich.text import Text
except ImportError:
    print("[LỖI] Thiếu thư viện 'rich'. Chạy lệnh: py -m pip install -U rich")
    sys.exit(1)

# Kiểm tra thư viện yt_dlp
try:
    from yt_dlp import YoutubeDL
    from yt_dlp.utils import DownloadError, ExtractorError
except ImportError:
    print("[LỖI] Chưa cài đặt yt-dlp. Chạy lệnh: py -m pip install -U yt-dlp")
    sys.exit(1)

# Thư viện tùy chọn: pyperclip (Clipboard)
try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

VERSION = "2.14.0"
AUTHOR = "An Nguyễn"
COPYRIGHT = f"© 2026 {AUTHOR} — Bảo lưu mọi quyền"
console = Console()

# ─────────────────────────────────────────────────────────── CẤU HÌNH (SETTINGS)
DEFAULT_SETTINGS = {
    "avg_speed": 2000000,
    "default_quality": "best",
    "default_output": "downloads",
    "auto_open_folder": True,
    "merge_mp4": True,
    "embed_thumbnail": True,
    "add_metadata": True,
    "audio_bitrate": "192",
    "concurrent_fragments": 8,
    "check_updates": True,
}


def load_settings():
    """Đọc cấu hình từ settings.json hoặc nạp mặc định."""
    cfg = DEFAULT_SETTINGS.copy()
    if os.path.isfile(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    cfg.update(saved)
        except Exception:
            pass
    return cfg


def save_settings(cfg):
    """Lưu cấu hình vào settings.json."""
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def record_speeds(results):
    """Lưu tốc độ tải trung bình (EMA) để ước lượng ETA chính xác hơn."""
    speeds = [
        r["size"] / r["time"]
        for r in results
        if r.get("ok") and r.get("time") and r.get("size")
    ]
    if not speeds:
        return
    cfg = load_settings()
    batch = sum(speeds) / len(speeds)
    old = cfg.get("avg_speed")
    cfg["avg_speed"] = int(0.6 * batch + 0.4 * old) if old else int(batch)
    save_settings(cfg)


# ─────────────────────────────────────────────────────────── BANNER & THÔNG BÁO
BANNER = r"""
██╗   ██╗███████╗ ██████╗██████╗  ██████╗ 
██║   ██║██╔════╝██╔════╝██╔══██╗██╔═══██╗
██║   ██║█████╗  ██║     ██║  ██║██║   ██║
╚██╗ ██╔╝██╔══╝  ██║     ██║  ██║██║   ██║
 ╚████╔╝ ███████╗╚██████╗██████╔╝╚██████╔╝
  ╚═══╝  ╚══════╝ ╚═════╝╚═════╝  ╚═════╝ """

BANNER_STYLES = [
    "bold bright_cyan", "bold cyan", "bold blue",
    "bold magenta", "bold bright_magenta", "bold bright_cyan",
]

WHATS_NEW = (
    f"[bold bright_magenta]★ ĐIỂM NỔI BẬT TRÊN BẢN {VERSION}[/]\n"
    "[bright_cyan]►[/] [bold]Chuẩn hóa MP4 100%[/]: Tự động gộp video và âm thanh thành MP4 tương thích mọi thiết bị, CapCut, Premiere.\n"
    "[bright_cyan]►[/] [bold]FFmpeg Portable 1-Click[/]: Tự động tải và chạy FFmpeg trong thư mục nội bộ `bin/`, không cần quyền Admin.\n"
    "[bright_cyan]►[/] [bold]Chống chặn YouTube 2026[/]: Tối ưu Client Spoofing (Android/Web/TV) chống lỗi 403 Forbidden và bóp băng thông.\n"
    "[bright_cyan]►[/] [bold]Tải đa nguồn & Clipboard[/]: Hỗ trợ đọc từ `links.txt`, dán nhanh từ Clipboard, hỗ trợ Playlist linh hoạt.\n"
    "[bright_cyan]►[/] [bold]Bộ công cụ Toolbox[/]: Tích hợp sẵn cắt video offline và chuyển đổi định dạng MP3/MP4 cực nhanh."
)

QUALITIES = [
    ("best", "Tốt nhất (bản cao nhất có sẵn: 4K/2K/1080p)"),
    ("2160", "2160p — 4K Ultra HD"),
    ("1440", "1440p — 2K QHD"),
    ("1080", "1080p — Full HD"),
    ("720",  "720p — HD"),
    ("480",  "480p — SD"),
    ("360",  "360p — Tiết kiệm dung lượng"),
]

AUDIO_BITRATES = [
    ("320", "320 kbps (Chất lượng Studio cao nhất)"),
    ("192", "192 kbps (Chất lượng tiêu chuẩn phổ biến)"),
    ("128", "128 kbps (Tiết kiệm dung lượng)"),
]

BROWSERS = ["chrome", "edge", "firefox", "brave", "opera", "vivaldi"]
ASSUME_SPEED = 10 * 1024 * 1024


def show_banner():
    console.print()
    for line, style in zip(BANNER.strip("\n").splitlines(), BANNER_STYLES):
        console.print(f"  {line}", style=style)
    console.print(
        Panel(
            "[bold cyan]TOOL TẢI VIDEO & ÂM THANH PRO MAX[/]  [dim]•[/]  "
            "YouTube [dim]•[/] TikTok [dim]•[/] Facebook [dim]•[/] "
            "Instagram [dim]•[/] Douyin [dim]•[/] 1000+ nền tảng\n"
            "[dim]Tự động xóa logo • Không watermark • Ghép MP4 chuẩn • Hỗ trợ tải hàng loạt[/]",
            title=f"[bold black on bright_cyan] PRO v{VERSION} [/]",
            subtitle=f"[bold bright_yellow]{AUTHOR}[/] [dim]•[/] [dim]{COPYRIGHT}[/]",
            border_style="bright_blue", box=box.DOUBLE, expand=False,
        )
    )
    console.print()


# ─────────────────────────────────────────────────────────── FFMPEG ENGINE
def find_ffmpeg():
    """Tìm ffmpeg: trong thư mục bin nội bộ, PATH hoặc WinGet."""
    # 1. Thư mục bin nội bộ của dự án
    local_bin = os.path.join(BIN_DIR, "ffmpeg.exe")
    if os.path.isfile(local_bin):
        return local_bin

    # 2. Thư mục gốc dự án
    root_bin = os.path.join(ROOT_DIR, "ffmpeg.exe")
    if os.path.isfile(root_bin):
        return root_bin

    # 3. Trong biến môi trường PATH
    exe = shutil.which("ffmpeg")
    if exe:
        return exe

    # 4. Thư mục cài đặt winget thông dụng
    local_app = os.environ.get("LOCALAPPDATA", "")
    if local_app:
        winget_links = os.path.join(local_app, "Microsoft", "WinGet", "Links")
        exe = shutil.which("ffmpeg", path=winget_links)
        if exe:
            return exe
        pkg_dir = os.path.join(local_app, "Microsoft", "WinGet", "Packages")
        if os.path.isdir(pkg_dir):
            for entry in os.listdir(pkg_dir):
                if entry.lower().startswith("gyan.ffmpeg"):
                    for base, _dirs, files in os.walk(os.path.join(pkg_dir, entry)):
                        if "ffmpeg.exe" in files:
                            return os.path.join(base, "ffmpeg.exe")
    return None


def download_portable_ffmpeg():
    """Tải và giải nén FFmpeg Portable trực tiếp vào thư mục bin của dự án."""
    import urllib.request

    os.makedirs(BIN_DIR, exist_ok=True)
    target_exe = os.path.join(BIN_DIR, "ffmpeg.exe")
    if os.path.isfile(target_exe):
        console.print("  [bright_green][OK] FFmpeg Portable đã có sẵn trong thư mục bin![/]")
        return target_exe

    console.print(Panel(
        "[bold cyan]TỰ ĐỘNG TẢI FFMPEG PORTABLE (TIỆN LỢI & KHÔNG CẦN ADMIN)[/]\n"
        "• FFmpeg là công cụ bắt buộc để ghép video chất lượng cao (1080p, 2K, 4K) và xuất MP3.\n"
        "• Bản portable sẽ được tải và lưu vào thư mục `bin/` của tool.\n"
        "• Quá trình này chỉ cần thực hiện 1 lần duy nhất.",
        border_style="cyan", box=box.ROUNDED
    ))

    # Link tải trực tiếp bản essentials từ Gyan (nhanh và ổn định)
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_path = os.path.join(BIN_DIR, "ffmpeg_temp.zip")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            total_size = int(response.headers.get("content-length", 0))

            progress_columns = [
                SpinnerColumn(style="bright_cyan"),
                TextColumn("[bold cyan]Đang tải FFmpeg Essentials..."),
                BarColumn(complete_style="bright_green", finished_style="bright_green"),
                "[progress.percentage]{task.percentage:>3.0f}%",
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
            ]

            with Progress(*progress_columns, console=console) as prog:
                task = prog.add_task("dl", total=total_size)
                with open(zip_path, "wb") as out_file:
                    block_size = 1024 * 1024  # 1MB
                    while True:
                        buf = response.read(block_size)
                        if not buf:
                            break
                        out_file.write(buf)
                        prog.update(task, advance=len(buf))

        console.print("  [bright_cyan]Đang giải nén ffmpeg.exe & ffprobe.exe vào bin/...[/]")
        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.namelist():
                base_name = os.path.basename(member)
                if base_name in ("ffmpeg.exe", "ffprobe.exe"):
                    source = zf.open(member)
                    target = open(os.path.join(BIN_DIR, base_name), "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)

        if os.path.exists(zip_path):
            os.remove(zip_path)

        if os.path.isfile(target_exe):
            console.print(f"  [bright_green][OK] Cài đặt FFmpeg Portable thành công tại: {target_exe}[/]\n")
            return target_exe
        else:
            console.print("  [red][X] Giải nén thất bại, không tìm thấy file ffmpeg.exe![/]\n")
            return None

    except Exception as e:
        console.print(f"  [red][X] Lỗi trong quá trình tải FFmpeg: {e}[/]")
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except Exception:
                pass
        return None


def intro_loading(ffmpeg_path):
    """Hiển thị trạng thái khởi động hệ thống mượt mà."""
    steps = [
        ("Khởi tạo Engine yt-dlp 2026", True),
        ("Kiểm tra bộ giải mã FFmpeg", bool(ffmpeg_path)),
        ("Cấu hình tăng tốc đường truyền", True),
    ]
    for msg, ok in steps:
        with console.status(f"  [cyan]Đang {msg.lower()}...[/]", spinner="dots", spinner_style="bright_cyan"):
            time.sleep(0.12)
        if ok:
            console.print(f"  [bright_green][OK] {msg}[/]")
        else:
            console.print(f"  [yellow][!!] {msg} — chưa phát hiện (bạn có thể tải tự động tại Menu)[/]")
    console.print()


# ─────────────────────────────────────────────────────────── TIỆN ÍCH DỮ LIỆU
def human_duration(sec):
    if not sec:
        return "—"
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def human_size(num_bytes):
    if not num_bytes:
        return "—"
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}" if unit != "B" else f"{int(num_bytes)} B"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


def detect_browser():
    """Tự nhận diện trình duyệt có sẵn để lấy cookie khi gặp video riêng tư."""
    roots = [
        os.environ.get("LOCALAPPDATA", ""),
        os.environ.get("PROGRAMFILES", ""),
        os.environ.get("PROGRAMFILES(X86)", ""),
    ]
    candidates = [
        ("chrome", [r"Google\Chrome\Application\chrome.exe"]),
        ("edge", [r"Microsoft\Edge\Application\msedge.exe"]),
        ("firefox", [r"Mozilla Firefox\firefox.exe"]),
        ("brave", [r"BraveSoftware\Brave-Browser\Application\brave.exe"]),
        ("opera", [r"Opera\launcher.exe", r"Opera\opera.exe"]),
    ]
    for name, rels in candidates:
        for root in roots:
            if not root:
                continue
            for rel in rels:
                if os.path.exists(os.path.join(root, rel)):
                    return name
    return None


AUTH_KEYWORDS = (
    "login", "log in", "sign in", "cookie", "private",
    "age-restricted", "confirm your age", "authentication",
    "members only", "requires an account"
)


def is_auth_error(msg):
    low = (msg or "").lower()
    return any(k in low for k in AUTH_KEYWORDS)


# ─────────────────────────────────────────────────────────── CORE YT-DLP BUILDER
def build_ydl_opts(quality, audio, out_dir, ffmpeg_path, browser=None, subs=None,
                   audio_bitrate="192", progress_hook=None, pp_hook=None,
                   is_playlist=False):
    """Xây dựng cấu hình yt-dlp tối ưu cho năm 2026."""
    cfg = load_settings()
    postprocessors = []

    if audio:
        fmt = "bestaudio/best"
        if ffmpeg_path:
            postprocessors.append({
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": str(audio_bitrate),
            })
            if cfg.get("embed_thumbnail", True):
                postprocessors.append({"key": "FFmpegThumbnailsConvertor", "format": "jpg"})
                postprocessors.append({"key": "EmbedThumbnail"})
            if cfg.get("add_metadata", True):
                postprocessors.append({"key": "FFmpegMetadata"})
    elif quality == "best":
        fmt = "bestvideo*+bestaudio/best"
    else:
        fmt = f"bestvideo*[height<={quality}]+bestaudio/best[height<={quality}]/best"

    os.makedirs(out_dir, exist_ok=True)

    # Đặt template tên file
    if is_playlist:
        tmpl = os.path.join(out_dir, "%(playlist_title,playlist)s", "%(playlist_index)s - %(title)s [%(id)s].%(ext)s")
    else:
        tmpl = os.path.join(out_dir, "%(title)s [%(id)s].%(ext)s")

    opts = {
        "format": fmt,
        "outtmpl": tmpl,
        "postprocessors": postprocessors,
        "noplaylist": not is_playlist,
        "windowsfilenames": True,
        "quiet": True,
        "noprogress": True,
        "no_warnings": True,
        "concurrent_fragment_downloads": cfg.get("concurrent_fragments", 8),
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 30,
        # Chống 403 Forbidden & Throttling từ YouTube năm 2026
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web", "tv"],
            }
        },
    }

    # Bắt buộc gộp về định dạng MP4 để tương thích tuyệt đối với Windows & Premiere/CapCut
    if not audio and cfg.get("merge_mp4", True) and ffmpeg_path:
        opts["merge_output_format"] = "mp4"

    if progress_hook:
        opts["progress_hooks"] = [progress_hook]
    if pp_hook:
        opts["postprocessor_hooks"] = [pp_hook]
    if ffmpeg_path:
        opts["ffmpeg_location"] = os.path.dirname(ffmpeg_path)
    if browser:
        opts["cookiesfrombrowser"] = (browser,)

    if subs:
        opts.update({
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["all"] if subs == "all" else [subs],
            "subtitlesformat": "srt/best",
        })

    return opts


def show_video_panel(info):
    """Hiện bảng tóm tắt thông tin video trước khi tải."""
    tb = Table.grid(padding=(0, 2))
    tb.add_column(style="bold cyan", justify="right")
    tb.add_column(style="white", overflow="fold")
    tb.add_row("Nền tảng", str(info.get("extractor_key", "?")).title())
    tb.add_row("Tiêu đề", str(info.get("title", "?")))
    tb.add_row("Kênh / Tác giả", str(info.get("uploader") or info.get("channel") or "—"))
    tb.add_row("Thời lượng", human_duration(info.get("duration")))
    views = info.get("view_count")
    tb.add_row("Lượt xem", f"{views:,}".replace(",", ".") if views else "—")
    console.print(Panel(tb, title="[bold bright_green]THÔNG TIN VIDEO[/]", border_style="green", box=box.ROUNDED))


def estimate_size(info):
    fs = info.get("filesize") or info.get("filesize_approx")
    if fs:
        return int(fs)
    rate = info.get("tbr") or ((info.get("abr") or 0) + (info.get("vbr") or 0))
    dur = info.get("duration")
    if rate and dur:
        return int(rate * 1000 / 8 * dur)
    return None


def fetch_previews(urls, quality, audio, out_dir, ffmpeg_path, browser=None, subs=None):
    """Phân tích các link để lấy thông tin sơ bộ và ước tính dung lượng."""
    previews = []
    opts = build_ydl_opts(quality, audio, out_dir, ffmpeg_path, browser, subs=subs)
    with console.status(f"  [cyan]Đang phân tích {len(urls)} đường link...[/]", spinner="dots", spinner_style="cyan"):
        with YoutubeDL(opts) as ydl:
            for url in urls:
                try:
                    inf = ydl.extract_info(url, download=False)
                    if "_type" in inf and inf["_type"] == "playlist":
                        entries = list(inf.get("entries") or [])
                        previews.append({
                            "url": url, "ok": True,
                            "title": f"[Playlist] {inf.get('title', 'Danh sách phát')} ({len(entries)} video)",
                            "platform": str(inf.get("extractor_key", "?")).title(),
                            "duration": sum((e.get("duration") or 0) for e in entries if isinstance(e, dict)),
                            "size": sum((estimate_size(e) or 0) for e in entries if isinstance(e, dict)),
                            "is_playlist": True,
                        })
                    else:
                        previews.append({
                            "url": url, "ok": True,
                            "title": inf.get("title", "?"),
                            "platform": str(inf.get("extractor_key", "?")).title(),
                            "duration": inf.get("duration"),
                            "size": estimate_size(inf),
                            "is_playlist": False,
                        })
                except Exception:
                    previews.append({
                        "url": url, "ok": False, "title": url,
                        "platform": "—", "duration": None, "size": None,
                        "is_playlist": False,
                    })
    return previews


def show_preview_panel(previews, real_speed=None):
    """Hiển thị bảng chi tiết danh sách chuẩn bị tải kèm ước tính thời gian."""
    tb = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan", border_style="bright_blue", padding=(0, 1))
    tb.add_column("#", justify="center", style="bold bright_cyan", width=3)
    tb.add_column("TIÊU ĐỀ", style="white", max_width=40, overflow="ellipsis")
    tb.add_column("NỀN TẢNG", style="magenta", justify="center")
    tb.add_column("THỜI LƯỢNG", justify="right", style="yellow")
    tb.add_column("DUNG LƯỢNG*", justify="right", style="cyan")

    tot_dur, tot_size = 0, 0
    for i, p in enumerate(previews, 1):
        if p["ok"]:
            tot_dur += p["duration"] or 0
            tot_size += p["size"] or 0
        tb.add_row(
            str(i), p["title"], p["platform"],
            human_duration(p["duration"]) if p["ok"] else "—",
            human_size(p["size"]) if p["size"] else "—"
        )
    console.print(Panel(tb, title="[bold]DANH SÁCH SẼ TẢI[/]", border_style="blue", box=box.ROUNDED))

    speed = real_speed or ASSUME_SPEED
    eta = f"~{human_duration(tot_size / speed)}" if tot_size else "—"
    note = f"tốc độ thực tế ~{human_size(speed)}/s" if real_speed else "giả định ~10 MB/s"

    console.print(Panel(
        f"[bold]Tổng số mục:[/] {len(previews)}  •  "
        f"[bold]Tổng thời lượng:[/] [yellow]{human_duration(tot_dur) if tot_dur else '—'}[/]  •  "
        f"[bold]Tổng dung lượng ước tính:[/] [cyan]{human_size(tot_size) if tot_size else '—'}[/]\n"
        f"[bold]Ước tính thời gian tải:[/] [bright_green]{eta}[/] [dim]({note})[/]",
        border_style="bright_blue", box=box.DOUBLE
    ))


def find_result_file(out_dir, video_id):
    """Tìm file vừa tải xong theo ID một cách an toàn."""
    marker = f"[{video_id}]."
    best = None
    try:
        for root, _dirs, files in os.walk(out_dir):
            for fname in files:
                if marker in fname:
                    full_path = os.path.join(root, fname)
                    mtime = os.path.getmtime(full_path)
                    if best is None or mtime > best[1]:
                        best = (full_path, mtime)
    except OSError:
        pass
    return best[0] if best else None


# ─────────────────────────────────────────────────────────── QUY TRÌNH TẢI XUỐNG
def run_downloads(urls, quality, audio, out_dir, ffmpeg_path, browser=None, subs=None,
                  audio_bitrate="192", is_playlist=False):
    """Thực thi quá trình tải với thanh tiến trình animation thời gian thực."""
    results = []
    task_map = {}
    pp_shown = set()

    def hook(d):
        if d["status"] == "downloading":
            fname = os.path.basename(d.get("filename", ""))
            tid = task_map.get(fname)
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            if tid is None:
                tid = progress.add_task("dl", filename=fname, total=total)
                task_map[fname] = tid
            progress.update(tid, total=total, completed=d.get("downloaded_bytes", 0))
        elif d["status"] == "finished":
            fname = os.path.basename(d.get("filename", ""))
            tid = task_map.get(fname)
            if tid is not None:
                t = progress.tasks[tid]
                progress.update(tid, completed=t.total or t.completed)

    def pp_hook(d):
        if d.get("status") == "started":
            pp = d.get("postprocessor", "")
            if pp == "ExtractAudio":
                fname = os.path.basename(d.get("info_dict", {}).get("filepath", ""))
                if fname not in pp_shown:
                    pp_shown.add(fname)
                    progress.console.print("  [magenta]► Đang chuyển đổi sang định dạng MP3...[/]")
            elif pp == "Merger":
                progress.console.print("  [cyan]► Đang ghép video và âm thanh thành MP4...[/]")

    opts = build_ydl_opts(
        quality, audio, out_dir, ffmpeg_path, browser=browser, subs=subs,
        audio_bitrate=audio_bitrate, progress_hook=hook, pp_hook=pp_hook,
        is_playlist=is_playlist
    )

    columns = [
        SpinnerColumn(style="bright_cyan", finished_text="[bright_green]■[/]"),
        TextColumn("[bold cyan]{task.fields[filename]}", justify="left"),
        BarColumn(bar_width=None, complete_style="bright_green", finished_style="bright_green", pulse_style="blue"),
        "[progress.percentage]{task.percentage:>3.0f}%",
        DownloadColumn(),
        TransferSpeedColumn(),
        "[dim]còn[/]", TimeRemainingColumn(),
        "[dim]mất[/]", TimeElapsedColumn(),
    ]

    with YoutubeDL(opts) as ydl, Progress(*columns, console=console, expand=True) as progress:
        for idx, url in enumerate(urls, 1):
            progress.console.rule(f"[bold]Mục {idx}/{len(urls)}[/]  [dim]{url[:75]}[/]", style="bright_blue")
            t0 = time.time()

            def download_with(dl):
                with console.status("  [cyan]Đang kết nối & phân tích...[/]", spinner="dots", spinner_style="cyan"):
                    inf = dl.extract_info(url, download=False)
                show_video_panel(inf)
                with console.status("  [cyan]Đang chuẩn bị tải...[/]", spinner="aesthetic", spinner_style="magenta"):
                    time.sleep(0.2)
                dl.download([url])
                return inf

            info, err = None, None
            try:
                info = download_with(ydl)
            except (DownloadError, ExtractorError) as e:
                err = str(e).split("\n")[0][:120]
                # Tự động lấy cookies từ trình duyệt nếu video cần đăng nhập
                if is_auth_error(err) and not browser:
                    det = detect_browser()
                    if det:
                        progress.console.print(
                            f"  [yellow][!!] Phát hiện video riêng tư / hạn chế — Tự động lấy cookies từ {det.title()}...[/]"
                        )
                        opts2 = build_ydl_opts(
                            quality, audio, out_dir, ffmpeg_path, browser=det, subs=subs,
                            audio_bitrate=audio_bitrate, progress_hook=hook, pp_hook=pp_hook,
                            is_playlist=is_playlist
                        )
                        try:
                            with YoutubeDL(opts2) as ydl2:
                                info = download_with(ydl2)
                            err = None
                        except (DownloadError, ExtractorError) as e2:
                            err = str(e2).split("\n")[0][:120]
            except KeyboardInterrupt:
                progress.console.print("\n  [yellow][!!] Đã hủy phiên tải hiện tại.[/]")
                break

            if info is not None:
                elapsed = time.time() - t0
                video_id = info.get("id", "")
                fpath = find_result_file(out_dir, video_id)
                fsize = os.path.getsize(fpath) if fpath and os.path.exists(fpath) else 0
                results.append({
                    "title": info.get("title", "?"),
                    "platform": str(info.get("extractor_key", "?")).title(),
                    "size": fsize, "time": elapsed, "ok": True, "file": fpath,
                })
                progress.console.print(f"  [bright_green][OK] Tải hoàn tất trong {elapsed:.1f}s — Dung lượng: {human_size(fsize)}[/]\n")
            else:
                results.append({
                    "title": url, "platform": "—", "size": 0,
                    "time": time.time() - t0, "ok": False, "file": err,
                })
                progress.console.print(f"  [red][X] Lỗi tải: {err}[/]")
                if is_auth_error(err or ""):
                    progress.console.print("  [yellow]→ Hãy đăng nhập tài khoản trên trình duyệt và thử lại.[/]")
                progress.console.print()

    return results


# ─────────────────────────────────────────────────────────── CẮT & XỬ LÝ MEDIA
AUDIO_EXTS = {".mp3", ".m4a", ".opus", ".ogg", ".wav", ".aac", ".flac"}


def cut_media_file(fpath, start, end, ffmpeg_path):
    """Cắt file media chính xác từng mili-giây bằng FFmpeg."""
    base, ext = os.path.splitext(fpath)
    out = f"{base} [cut {start:g}-{end:g}s]{ext}"
    cmd = [
        ffmpeg_path, "-y", "-hide_banner", "-loglevel", "error",
        "-ss", f"{start:.3f}", "-i", fpath, "-t", f"{end - start:.3f}"
    ]
    if ext.lower() in AUDIO_EXTS:
        cmd += ["-vn", "-c:a", "copy"]
    else:
        # Re-encode frame-accurate với H.264
        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac"]
    cmd.append(out)

    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0 or not os.path.exists(out):
        detail = (r.stderr or "Lỗi không xác định").strip().splitlines()[-1][:120]
        raise RuntimeError(detail)
    return out


def apply_cut(results, cut, ffmpeg_path):
    """Cắt hàng loạt các file vừa tải thành công."""
    start, end = cut
    console.print(Rule(f"[bold bright_magenta]ĐANG CẮT FILE {start:g}s → {end:g}s[/]", style="magenta"))
    for r in results:
        if not (r.get("ok") and r.get("file") and os.path.exists(r["file"])):
            continue
        fname = os.path.basename(r["file"])
        try:
            with console.status(f"  [magenta]Đang cắt {fname[:50]}...[/]", spinner="dots", spinner_style="magenta"):
                new_path = cut_media_file(r["file"], start, end, ffmpeg_path)
            r["file"] = new_path
            r["size"] = os.path.getsize(new_path)
            console.print(f"  [bright_green][OK] Đã cắt xong:[/] [cyan]{os.path.basename(new_path)}[/]")
        except Exception as e:
            console.print(f"  [red][X] Lỗi cắt ({e}) — Đã giữ nguyên file gốc.[/]")
    console.print()


def show_summary(results, out_dir):
    """Bảng tổng kết sau khi tải xong toàn bộ."""
    tb = Table(title="KẾT QUẢ TẢI XUỐNG", box=box.HEAVY, border_style="bright_blue",
               title_style="bold bright_cyan", header_style="bold cyan")
    tb.add_column("#", justify="center", style="dim", width=3)
    tb.add_column("TIÊU ĐỀ", style="white", max_width=45, overflow="ellipsis")
    tb.add_column("NỀN TẢNG", style="magenta", justify="center")
    tb.add_column("DUNG LƯỢNG", justify="right", style="cyan")
    tb.add_column("THỜI GIAN", justify="right", style="yellow")
    tb.add_column("TỐC ĐỘ", justify="right", style="bright_magenta")
    tb.add_column("TRẠNG THÁI", justify="center")

    for i, r in enumerate(results, 1):
        speed = (f"{human_size(r['size'] / r['time'])}/s" if r["ok"] and r["time"] and r["size"] else "—")
        tb.add_row(
            str(i), r["title"], r["platform"],
            human_size(r["size"]) if r["ok"] else "—",
            f"{r['time']:.1f}s", speed,
            "[bright_green]THÀNH CÔNG[/]" if r["ok"] else "[red]THẤT BẠI[/]"
        )
    console.print()
    console.print(tb)
    ok = sum(1 for r in results if r["ok"])
    console.print(Panel.fit(
        f"[bold]Tổng kết:[/] [bright_green]{ok} thành công[/]  "
        f"{f'[red]{len(results) - ok} thất bại[/]' if ok < len(results) else ''}\n"
        f"[bold]Thư mục lưu trữ:[/] [cyan]{out_dir}[/]",
        border_style="bright_green" if ok == len(results) else "yellow",
        box=box.DOUBLE
    ))


def open_result_folder(results, out_dir):
    """Mở thư mục lưu file trên Windows Explorer."""
    cfg = load_settings()
    if not cfg.get("auto_open_folder", True):
        return

    ok_files = [r["file"] for r in results if r.get("ok") and r.get("file") and os.path.exists(r["file"])]
    try:
        if ok_files:
            subprocess.Popen(f'explorer /select,"{ok_files[-1]}"')
        elif os.path.isdir(out_dir):
            os.startfile(out_dir)
    except Exception:
        try:
            subprocess.Popen(f'explorer "{out_dir}"')
        except Exception:
            pass


# ─────────────────────────────────────────────────────────── CÁC BƯỚC NHẬP LIỆU (WIZARD)
def parse_urls_from_text(raw):
    urls = [u.strip().strip(",") for u in raw.replace("\n", " ").split() if u.strip()]
    return list(dict.fromkeys([u for u in urls if u.startswith("http")]))


def ask_urls():
    """Hỏi link từ người dùng, hỗ trợ xem trợ giúp 'help'."""
    while True:
        console.print(Panel(
            "[bold]DÁN ĐƯỜNG LINK VIDEO VÀO ĐÂY[/]\n"
            "[dim]Hỗ trợ: YouTube, TikTok, Facebook, Instagram, Douyin, X/Twitter, Vimeo...\n"
            "Có thể dán nhiều link cùng lúc (cách nhau bằng dấu cách hoặc xuống dòng)[/]",
            title="[bold cyan]BƯỚC 1/5 • NHẬP LINK[/]",
            border_style="cyan", box=box.ROUNDED
        ))
        raw = Prompt.ask("  [bold bright_cyan]► Link[/]", default="")
        if raw.strip().lower() == "help":
            console.print(Panel(
                "[bold cyan]HƯỚNG DẪN CHI TIẾT[/]\n"
                "  1. Dán link video trực tiếp hoặc tải hàng loạt bằng file links.txt\n"
                "  2. Chọn tải Video hoặc Âm thanh MP3\n"
                "  3. Chọn chất lượng (Tốt nhất, 4K, 1080p, 720p...)\n"
                "  4. Video tải về tự động loại bỏ watermark và gộp thành MP4 chuẩn\n"
                "  5. Nhấn Ctrl+C bất cứ lúc nào để hủy thao tác",
                title="[bold]TRỢ GIÚP[/]", border_style="bright_blue", box=box.ROUNDED
            ))
            continue

        urls = parse_urls_from_text(raw)
        if urls:
            console.print(f"  [bright_green][OK] Đã nhận {len(urls)} đường link hợp lệ[/]\n")
            return urls
        console.print("  [red][X] Đường link không hợp lệ! Vui lòng bắt đầu bằng http:// hoặc https://[/]\n")


def load_urls_from_file(file_path="links.txt"):
    """Đọc link từ file văn bản."""
    full_path = os.path.join(ROOT_DIR, file_path) if not os.path.isabs(file_path) else file_path
    if not os.path.isfile(full_path):
        console.print(f"  [yellow][!!] Không tìm thấy file `{os.path.basename(full_path)}`.[/]")
        with open(full_path, "w", encoding="utf-8") as f:
            f.write("# Dán mỗi dòng 1 link video vào đây\n")
        console.print(f"  [bright_green][OK] Đã tự tạo file `{os.path.basename(full_path)}`. Hãy dán link vào file rồi thử lại![/]\n")
        return []

    urls = []
    with open(full_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and line.startswith("http"):
                urls.append(line)
    urls = list(dict.fromkeys(urls))
    return urls


def load_urls_from_clipboard():
    """Lấy link từ clipboard hệ thống."""
    if not HAS_PYPERCLIP:
        console.print("  [yellow][!!] Thư viện pyperclip chưa được cài. Đang tự cài đặt...[/]")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyperclip"], capture_output=True)
        return []

    raw = pyperclip.paste()
    urls = parse_urls_from_text(raw)
    return urls


def ask_mode():
    """Chọn chế độ tải: Video hoặc Âm thanh MP3."""
    console.print(Panel(
        "  [bold]1.[/] Tải [bold cyan]VIDEO CHẤT LƯỢNG CAO[/] (MP4)\n"
        "  [bold]2.[/] Chỉ tải [bold cyan]ÂM THANH (MP3)[/] (Kèm ảnh bìa & thông tin bài hát)",
        title="[bold]BƯỚC 2/5 • CHẾ ĐỘ TẢI[/]",
        border_style="blue", box=box.ROUNDED
    ))
    while True:
        c = IntPrompt.ask("  [bold bright_cyan]► Chọn[/]", default=1)
        if c in (1, 2):
            return c == 2
        console.print("  [red][X] Chỉ chọn 1 hoặc 2[/]")


def ask_quality():
    """Chọn độ phân giải video."""
    cfg = load_settings()
    def_q = cfg.get("default_quality", "best")
    def_idx = 1
    for idx, (code, _) in enumerate(QUALITIES, 1):
        if code == def_q:
            def_idx = idx
            break

    tb = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan", border_style="bright_blue", padding=(0, 2))
    tb.add_column("#", justify="center", style="bold bright_cyan", width=3)
    tb.add_column("CHẤT LƯỢNG VIDEO", style="white")
    for i, (_code, label) in enumerate(QUALITIES, 1):
        tb.add_row(str(i), label)
    console.print(Panel(tb, title="[bold]BƯỚC 3/5 • CHẤT LƯỢNG HÌNH ẢNH[/]", border_style="blue", box=box.ROUNDED))

    while True:
        c = IntPrompt.ask("  [bold bright_cyan]► Chọn[/]", default=def_idx)
        if 1 <= c <= len(QUALITIES):
            code, label = QUALITIES[c - 1]
            console.print(f"  [bright_green][OK] Đã chọn: {label}[/]\n")
            return code
        console.print(f"  [red][X] Vui lòng chọn từ 1 đến {len(QUALITIES)}[/]")


def ask_audio_bitrate():
    """Chọn chất lượng âm thanh MP3."""
    cfg = load_settings()
    def_br = cfg.get("audio_bitrate", "192")
    def_idx = 2
    for idx, (code, _) in enumerate(AUDIO_BITRATES, 1):
        if code == def_br:
            def_idx = idx
            break

    tb = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan", border_style="bright_blue", padding=(0, 2))
    tb.add_column("#", justify="center", style="bold bright_cyan", width=3)
    tb.add_column("CHẤT LƯỢNG ÂM THANH (BITRATE)", style="white")
    for i, (_code, label) in enumerate(AUDIO_BITRATES, 1):
        tb.add_row(str(i), label)
    console.print(Panel(tb, title="[bold]BƯỚC 3/5 • BITRATE ÂM THANH[/]", border_style="blue", box=box.ROUNDED))

    while True:
        c = IntPrompt.ask("  [bold bright_cyan]► Chọn[/]", default=def_idx)
        if 1 <= c <= len(AUDIO_BITRATES):
            code, label = AUDIO_BITRATES[c - 1]
            console.print(f"  [bright_green][OK] Đã chọn: {label}[/]\n")
            return code
        console.print(f"  [red][X] Vui lòng chọn từ 1 đến {len(AUDIO_BITRATES)}[/]")


def ask_output():
    """Chọn thư mục lưu file."""
    cfg = load_settings()
    def_out = cfg.get("default_output", "downloads")
    console.print(Panel(
        f"[bold]THƯ MỤC LƯU TRỮ[/]\n"
        f"[dim]Mặc định: `{def_out}` (Nhấn Enter để giữ nguyên)[/]",
        title="[bold]BƯỚC 4/5 • THƯ MỤC LƯU FILE[/]",
        border_style="blue", box=box.ROUNDED
    ))
    out = Prompt.ask("  [bold bright_cyan]► Thư mục[/]", default=def_out)
    return os.path.abspath(out)


def parse_cut_time(s):
    s = s.strip().replace(",", ".")
    if not s:
        raise ValueError
    if ":" in s:
        parts = s.split(":")
        if not 2 <= len(parts) <= 3:
            raise ValueError
        total = 0.0
        for p in parts:
            total = total * 60 + float(p)
        return total
    return float(s)


def ask_cut(ffmpeg_path):
    """Tùy chọn cắt đoạn video / audio sau khi tải."""
    console.print(Panel(
        "[bold]CẮT FILE SAU KHI TẢI (Tùy chọn nâng cao)[/]\n"
        "[dim]Nhập giây kiểu số thập phân (1.5) hoặc phút:giây (0:15.5)\n"
        "File gốc vẫn được giữ nguyên vẹn, file đã cắt được tạo thêm.[/]",
        title="[bold]BƯỚC 5/5 • TÙY CHỌN CẮT[/]",
        border_style="blue", box=box.ROUNDED
    ))
    if not Confirm.ask("  [bold]► Bạn có muốn cắt file sau khi tải không?[/]", default=False):
        return None
    if not ffmpeg_path:
        console.print("  [yellow][!!] Chưa có FFmpeg nên không thể thực hiện cắt — Bỏ qua bước này.[/]\n")
        return None

    while True:
        try:
            s = Prompt.ask("  [bold bright_cyan]► Điểm bắt đầu (giây)[/]", default="0")
            e = Prompt.ask("  [bold bright_cyan]► Điểm kết thúc (giây)[/]", default="30")
            start, end = parse_cut_time(s), parse_cut_time(e)
            if end <= start:
                console.print("  [red][X] Điểm kết thúc phải lớn hơn điểm bắt đầu![/]")
                continue
            console.print(f"  [bright_green][OK] Thiết lập cắt từ {start:g}s → {end:g}s[/]\n")
            return (start, end)
        except ValueError:
            console.print("  [red][X] Định dạng thời gian không đúng! Nhập kiểu 1.5 hoặc 0:15.5[/]")


def ask_subs():
    """Tùy chọn tải phụ đề đi kèm."""
    console.print(Panel(
        "[bold]TẢI PHỤ ĐỀ / SUBTITLES (.SRT)[/]\n"
        "[dim]Nhập mã ngôn ngữ: vi (Tiếng Việt), en (Tiếng Anh), ja (Tiếng Nhật)...\n"
        "Nhập 'all' để lấy mọi phụ đề • Nhấn Enter để bỏ qua không tải phụ đề[/]",
        title="[bold]TÙY CHỌN • PHỤ ĐỀ[/]",
        border_style="blue", box=box.ROUNDED
    ))
    raw = Prompt.ask("  [bold bright_cyan]► Mã phụ đề[/]", default="").strip().lower()
    if not raw:
        return None
    console.print(f"  [bright_green][OK] Sẽ tải phụ đề: {raw}[/]\n")
    return raw


def check_playlist_intent(urls):
    """Kiểm tra xem trong danh sách có link playlist không."""
    has_playlist = any("list=" in u.lower() or "/playlist" in u.lower() for u in urls)
    if not has_playlist:
        return False
    console.print(Panel(
        "[bold yellow][!!] PHÁT HIỆN ĐƯỜNG LINK DANH SÁCH PHÁT (PLAYLIST)[/]\n"
        "Bạn muốn tải toàn bộ danh sách phát hay chỉ tải 1 video đơn?",
        border_style="yellow", box=box.ROUNDED
    ))
    return Confirm.ask("  [bold bright_cyan]► Tải TOÀN BỘ Playlist?[/]", default=False)


# ─────────────────────────────────────────────────────────── MENU CÀI ĐẶT & TOOLBOX
def settings_menu():
    """Menu quản lý cấu hình người dùng."""
    while True:
        cfg = load_settings()
        tb = Table(title="CÀI ĐẶT HỆ THỐNG", box=box.ROUNDED, border_style="bright_blue",
                   title_style="bold bright_cyan", header_style="bold cyan")
        tb.add_column("#", justify="center", style="bold bright_cyan", width=3)
        tb.add_column("MỤC CÀI ĐẶT", style="white")
        tb.add_column("GIÁ TRỊ HIỆN TẠI", style="yellow")

        tb.add_row("1", "Chất lượng video mặc định", str(cfg.get("default_quality", "best")))
        tb.add_row("2", "Thư mục lưu mặc định", str(cfg.get("default_output", "downloads")))
        tb.add_row("3", "Tự động gộp định dạng chuẩn MP4", "[bright_green]Bật[/]" if cfg.get("merge_mp4", True) else "[red]Tắt[/]")
        tb.add_row("4", "Tự động mở thư mục sau khi tải", "[bright_green]Bật[/]" if cfg.get("auto_open_folder", True) else "[red]Tắt[/]")
        tb.add_row("5", "Nhúng ảnh bìa & thông tin vào MP3", "[bright_green]Bật[/]" if cfg.get("embed_thumbnail", True) else "[red]Tắt[/]")
        tb.add_row("6", "Chất lượng âm thanh MP3 mặc định", f"{cfg.get('audio_bitrate', '192')} kbps")
        tb.add_row("7", "Khôi phục cài đặt gốc", "[dim]Mặc định chuẩn[/]")
        tb.add_row("8", "Quay lại Menu chính", "—")

        console.print()
        console.print(tb)

        c = IntPrompt.ask("  [bold bright_cyan]► Chọn mục cần đổi (1-8)[/]", default=8)
        if c == 8:
            break
        elif c == 1:
            code = ask_quality()
            cfg["default_quality"] = code
            save_settings(cfg)
        elif c == 2:
            out = Prompt.ask("  [bold]Nhập thư mục mặc định mới[/]", default=cfg.get("default_output", "downloads"))
            cfg["default_output"] = out
            save_settings(cfg)
        elif c == 3:
            cfg["merge_mp4"] = not cfg.get("merge_mp4", True)
            save_settings(cfg)
        elif c == 4:
            cfg["auto_open_folder"] = not cfg.get("auto_open_folder", True)
            save_settings(cfg)
        elif c == 5:
            cfg["embed_thumbnail"] = not cfg.get("embed_thumbnail", True)
            save_settings(cfg)
        elif c == 6:
            code = ask_audio_bitrate()
            cfg["audio_bitrate"] = code
            save_settings(cfg)
        elif c == 7:
            save_settings(DEFAULT_SETTINGS)
            console.print("  [bright_green][OK] Đã khôi phục cài đặt mặc định![/]")


def toolbox_menu(ffmpeg_path):
    """Bộ công cụ tiện ích offline (cắt file, convert, quản lý FFmpeg)."""
    while True:
        console.print(Panel(
            "  [bold]1.[/] Cắt file Video / Audio bất kỳ trên máy tính\n"
            "  [bold]2.[/] Chuyển đổi định dạng sang MP3 hoặc MP4\n"
            "  [bold]3.[/] Tải / Cài đặt FFmpeg Portable vào thư mục `bin/`\n"
            "  [bold]4.[/] Mở thư mục tải về (`downloads`)\n"
            "  [bold]5.[/] Quay lại Menu chính",
            title="[bold]BỘ CÔNG CỤ TIỆN ÍCH (TOOLBOX)[/]", border_style="bright_blue", box=box.ROUNDED
        ))
        c = IntPrompt.ask("  [bold bright_cyan]► Chọn[/]", default=5)
        if c == 5:
            break
        elif c == 1:
            if not ffmpeg_path:
                console.print("  [red][X] Cần có FFmpeg để cắt file. Hãy chọn mục 3 để tải FFmpeg trước![/]\n")
                continue
            fpath = Prompt.ask("  [bold]► Nhập đường dẫn file cần cắt (hoặc kéo thả file vào đây)[/]").strip('"\'')
            if not os.path.isfile(fpath):
                console.print("  [red][X] File không tồn tại![/]\n")
                continue
            try:
                s = parse_cut_time(Prompt.ask("  [bold]► Giây bắt đầu[/]", default="0"))
                e = parse_cut_time(Prompt.ask("  [bold]► Giây kết thúc[/]", default="30"))
                with console.status("  [magenta]Đang cắt file...[/]", spinner="dots", spinner_style="magenta"):
                    out = cut_media_file(fpath, s, e, ffmpeg_path)
                console.print(f"  [bright_green][OK] Đã cắt thành công: {out}[/]\n")
            except Exception as ex:
                console.print(f"  [red][X] Lỗi: {ex}[/]\n")

        elif c == 2:
            if not ffmpeg_path:
                console.print("  [red][X] Cần có FFmpeg để chuyển đổi định dạng. Hãy chọn mục 3 để tải FFmpeg trước![/]\n")
                continue
            fpath = Prompt.ask("  [bold]► Nhập đường dẫn file cần convert (hoặc kéo thả file vào đây)[/]").strip('"\'')
            if not os.path.isfile(fpath):
                console.print("  [red][X] File không tồn tại![/]\n")
                continue
            target_fmt = Prompt.ask("  [bold]► Định dạng muốn chuyển sang (mp3 / mp4)[/]", choices=["mp3", "mp4"], default="mp3")
            base, _ = os.path.splitext(fpath)
            out_file = f"{base}_converted.{target_fmt}"
            cmd = [ffmpeg_path, "-y", "-i", fpath]
            if target_fmt == "mp3":
                cmd += ["-vn", "-acodec", "libmp3lame", "-b:a", "192k", out_file]
            else:
                cmd += ["-c:v", "libx264", "-c:a", "aac", out_file]
            with console.status("  [cyan]Đang chuyển đổi định dạng...[/]", spinner="dots", spinner_style="cyan"):
                r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode == 0 and os.path.exists(out_file):
                console.print(f"  [bright_green][OK] Chuyển đổi thành công: {out_file}[/]\n")
            else:
                console.print(f"  [red][X] Chuyển đổi thất bại: {r.stderr[:200]}[/]\n")

        elif c == 3:
            res = download_portable_ffmpeg()
            if res:
                ffmpeg_path = res

        elif c == 4:
            cfg = load_settings()
            out_dir = os.path.abspath(cfg.get("default_output", "downloads"))
            os.makedirs(out_dir, exist_ok=True)
            try:
                subprocess.Popen(f'explorer "{out_dir}"')
            except Exception:
                pass


# ─────────────────────────────────────────────────────────── CẬP NHẬT ENGINE
def do_update():
    """Tự động nâng cấp yt-dlp, rich, requests, pyperclip lên bản mới nhất."""
    try:
        from yt_dlp.version import __version__ as old_ver
    except Exception:
        old_ver = "?"
    console.print(Panel(
        f"[bold]CẬP NHẬT BỘ LÕI ENGINE TẢI[/]\n"
        f"Phiên bản yt-dlp hiện tại: [cyan]{old_ver}[/]\n"
        f"[dim]Cập nhật thường xuyên để tải ổn định các video YouTube, TikTok mới nhất[/]",
        border_style="blue", box=box.ROUNDED
    ))
    with console.status("  [cyan]Đang kiểm tra & cập nhật yt-dlp, rich, requests, pyperclip...[/]", spinner="dots", spinner_style="bright_cyan"):
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp", "rich", "requests", "pyperclip"],
            capture_output=True, text=True
        )
    if r.returncode != 0:
        console.print("  [red][X] Cập nhật thất bại. Vui lòng kiểm tra kết nối mạng và thử lại.[/]\n")
        return
    new_ver = subprocess.run(
        [sys.executable, "-c", "import yt_dlp;print(yt_dlp.version.__version__)"],
        capture_output=True, text=True
    ).stdout.strip()
    if new_ver and new_ver != old_ver:
        console.print(f"  [bright_green][OK] Đã nâng cấp thành công: {old_ver} → {new_ver}![/]\n")
    else:
        console.print(f"  [bright_green][OK] yt-dlp đã ở phiên bản mới nhất ({new_ver or old_ver}).[/]\n")


def parse_version(v):
    out = []
    for p in str(v).split("."):
        try:
            out.append(int(p))
        except ValueError:
            out.append(0)
    return tuple(out)


def check_updates_on_startup():
    """Kiểm tra bản cập nhật khi khởi động."""
    cfg = load_settings()
    if not cfg.get("check_updates", True):
        return
    try:
        from yt_dlp.version import __version__ as cur
    except Exception:
        return
    try:
        from urllib.request import Request, urlopen
        with console.status("  [cyan]Đang kiểm tra cập nhật yt-dlp...[/]", spinner="dots", spinner_style="bright_cyan"):
            req = Request("https://pypi.org/pypi/yt-dlp/json", headers={"User-Agent": f"video-tool/{VERSION}"})
            with urlopen(req, timeout=4) as resp:
                latest = json.load(resp)["info"]["version"]
        if parse_version(latest) > parse_version(cur):
            console.print(Panel(
                f"Bản hiện tại: [cyan]{cur}[/]  →  Bản mới nhất: [bright_green]{latest}[/]\n"
                f"[bold]Chọn mục 6 trong Menu chính[/] để tự động nâng cấp!",
                title="[bold yellow][!!] CÓ BẢN CẬP NHẬT MỚI[/]",
                border_style="yellow", box=box.ROUNDED
            ))
        else:
            console.print(f"  [bright_green][OK] yt-dlp [cyan]{cur}[/] đang là phiên bản mới nhất[/]")
    except Exception:
        pass
    console.print()


# ─────────────────────────────────────────────────────────── MENU CHÍNH
def main_menu():
    console.print(Panel(
        "  [bold]1.[/] Tải video / âm thanh từ link (Nhập trực tiếp)\n"
        "  [bold]2.[/] Tải hàng loạt từ danh sách file ([cyan]links.txt[/])\n"
        "  [bold]3.[/] Tải nhanh từ Clipboard (Bộ nhớ tạm)\n"
        "  [bold]4.[/] Bộ công cụ tiện ích (Toolbox: Cắt video, Convert, FFmpeg)\n"
        "  [bold]5.[/] Cài đặt & Cấu hình\n"
        "  [bold]6.[/] Cập nhật bộ lõi engine (yt-dlp)\n"
        "  [bold]7.[/] Thoát chương trình",
        title="[bold bright_cyan]MENU CHÍNH[/]", border_style="bright_blue", box=box.DOUBLE
    ))
    while True:
        c = IntPrompt.ask("  [bold bright_cyan]► Chọn thao tác (1-7)[/]", default=1)
        if 1 <= c <= 7:
            return c
        console.print("  [red][X] Vui lòng chỉ chọn số từ 1 đến 7[/]")


def interactive_loop(ffmpeg_path):
    while True:
        try:
            choice = main_menu()
            if choice == 7:
                break
            elif choice == 6:
                do_update()
                continue
            elif choice == 5:
                settings_menu()
                continue
            elif choice == 4:
                toolbox_menu(ffmpeg_path)
                continue

            # Xử lý các luồng lấy link tải
            urls = []
            if choice == 1:
                urls = ask_urls()
            elif choice == 2:
                urls = load_urls_from_file("links.txt")
                if not urls:
                    continue
                console.print(f"  [bright_green][OK] Đã nạp {len(urls)} đường link từ links.txt[/]\n")
            elif choice == 3:
                urls = load_urls_from_clipboard()
                if not urls:
                    console.print("  [yellow][!!] Không tìm thấy link hợp lệ trong Clipboard![/]\n")
                    continue
                console.print(f"  [bright_green][OK] Đã lấy {len(urls)} đường link từ Clipboard[/]\n")

            is_playlist = check_playlist_intent(urls)
            audio = ask_mode()
            quality = "best" if audio else ask_quality()
            audio_bitrate = ask_audio_bitrate() if audio else "192"
            out_dir = ask_output()
            cut = ask_cut(ffmpeg_path)
            subs = ask_subs()

            # Phân tích sơ bộ và hiển thị ước tính
            previews = fetch_previews(urls, quality, audio, out_dir, ffmpeg_path, subs=subs)
            show_preview_panel(previews, load_settings().get("avg_speed"))

            # Xác nhận cuối cùng trước khi tải
            q_label = f"MP3 ({audio_bitrate} kbps)" if audio else next((l for c, l in QUALITIES if c == quality), quality)
            console.print(Panel(
                f"[bold]Số lượng mục:[/] {len(urls)} {'(Bao gồm Playlist)' if is_playlist else ''}\n"
                f"[bold]Chế độ:[/]{'Âm thanh MP3' if audio else 'Video MP4'} — {q_label}\n"
                f"[bold]Thư mục lưu:[/] {out_dir}\n"
                f"[bold]Cắt file:[/] {f'{cut[0]:g}s → {cut[1]:g}s' if cut else 'Không'}\n"
                f"[bold]Phụ đề:[/] {subs.upper() if subs else 'Không'}\n"
                f"[dim]Tự động bỏ logo/watermark • Chuẩn hóa MP4 • Tự động dùng cookies nếu cần[/]",
                title="[bold cyan]XÁC NHẬN BẮT ĐẦU TẢI[/]", border_style="cyan", box=box.DOUBLE
            ))

            if not Confirm.ask("  [bold]► Bắt đầu tải ngay?[/]", default=True):
                console.print("  [dim]Đã hủy lượt tải. Quay lại Menu chính.[/]\n")
                continue

            console.print()
            results = run_downloads(
                urls, quality, audio, out_dir, ffmpeg_path,
                subs=subs, audio_bitrate=audio_bitrate, is_playlist=is_playlist
            )
            record_speeds(results)
            if results:
                if cut:
                    apply_cut(results, cut, ffmpeg_path)
                show_summary(results, out_dir)
                open_result_folder(results, out_dir)

            console.print()
            if not Confirm.ask("  [bold bright_cyan]► Tiếp tục tải thêm video khác?[/]", default=True):
                break
            console.print(Rule(style="bright_blue"))

        except KeyboardInterrupt:
            console.print("\n")
            if Confirm.ask("  [yellow]Bạn có muốn thoát chương trình?[/]", default=True):
                break
            console.print()

    console.print(Panel.fit(
        f"[bold bright_cyan]Cảm ơn bạn đã sử dụng Tool Tải Video PRO v{VERSION}![/]\n"
        f"[dim]{COPYRIGHT}[/]",
        border_style="blue", box=box.DOUBLE
    ))


# ─────────────────────────────────────────────────────────── MAIN ENTRY POINT
def main():
    ffmpeg_path = find_ffmpeg()

    # Kiểm tra cờ tham số dòng lệnh
    args = sys.argv[1:]
    if "--gui" in args:
        try:
            import gui_downloader
            gui_downloader.run()
            return
        except Exception as e:
            print(f"[LỖI] Không thể mở GUI: {e}")

    # Chế độ dòng lệnh không tương tác hoặc hiển thị trợ giúp
    if args and ("-h" in args or "--help" in args or not all(a.startswith("-") for a in args)):
        import argparse
        p = argparse.ArgumentParser(add_help=True, description="Tool Tải Video PRO v4.0")
        p.add_argument("urls", nargs="*", help="Danh sách các đường link video")
        p.add_argument("-q", "--quality", default="best", help="Chất lượng video (best, 1080, 720...)")
        p.add_argument("--audio", action="store_true", help="Chỉ tải âm thanh MP3")
        p.add_argument("--bitrate", default="192", help="Bitrate âm thanh (128, 192, 320)")
        p.add_argument("-o", "--output", default="downloads", help="Thư mục lưu file")
        p.add_argument("--cookies-from-browser", choices=BROWSERS, default=None, help="Lấy cookies từ trình duyệt")
        p.add_argument("--subs", default=None, help="Tải phụ đề (vi, en, all...)")
        p.add_argument("--cut", nargs=2, type=float, metavar=("START", "END"), help="Cắt video sau khi tải")
        p.add_argument("--playlist", action="store_true", help="Tải toàn bộ Playlist nếu phát hiện")
        a = p.parse_args(args)

        if a.urls:
            cut = tuple(a.cut) if a.cut else None
            out_dir = os.path.abspath(a.output)
            results = run_downloads(
                a.urls, a.quality, a.audio, out_dir, ffmpeg_path,
                browser=a.cookies_from_browser, subs=a.subs,
                audio_bitrate=a.bitrate, is_playlist=a.playlist
            )
            record_speeds(results)
            if cut and ffmpeg_path:
                apply_cut(results, cut, ffmpeg_path)
            show_summary(results, out_dir)
            open_result_folder(results, out_dir)
            return

    # Chế độ tương tác
    show_banner()
    intro_loading(ffmpeg_path)
    console.print(Panel(WHATS_NEW, title=f"[bold bright_magenta]★ NÂNG CẤP LỚN v{VERSION}[/]", border_style="magenta", box=box.ROUNDED))
    console.print()
    check_updates_on_startup()

    # Nhắc nhở nếu chưa có FFmpeg
    if not ffmpeg_path:
        console.print(Panel(
            "[bold yellow][!!] CHƯA TÌM THẤY BỘ GIẢI MÃ FFMPEG TRÊN MÁY[/]\n"
            "• Nếu không có FFmpeg, video 1080p/4K từ YouTube sẽ không ghép được âm thanh và không xuất được MP3.\n"
            "• Tool có thể tự động tải bản FFmpeg Portable nhẹ (~30MB) về dùng ngay mà không cần cài đặt.",
            border_style="yellow", box=box.ROUNDED
        ))
        if Confirm.ask("  [bold bright_green]► Bạn có muốn tải FFmpeg Portable ngay bây giờ không?[/]", default=True):
            res = download_portable_ffmpeg()
            if res:
                ffmpeg_path = res

    interactive_loop(ffmpeg_path)


if __name__ == "__main__":
    main()
