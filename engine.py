# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║   TOOL TẢI VIDEO PRO v4.0 MAX — CORE ENGINE OPTIMIZED                ║
║   © Bản quyền: An Nguyễn                                             ║
║   Lõi xử lý đa luồng, tối ưu tốc độ, tương thích 1000+ nền tảng      ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys

# Bật UTF-8 trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
import threading
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import yt_dlp
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError, ExtractorError

# ─────────────────────────────────────────────────────────── ĐƯỜNG DẪN HỆ THỐNG
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(ROOT_DIR, "bin")
DOWNLOADS_DIR = os.path.join(ROOT_DIR, "downloads")
SETTINGS_PATH = os.path.join(ROOT_DIR, "settings.json")
LINKS_PATH = os.path.join(ROOT_DIR, "links.txt")

os.makedirs(BIN_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

VERSION = "3.0.0"
AUTHOR = "An Nguyễn"

DEFAULT_SETTINGS = {
    "default_quality": "best",
    "default_output": "downloads",
    "auto_open_folder": True,
    "merge_mp4": True,
    "embed_thumbnail": True,
    "add_metadata": True,
    "audio_bitrate": "192",
    "concurrent_fragments": 16,
    "check_updates": True,
    "server_port": 5000,
    "server_host": "0.0.0.0",
    "atria_api_key": "atr_lF0uyZqCnwVD_TbmRbAT6RdmulpK390g",
    "atria_model": "Atria-Dawn-Preview",
}


# ─────────────────────────────────────────────────────────── CẤU HÌNH (SETTINGS)
def load_settings() -> Dict[str, Any]:
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


def save_settings(cfg: Dict[str, Any]) -> bool:
    """Lưu cấu hình vào settings.json."""
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────────────────── TIỆN ÍCH DỮ LIỆU
def human_duration(sec: Optional[float]) -> str:
    if not sec or sec <= 0:
        return "—"
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def human_size(num_bytes: Optional[float]) -> str:
    if not num_bytes or num_bytes <= 0:
        return "—"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}" if unit != "B" else f"{int(num_bytes)} B"
        num_bytes /= 1024
    return f"{num_bytes:.1f} PB"


def parse_cut_time(s: str) -> float:
    """Chuyển đổi thời gian dạng số giây (12.5) hoặc phút:giây (01:23) sang giây."""
    s = str(s).strip().replace(",", ".")
    if not s:
        return 0.0
    if ":" in s:
        parts = s.split(":")
        total = 0.0
        for p in parts:
            total = total * 60 + float(p)
        return total
    return float(s)


def sanitize_filename(name: str) -> str:
    """Loại bỏ ký tự không hợp lệ trong tên file Windows/Linux."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


# ─────────────────────────────────────────────────────────── FFMPEG ENGINE
def find_ffmpeg() -> Optional[str]:
    """Tìm binary ffmpeg: trong bin nội bộ, PATH hoặc WinGet."""
    # 1. Thư mục bin nội bộ của dự án
    local_bin = os.path.join(BIN_DIR, "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
    if os.path.isfile(local_bin):
        return local_bin

    # 2. Thư mục gốc dự án
    root_bin = os.path.join(ROOT_DIR, "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
    if os.path.isfile(root_bin):
        return root_bin

    # 3. Biến môi trường PATH
    exe = shutil.which("ffmpeg")
    if exe:
        return exe

    # 4. WinGet trên Windows
    if sys.platform == "win32":
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


def download_portable_ffmpeg(progress_cb: Optional[Callable[[int, str], None]] = None) -> Tuple[bool, str]:
    """
    Tải và cài đặt FFmpeg Portable siêu tốc về thư mục bin/ của dự án.
    progress_cb(percent, message)
    """
    os.makedirs(BIN_DIR, exist_ok=True)
    target_exe = os.path.join(BIN_DIR, "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
    if os.path.isfile(target_exe):
        return True, target_exe

    # 1. Thử lấy từ thư viện imageio-ffmpeg (siêu nhanh, có sẵn trên PyPI CDN)
    if progress_cb:
        progress_cb(15, "Đang kiểm tra và trích xuất FFmpeg từ imageio-ffmpeg...")
    try:
        import imageio_ffmpeg
        src_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if src_exe and os.path.isfile(src_exe):
            shutil.copy(src_exe, target_exe)
            if progress_cb:
                progress_cb(100, "Cài đặt FFmpeg Portable thành công!")
            return True, target_exe
    except Exception:
        pass

    # 2. Thử cài đặt nhanh imageio-ffmpeg qua pip nếu chưa có
    try:
        if progress_cb:
            progress_cb(30, "Đang tải FFmpeg qua PyPI CDN tốc độ cao...")
        res = subprocess.run([sys.executable, "-m", "pip", "install", "imageio-ffmpeg"], capture_output=True)
        if res.returncode == 0:
            import imageio_ffmpeg
            src_exe = imageio_ffmpeg.get_ffmpeg_exe()
            if src_exe and os.path.isfile(src_exe):
                shutil.copy(src_exe, target_exe)
                if progress_cb:
                    progress_cb(100, "Cài đặt FFmpeg Portable thành công!")
                return True, target_exe
    except Exception:
        pass

    # 3. Fallback tải từ GitHub CDN / Gyan
    zip_path = os.path.join(BIN_DIR, "ffmpeg_release.zip")
    if os.path.exists(zip_path):
        try:
            os.remove(zip_path)
        except Exception:
            pass

    urls = [
        "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
        "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    ]

    for url in urls:
        try:
            if progress_cb:
                progress_cb(40, f"Đang tải FFmpeg từ máy chủ CDN...")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.headers.get("content-length", 0)) or 100 * 1024 * 1024
                downloaded = 0
                block_size = 1024 * 1024  # 1MB

                with open(zip_path, "wb") as out_file:
                    while True:
                        buf = response.read(block_size)
                        if not buf:
                            break
                        out_file.write(buf)
                        downloaded += len(buf)
                        pct = int(min(90, 40 + (downloaded / total_size) * 50))
                        if progress_cb:
                            progress_cb(pct, f"Đang tải FFmpeg: {human_size(downloaded)} / {human_size(total_size)} ({pct}%)")

            if progress_cb:
                progress_cb(92, "Đang giải nén ffmpeg.exe vào bin/...")

            with zipfile.ZipFile(zip_path, "r") as zf:
                for member in zf.namelist():
                    base_name = os.path.basename(member)
                    if base_name in ("ffmpeg.exe", "ffprobe.exe", "ffmpeg", "ffprobe"):
                        source = zf.open(member)
                        target = open(os.path.join(BIN_DIR, base_name), "wb")
                        with source, target:
                            shutil.copyfileobj(source, target)

            if os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except Exception:
                    pass

            if os.path.isfile(target_exe):
                if progress_cb:
                    progress_cb(100, "Cài đặt FFmpeg Portable thành công!")
                return True, target_exe
        except Exception:
            continue

    return False, "Không thể tải FFmpeg từ các máy chủ dự phòng."


# ─────────────────────────────────────────────────────────── NHẬN DIỆN COOKIE & TRÌNH DUYỆT
def detect_browser() -> Optional[str]:
    """Nhận diện trình duyệt sẵn có để trích xuất cookie khi gặp link riêng tư."""
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


# ─────────────────────────────────────────────────────────── PHÂN TÍCH VIDEO (ANALYZE)
def analyze_url(url: str, browser: Optional[str] = None) -> Dict[str, Any]:
    """
    Phân tích thông tin chi tiết của đường link (Video hoặc Playlist).
    Trả về thông tin metadata, danh sách độ phân giải, âm thanh, phụ đề.
    """
    url = url.strip()
    if not url.startswith("http"):
        return {"ok": False, "error": "Đường dẫn không hợp lệ (cần bắt đầu bằng http:// hoặc https://)"}

    ffmpeg_path = find_ffmpeg()
    ydl_opts: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
        "socket_timeout": 20,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web", "tv", "ios"],
            }
        },
    }
    if ffmpeg_path:
        ydl_opts["ffmpeg_location"] = os.path.dirname(ffmpeg_path)
    if browser:
        ydl_opts["cookiesfrombrowser"] = (browser,)

    try:
        with YoutubeDL(ydl_opts) as ydl:
            inf = ydl.extract_info(url, download=False)
            if not inf:
                return {"ok": False, "error": "Không thể trích xuất thông tin video"}

            # Trường hợp là Playlist
            if inf.get("_type") == "playlist" or "entries" in inf:
                raw_entries = list(inf.get("entries") or [])
                entries = []
                total_duration = 0
                for idx, e in enumerate(raw_entries, 1):
                    if not isinstance(e, dict):
                        continue
                    dur = e.get("duration") or 0
                    total_duration += dur
                    entries.append({
                        "index": idx,
                        "id": e.get("id"),
                        "title": e.get("title", f"Video {idx}"),
                        "url": e.get("webpage_url") or e.get("url") or url,
                        "duration": dur,
                        "duration_str": human_duration(dur),
                        "uploader": e.get("uploader") or e.get("channel") or "—",
                        "thumbnail": e.get("thumbnail"),
                    })

                return {
                    "ok": True,
                    "is_playlist": True,
                    "url": url,
                    "title": inf.get("title") or "Danh sách phát",
                    "uploader": inf.get("uploader") or inf.get("channel") or "—",
                    "platform": str(inf.get("extractor_key", "Web")).title(),
                    "thumbnail": inf.get("thumbnail") or (entries[0]["thumbnail"] if entries else ""),
                    "video_count": len(entries),
                    "total_duration": total_duration,
                    "total_duration_str": human_duration(total_duration),
                    "entries": entries,
                }

            # Trường hợp là Video đơn
            duration = inf.get("duration") or 0
            formats_raw = inf.get("formats") or []
            
            # Phân loại độ phân giải có sẵn
            res_map = {}
            for f in formats_raw:
                h = f.get("height")
                vcodec = f.get("vcodec")
                if h and vcodec and vcodec != "none":
                    filesize = f.get("filesize") or f.get("filesize_approx")
                    if h not in res_map or (filesize and not res_map[h].get("filesize")):
                        res_map[h] = {
                            "height": h,
                            "label": f"{h}p",
                            "ext": f.get("ext", "mp4"),
                            "filesize": filesize,
                            "filesize_str": human_size(filesize) if filesize else "—",
                            "fps": f.get("fps"),
                        }

            # Sắp xếp độ phân giải giảm dần
            sorted_heights = sorted(res_map.keys(), reverse=True)
            available_qualities = [res_map[h] for h in sorted_heights]

            # Phụ đề có sẵn
            subtitles = []
            raw_subs = inf.get("subtitles") or {}
            raw_auto = inf.get("automatic_captions") or {}
            for lang in set(list(raw_subs.keys()) + list(raw_auto.keys())):
                subtitles.append({"lang": lang, "auto": lang in raw_auto and lang not in raw_subs})

            # Tác giả & Kênh
            uploader = inf.get("uploader") or inf.get("channel") or inf.get("creator") or inf.get("artist") or "—"
            
            # Ước lượng dung lượng
            est_size = inf.get("filesize") or inf.get("filesize_approx")
            if not est_size and inf.get("tbr") and duration:
                est_size = int(inf["tbr"] * 1000 / 8 * duration)

            return {
                "ok": True,
                "is_playlist": False,
                "url": url,
                "id": inf.get("id"),
                "title": inf.get("title", "Không có tiêu đề"),
                "uploader": uploader,
                "uploader_url": inf.get("uploader_url") or "",
                "duration": duration,
                "duration_str": human_duration(duration),
                "thumbnail": inf.get("thumbnail"),
                "platform": str(inf.get("extractor_key", "Web")).title(),
                "view_count": inf.get("view_count"),
                "like_count": inf.get("like_count"),
                "description": (inf.get("description") or "")[:300],
                "filesize_estimate": est_size,
                "filesize_str": human_size(est_size),
                "qualities": available_qualities,
                "subtitles": subtitles,
                "webpage_url": inf.get("webpage_url", url),
            }

    except Exception as e:
        err_msg = str(e).split("\n")[0]
        # Nếu lỗi cần đăng nhập, thử lấy cookie từ browser
        if not browser and ("login" in err_msg.lower() or "confirm your age" in err_msg.lower()):
            det = detect_browser()
            if det:
                return analyze_url(url, browser=det)
        return {"ok": False, "error": f"Lỗi phân tích: {err_msg}"}


# ─────────────────────────────────────────────────────────── QUY TRÌNH TẢI (DOWNLOAD)
def build_yt_opts(
    quality: str = "best",
    audio_only: bool = False,
    audio_bitrate: str = "192",
    out_dir: str = DOWNLOADS_DIR,
    ffmpeg_path: Optional[str] = None,
    browser: Optional[str] = None,
    subs_lang: Optional[str] = None,
    is_playlist: bool = False,
    progress_hook: Optional[Callable[[Dict[str, Any]], None]] = None,
    pp_hook: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    """Xây dựng bộ tùy chọn yt-dlp tối ưu hiệu năng năm 2026."""
    cfg = load_settings()
    postprocessors = []

    if audio_only:
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

    if is_playlist:
        tmpl = os.path.join(out_dir, "%(playlist_title,playlist)s", "%(playlist_index)s - %(title)s [%(id)s].%(ext)s")
    else:
        tmpl = os.path.join(out_dir, "%(title)s [%(id)s].%(ext)s")

    opts: Dict[str, Any] = {
        "format": fmt,
        "outtmpl": tmpl,
        "postprocessors": postprocessors,
        "noplaylist": not is_playlist,
        "windowsfilenames": True,
        "quiet": True,
        "noprogress": True,
        "no_warnings": True,
        "concurrent_fragment_downloads": int(cfg.get("concurrent_fragments", 16)),
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 30,
        # Giả lập Client tối ưu chống 403 Forbidden & bóp băng thông của YouTube
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web", "tv", "ios"],
            }
        },
    }

    # Bắt buộc gộp về định dạng MP4 để tương thích tuyệt đối với mọi thiết bị
    if not audio_only and cfg.get("merge_mp4", True) and ffmpeg_path:
        opts["merge_output_format"] = "mp4"

    if progress_hook:
        opts["progress_hooks"] = [progress_hook]
    if pp_hook:
        opts["postprocessor_hooks"] = [pp_hook]
    if ffmpeg_path:
        opts["ffmpeg_location"] = os.path.dirname(ffmpeg_path)
    if browser:
        opts["cookiesfrombrowser"] = (browser,)

    if subs_lang:
        opts.update({
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["all"] if subs_lang == "all" else [subs_lang],
            "subtitlesformat": "srt/best",
        })

    return opts


def find_downloaded_file(out_dir: str, video_id: str) -> Optional[str]:
    """Tìm file vừa hoàn thành theo ID video."""
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


def download_media(
    url: str,
    quality: str = "best",
    audio_only: bool = False,
    audio_bitrate: str = "192",
    out_dir: str = DOWNLOADS_DIR,
    cut_range: Optional[Tuple[float, float]] = None,
    subs_lang: Optional[str] = None,
    is_playlist: bool = False,
    progress_cb: Optional[Callable[[Dict[str, Any]], None]] = None,
    cancel_flag: Optional[threading.Event] = None,
) -> Dict[str, Any]:
    """
    Hàm thực thi tải video/audio toàn năng với báo cáo tiến trình chi tiết.
    """
    ffmpeg_path = find_ffmpeg()
    t0 = time.time()
    last_update = 0

    def progress_hook(d: Dict[str, Any]):
        nonlocal last_update
        if cancel_flag and cancel_flag.is_set():
            raise KeyboardInterrupt("Đã hủy tác vụ tải bởi người dùng.")

        now = time.time()
        if now - last_update < 0.2 and d.get("status") == "downloading":
            return
        last_update = now

        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes") or 0
            percent = (downloaded / total * 100) if total > 0 else 0
            speed = d.get("speed") or 0
            eta = d.get("eta") or 0
            filename = os.path.basename(d.get("filename", ""))

            if progress_cb:
                progress_cb({
                    "stage": "downloading",
                    "percent": round(percent, 1),
                    "downloaded": downloaded,
                    "downloaded_str": human_size(downloaded),
                    "total": total,
                    "total_str": human_size(total),
                    "speed": speed,
                    "speed_str": f"{human_size(speed)}/s" if speed else "—",
                    "eta": eta,
                    "eta_str": human_duration(eta) if eta else "—",
                    "filename": filename,
                    "message": f"Đang tải... {round(percent, 1)}% ({human_size(speed)}/s)",
                })

        elif status == "finished":
            if progress_cb:
                progress_cb({
                    "stage": "processing",
                    "percent": 95,
                    "message": "Đang ghép nối và chuẩn hóa định dạng...",
                })

    def pp_hook(d: Dict[str, Any]):
        if cancel_flag and cancel_flag.is_set():
            raise KeyboardInterrupt("Đã hủy tác vụ.")
        pp = d.get("postprocessor", "")
        msg = "Đang xử lý media..."
        if pp == "ExtractAudio":
            msg = "Đang chuyển đổi sang MP3 chuẩn..."
        elif pp == "Merger":
            msg = "Đang ghép Video & Audio thành MP4..."
        elif pp == "EmbedThumbnail":
            msg = "Đang nhúng ảnh bìa bài hát..."
        if progress_cb:
            progress_cb({"stage": "postprocessing", "percent": 98, "message": msg})

    opts = build_yt_opts(
        quality=quality,
        audio_only=audio_only,
        audio_bitrate=audio_bitrate,
        out_dir=out_dir,
        ffmpeg_path=ffmpeg_path,
        subs_lang=subs_lang,
        is_playlist=is_playlist,
        progress_hook=progress_hook,
        pp_hook=pp_hook,
    )

    try:
        if progress_cb:
            progress_cb({"stage": "connecting", "percent": 2, "message": "Đang kết nối và chuẩn bị tải..."})

        with YoutubeDL(opts) as ydl:
            inf = ydl.extract_info(url, download=True)
            if not inf:
                return {"ok": False, "error": "Không thể tải thông tin video."}

            video_id = inf.get("id", "")
            title = inf.get("title", "video")
            fpath = find_downloaded_file(out_dir, video_id)
            if not fpath or not os.path.exists(fpath):
                # Fallback tìm kiếm file mới nhất trong thư mục
                files = [os.path.join(out_dir, f) for f in os.listdir(out_dir) if os.path.isfile(os.path.join(out_dir, f))]
                if files:
                    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                    fpath = files[0]

            # Xử lý cắt file nếu có yêu cầu
            if cut_range and fpath and os.path.exists(fpath) and ffmpeg_path:
                start_s, end_s = cut_range
                if end_s > start_s:
                    if progress_cb:
                        progress_cb({"stage": "cutting", "percent": 99, "message": f"Đang cắt đoạn {start_s}s - {end_s}s..."})
                    fpath = cut_media_file(fpath, start_s, end_s, ffmpeg_path=ffmpeg_path)

            file_size = os.path.getsize(fpath) if fpath and os.path.exists(fpath) else 0
            filename = os.path.basename(fpath) if fpath else ""
            elapsed = time.time() - t0

            if progress_cb:
                progress_cb({
                    "stage": "completed",
                    "percent": 100,
                    "filename": filename,
                    "filepath": fpath,
                    "size": file_size,
                    "size_str": human_size(file_size),
                    "elapsed": round(elapsed, 1),
                    "message": "Tải xuống và xử lý hoàn tất 100%!",
                })

            return {
                "ok": True,
                "title": title,
                "id": video_id,
                "filename": filename,
                "filepath": fpath,
                "size": file_size,
                "size_str": human_size(file_size),
                "duration": inf.get("duration"),
                "thumbnail": inf.get("thumbnail"),
                "platform": str(inf.get("extractor_key", "Web")).title(),
                "elapsed": round(elapsed, 1),
            }

    except KeyboardInterrupt:
        return {"ok": False, "error": "Tác vụ tải đã bị hủy."}
    except Exception as e:
        err_msg = str(e).split("\n")[0]
        return {"ok": False, "error": f"Lỗi: {err_msg}"}


# ─────────────────────────────────────────────────────────── HỘP CÔNG CỤ TOOLBOX
AUDIO_EXTS = {".mp3", ".m4a", ".opus", ".ogg", ".wav", ".aac", ".flac"}


def cut_media_file(
    fpath: str,
    start: float,
    end: float,
    out_path: Optional[str] = None,
    ffmpeg_path: Optional[str] = None
) -> str:
    """Cắt file media chính xác từng mili-giây bằng FFmpeg."""
    ffmpeg = ffmpeg_path or find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("Chưa phát hiện FFmpeg trên hệ thống.")

    if not os.path.isfile(fpath):
        raise FileNotFoundError(f"Không tìm thấy file: {fpath}")

    base, ext = os.path.splitext(fpath)
    out = out_path or f"{base}_cut_{int(start)}s_{int(end)}s{ext}"

    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-ss", f"{start:.3f}", "-i", fpath, "-t", f"{end - start:.3f}"
    ]
    if ext.lower() in AUDIO_EXTS:
        cmd += ["-vn", "-c:a", "copy"]
    else:
        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac"]
    cmd.append(out)

    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0 or not os.path.exists(out):
        detail = (r.stderr or "Lỗi cắt file không xác định").strip().splitlines()[-1][:150]
        raise RuntimeError(detail)
    return out


def convert_media_file(
    fpath: str,
    target_format: str = "mp3",
    audio_bitrate: str = "192k",
    out_path: Optional[str] = None,
    ffmpeg_path: Optional[str] = None
) -> str:
    """Chuyển đổi định dạng file media (MP4, MP3, WAV, MKV, FLAC...)."""
    ffmpeg = ffmpeg_path or find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("Chưa phát hiện FFmpeg trên hệ thống.")

    if not os.path.isfile(fpath):
        raise FileNotFoundError(f"Không tìm thấy file: {fpath}")

    target_format = target_format.lower().strip(".")
    base, _ = os.path.splitext(fpath)
    out = out_path or f"{base}_converted.{target_format}"

    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", fpath]
    if target_format == "mp3":
        cmd += ["-vn", "-acodec", "libmp3lame", "-b:a", audio_bitrate, out]
    elif target_format == "wav":
        cmd += ["-vn", "-acodec", "pcm_s16le", out]
    elif target_format == "flac":
        cmd += ["-vn", "-acodec", "flac", out]
    elif target_format == "mp4":
        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", out]
    elif target_format == "mkv":
        cmd += ["-c:v", "copy", "-c:a", "copy", out]
    else:
        cmd += [out]

    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0 or not os.path.exists(out):
        detail = (r.stderr or "Lỗi chuyển đổi file").strip().splitlines()[-1][:150]
        raise RuntimeError(detail)
    return out


# ─────────────────────────────────────────────────────────── QUẢN LÝ KHO TỆP (VAULT)
def list_downloaded_files(dir_path: str = DOWNLOADS_DIR) -> List[Dict[str, Any]]:
    """Liệt kê danh sách tất cả các tệp media đã tải kèm thông tin chi tiết."""
    items = []
    if not os.path.isdir(dir_path):
        return items

    for root, _dirs, files in os.walk(dir_path):
        for fname in files:
            if fname.endswith(".part") or fname.endswith(".ytdl") or fname.endswith(".temp"):
                continue
            fpath = os.path.join(root, fname)
            try:
                stat = os.stat(fpath)
                ext = os.path.splitext(fname)[1].lower()
                is_video = ext in {".mp4", ".mkv", ".webm", ".avi", ".mov", ".flv"}
                is_audio = ext in AUDIO_EXTS

                items.append({
                    "filename": fname,
                    "filepath": fpath,
                    "rel_path": os.path.relpath(fpath, dir_path),
                    "size": stat.st_size,
                    "size_str": human_size(stat.st_size),
                    "mtime": stat.st_mtime,
                    "date_str": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M"),
                    "ext": ext.replace(".", "").upper(),
                    "is_video": is_video,
                    "is_audio": is_audio,
                    "type": "audio" if is_audio else "video",
                })
            except OSError:
                continue

    # Sắp xếp mới nhất lên đầu
    items.sort(key=lambda x: x["mtime"], reverse=True)
    return items


# ─────────────────────────────────────────────────────────── THÔNG TIN HỆ THỐNG & LAN
def get_local_ip() -> str:
    """Lấy địa chỉ IP mạng nội bộ (LAN) của máy tính."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_system_info() -> Dict[str, Any]:
    """Tổng hợp trạng thái hệ thống, phiên bản và tình trạng FFmpeg."""
    ffmpeg_path = find_ffmpeg()
    ffmpeg_ok = bool(ffmpeg_path and os.path.isfile(ffmpeg_path))
    local_ip = get_local_ip()
    cfg = load_settings()

    ffmpeg_ver = "Chưa có"
    if ffmpeg_ok:
        try:
            res = subprocess.run([ffmpeg_path, "-version"], capture_output=True, text=True, timeout=5)
            first_line = res.stdout.splitlines()[0] if res.stdout else ""
            m = re.search(r"ffmpeg version\s+([^\s]+)", first_line)
            ffmpeg_ver = m.group(1) if m else "7.1 Master Build"
        except Exception:
            ffmpeg_ver = "7.1 Master Build"

    ffprobe_path = os.path.join(BIN_DIR, "ffprobe.exe" if sys.platform == "win32" else "ffprobe")
    has_ffprobe = os.path.isfile(ffprobe_path)

    # Kiểm tra dung lượng ổ đĩa
    disk_free = 0
    disk_total = 0
    try:
        usage = shutil.disk_usage(DOWNLOADS_DIR)
        disk_free = usage.free
        disk_total = usage.total
    except Exception:
        pass

    return {
        "version": VERSION,
        "author": AUTHOR,
        "python_version": sys.version.split()[0],
        "ytdlp_version": getattr(yt_dlp, "__version__", "2026"),
        "ffmpeg_status": "Sẵn sàng" if ffmpeg_ok else "Chưa cài đặt",
        "ffmpeg_path": ffmpeg_path or "Chưa có (Có thể tải tự động)",
        "ffmpeg_version": ffmpeg_ver,
        "ffmpeg_ok": ffmpeg_ok,
        "ffmpeg_ready": ffmpeg_ok,
        "has_ffprobe": has_ffprobe,
        "local_ip": local_ip,
        "port": cfg.get("server_port", 5000),
        "web_url_local": f"http://localhost:{cfg.get('server_port', 5000)}",
        "web_url_lan": f"http://{local_ip}:{cfg.get('server_port', 5000)}",
        "downloads_dir": DOWNLOADS_DIR,
        "disk_free_str": human_size(disk_free),
        "disk_total_str": human_size(disk_total),
        "public_url": get_public_url(),
        "has_cloudflared": os.path.isfile(os.path.join(BIN_DIR, "cloudflared.exe" if sys.platform == "win32" else "cloudflared")),
    }


def update_ytdlp() -> Tuple[bool, str]:
    """Cập nhật yt-dlp lên phiên bản mới nhất từ PyPI."""
    try:
        res = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if res.returncode == 0:
            return True, "Cập nhật yt-dlp thành công!"
        return False, res.stderr or "Lỗi cập nhật yt-dlp"
    except Exception as e:
        return False, str(e)


# ─────────────────────────────────────────────────────────── CLOUDFLARE PUBLIC TUNNEL
_tunnel_process: Optional[subprocess.Popen] = None
_tunnel_url: Optional[str] = None
_tunnel_lock = threading.Lock()


def start_public_tunnel(port: int = 5000, timeout: int = 20) -> Tuple[bool, str]:
    """Khởi chạy Cloudflare Tunnel tạo link công khai toàn cầu (HTTPS) miễn phí."""
    global _tunnel_process, _tunnel_url
    with _tunnel_lock:
        if _tunnel_url and _tunnel_process and _tunnel_process.poll() is None:
            return True, _tunnel_url

        cloudflared_exe = os.path.join(BIN_DIR, "cloudflared.exe" if sys.platform == "win32" else "cloudflared")
        if not os.path.isfile(cloudflared_exe):
            return False, "Chưa có cloudflared.exe trong thư mục bin/."

        try:
            cmd = [cloudflared_exe, "tunnel", "--url", f"http://localhost:{port}"]
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            _tunnel_process = proc
            _tunnel_url = None

            t0 = time.time()
            for line in proc.stderr:
                m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                if m:
                    _tunnel_url = m.group(0)
                    break
                if time.time() - t0 > timeout or proc.poll() is not None:
                    break

            if _tunnel_url:
                return True, _tunnel_url
            else:
                stop_public_tunnel()
                return False, "Không thể tạo link công khai (Hết thời gian chờ kết nối)."
        except Exception as e:
            stop_public_tunnel()
            return False, f"Lỗi tạo tunnel: {str(e)}"


def stop_public_tunnel() -> bool:
    """Dừng Cloudflare Tunnel."""
    global _tunnel_process, _tunnel_url
    with _tunnel_lock:
        if _tunnel_process:
            try:
                _tunnel_process.terminate()
            except Exception:
                pass
            _tunnel_process = None
        _tunnel_url = None
    return True


def get_public_url() -> Optional[str]:
    """Lấy link công khai hiện tại nếu đang bật."""
    global _tunnel_url, _tunnel_process
    if _tunnel_process and _tunnel_process.poll() is None:
        return _tunnel_url
    return None


# ─────────────────────────────────────────────────────────── KHÁM PHÁ Ý TƯỞNG & TÌM KIẾM GOOGLE / INTERNET
def fetch_google_suggestions(query: str, lang: str = "vi") -> List[str]:
    """Lấy gợi ý tìm kiếm từ Google Autocomplete API theo thời gian thực."""
    query = query.strip()
    if not query:
        return []
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://suggestqueries.google.com/complete/search?client=firefox&hl={lang}&q={encoded}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
                return [str(s) for s in data[1][:10]]
    except Exception:
        pass
    return []


def search_internet_videos(query: str, limit: int = 12) -> List[Dict[str, Any]]:
    """Tìm kiếm video/audio trên YouTube và Internet bằng yt-dlp flat search."""
    query = query.strip()
    if not query:
        return []

    limit = max(1, min(limit, 24))
    search_query = f"ytsearch{limit}:{query}"

    ydl_opts = {
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "skip_download": True,
    }

    results = []
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
            entries = info.get("entries", []) if info else []
            for item in entries:
                if not item:
                    continue
                url = item.get("url") or item.get("webpage_url")
                if not url and item.get("id"):
                    url = f"https://www.youtube.com/watch?v={item.get('id')}"

                thumbnails = item.get("thumbnails") or []
                thumb = item.get("thumbnail") or (thumbnails[-1].get("url") if thumbnails else "")
                if not thumb and item.get("id"):
                    thumb = f"https://i.ytimg.com/vi/{item.get('id')}/hqdefault.jpg"

                results.append({
                    "id": item.get("id", ""),
                    "title": item.get("title", "Video không tiêu đề"),
                    "url": url,
                    "thumbnail": thumb,
                    "duration": item.get("duration"),
                    "duration_str": human_duration(item.get("duration")),
                    "uploader": item.get("uploader") or item.get("channel", "Ẩn danh"),
                    "view_count": item.get("view_count"),
                    "views_str": f"{item.get('view_count'):,}" if item.get("view_count") else "—",
                    "platform": "YouTube",
                })
    except Exception as e:
        print(f"[SEARCH ERROR] {e}")

    return results


def get_trending_presets() -> List[Dict[str, Any]]:
    """Danh mục gợi ý xu hướng thịnh hành và ý tưởng làm video sáng tạo."""
    return [
        {
            "id": "tiktok_viral",
            "icon": "fa-brands fa-tiktok",
            "title": "TikTok Viral 2026",
            "subtitle": "Xu hướng video ngắn, biến hình & điệu nhảy triệu view",
            "query": "trending tiktok viral 2026",
            "tag": "Trending"
        },
        {
            "id": "douyin_remix",
            "icon": "fa-solid fa-music",
            "title": "Nhạc Douyin & Remix",
            "subtitle": "Giai điệu hot trend TikTok, beat chill, remix căng đét",
            "query": "nhac douyin hot trend tiktok remix 2026",
            "tag": "Music"
        },
        {
            "id": "movie_recap",
            "icon": "fa-solid fa-clapperboard",
            "title": "Tóm Tắt & Review Phim",
            "subtitle": "Ý tưởng kịch bản review phim điện ảnh, anime, drama",
            "query": "review phim hay tom tat phim 2026",
            "tag": "Cinema"
        },
        {
            "id": "nature_4k",
            "icon": "fa-solid fa-mountain-sun",
            "title": "Kho Video 4K Chill",
            "subtitle": "Cảnh quay thiên nhiên 4K HDR, drone phong cảnh, thư giãn",
            "query": "4k 60fps scenic relaxation nature drone footage",
            "tag": "4K Ultra"
        },
        {
            "id": "capcut_template",
            "icon": "fa-solid fa-wand-magic-sparkles",
            "title": "CapCut & Meme Templates",
            "subtitle": "Mẫu edit thịnh hành, hài hước, hiệu ứng giật giật",
            "query": "capcut template trend viral meme clip",
            "tag": "Creative"
        },
        {
            "id": "podcast_story",
            "icon": "fa-solid fa-microphone-lines",
            "title": "Podcast & Truyện Cảm Động",
            "subtitle": "Đoạn cắt podcast truyền cảm hứng, bài học cuộc sống",
            "query": "podcast viral tam su truyen cam hung",
            "tag": "Podcast"
        }
    ]


def generate_creative_prompts(topic: str) -> Dict[str, Any]:
    """Tạo ý tưởng kịch bản, câu Hook mở đầu và hashtag cho chủ đề được chọn."""
    topic_clean = topic.strip()
    return {
        "topic": topic_clean,
        "hooks": [
            f"⚡ 'Có thể bạn chưa biết: Bí mật đằng sau {topic_clean} mà 99% mọi người bỏ lỡ...'",
            f"🔥 'Đừng lướt qua nếu bạn đang tìm kiếm ý tưởng về {topic_clean} đỉnh nhất năm 2026!'",
            f"💡 '3 bước cực đơn giản để làm chủ {topic_clean} chỉ trong 60 giây.'",
            f"😱 'Sự thật gây sốc về {topic_clean} mà không ai nói cho bạn biết!'"
        ],
        "script_outline": [
            "1. 0s - 3s: Hook giật tít giữ chân người xem ngay giây đầu tiên.",
            "2. 3s - 15s: Nêu vấn đề hoặc nỗi đau thường gặp liên quan đến chủ đề.",
            "3. 15s - 45s: Đưa ra giải pháp / nội dung chính hấp dẫn kèm hình ảnh sinh động.",
            "4. 45s - 60s: Call To Action (Kêu gọi Like, Share, Lưu video để xem lại)."
        ],
        "hashtags": [
            f"#{topic_clean.replace(' ', '')}",
            "#Trending2026",
            "#TikTokViral",
            "#VideoProMax",
            "#ContentCreator",
            "#Hottrend"
        ]
    }


# ─────────────────────────────────────────────────────────── TRỤ CỘT 1: ATRIA DAWN AI SUITE (REASONING ENGINE)
def get_atria_api_key(custom_key: Optional[str] = None) -> str:
    """Lấy API Key Atria từ tham số hoặc cấu hình settings.json."""
    if custom_key and custom_key.strip():
        return custom_key.strip()
    cfg = load_settings()
    return cfg.get("atria_api_key", "atr_lF0uyZqCnwVD_TbmRbAT6RdmulpK390g").strip()


def call_atria_ai(
    input_text: str,
    api_key: Optional[str] = None,
    timeout: int = 50
) -> Tuple[bool, str, Optional[str]]:
    """
    Gọi Atria Dawn AI Reasoning Model qua endpoint Responses API.
    Trả về (thành_công: bool, nội_dung_trả_lời: str, suy_luận_nội_tại: Optional[str]).
    """
    key = get_atria_api_key(api_key)
    if not key:
        return False, "Chưa cấu hình Atria AI API Key. Vui lòng vào Cài đặt để thêm key.", None

    url = "https://api.atria-asi.ai/v1/responses"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "Atria-Dawn-Preview",
        "input": input_text.strip()
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))

            reasoning_text = None
            answer_text = None

            for item in data.get("output", []):
                item_type = item.get("type")
                if item_type == "reasoning":
                    for c in item.get("content", []):
                        if c.get("type") == "reasoning_text":
                            reasoning_text = c.get("text", "")
                elif item_type == "message" and item.get("role") == "assistant":
                    for c in item.get("content", []):
                        if c.get("type") == "output_text":
                            answer_text = c.get("text", "")

            if answer_text:
                return True, answer_text.strip(), reasoning_text
            return False, "Atria AI không trả về nội dung hợp lệ.", reasoning_text

    except urllib.error.HTTPError as e:
        err_msg = f"HTTP {e.code}: {e.reason}"
        try:
            err_body = e.read().decode("utf-8")
            err_msg += f" - {err_body}"
        except Exception:
            pass
        return False, err_msg, None
    except socket.timeout:
        return False, "Thời gian chờ Atria AI phản hồi quá lâu (Timeout). Vui lòng thử lại với yêu cầu ngắn hơn.", None
    except Exception as e:
        return False, f"Lỗi kết nối Atria AI: {str(e)}", None


def test_atria_api_key(api_key: Optional[str] = None) -> Dict[str, Any]:
    """Kiểm tra tính hợp lệ của API Key Atria và đo độ trễ (latency)."""
    t0 = time.time()
    ok, reply, reasoning = call_atria_ai("Xin chào, hãy trả lời 'OK' trong đúng 1 từ.", api_key=api_key, timeout=20)
    latency_ms = int((time.time() - t0) * 1000)
    return {
        "ok": ok,
        "latency_ms": latency_ms,
        "message": "Kết nối Atria AI thành công!" if ok else reply,
        "preview": reply[:100] if ok else None
    }


def ai_summarize_video(
    title: str,
    description: str = "",
    duration_str: str = "",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Tóm tắt nội dung video, trích xuất điểm nhấn và ý tưởng chuyển thể."""
    prompt = f"""Bạn là chuyên gia phân tích nội dung truyền thông đa phương tiện.
Hãy phân tích và tóm tắt chi tiết video sau đây:
- Tiêu đề: {title}
- Thời lượng: {duration_str or 'Không rõ'}
- Mô tả nguồn: {description[:1500] if description else 'Nội dung thịnh hành'}

Hãy trình bày theo cấu trúc Markdown chuyên nghiệp:
1. 📌 TỔNG QUAN NỘI DUNG (Trong 2-3 câu súc tích)
2. 💡 4-5 BÀI HỌC / ĐIỂM NHẤN CỐT LÕI (Bullets có icon)
3. 🎯 PHÂN TÍCH TÂM LÝ KHÁN GIẢ (Tại sao video này thu hút)
4. 🚀 3 Ý TƯỞNG RE-MAKE / LÀM LẠI CHO TIKTOK / SHORTS (Kèm góc nhìn mới)
"""
    ok, res, reasoning = call_atria_ai(prompt, api_key=api_key, timeout=60)
    return {"ok": ok, "content": res, "reasoning": reasoning}


def ai_generate_shorts_script(
    topic_or_title: str,
    style: str = "viral",
    duration: int = 60,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Tạo kịch bản video ngắn (Shorts / Reels / TikTok) 30s-60s kèm chỉ dẫn quay."""
    prompt = f"""Bạn là đạo diễn kịch bản video ngắn triệu view hàng đầu trên TikTok và YouTube Shorts.
Hãy viết một kịch bản hoàn chỉnh cho video ngắn thời lượng khoảng {duration} giây.
- Chủ đề: {topic_or_title}
- Phong cách: {style} (kịch tính, lôi cuốn, nhịp điệu nhanh)

Yêu cầu định dạng cấu trúc chi tiết:
1. 🎬 TIÊU ĐỀ VIDEO (Gợi ý 2 tiêu đề giật tít, khơi gợi tò mò)
2. ⏱️ KỊCH BẢN CHI TIẾT TỪNG PHÂN CẢNH:
   - [00:00 - 00:03] HOOK CÂU VIEW: (Lời thoại mở đầu giật gân + Hành động hình ảnh / B-roll giữ chân)
   - [00:03 - 00:15] NÊU VẤN ĐỀ: (Đánh vào nỗi đau / thắc mắc của người xem)
   - [00:15 - 00:45] CAO TRÀO & GIẢI PHÁP: (Lời thoại chính, nhịp điệu dồn dập, hướng dẫn cụ thể)
   - [00:45 - 00:60] CALL TO ACTION (CTA): (Kêu gọi bình luận, lưu video và chia sẻ)
3. 🎵 GỢI Ý ÂM THANH & BGM: (Nhạc nền phù hợp, hiệu ứng âm thanh SFX whoosh, ding, pop)
4. 🏷️ HASHTAGS ĐỀ XUẤT: (10 thẻ hashtag chuẩn SEO)
"""
    ok, res, reasoning = call_atria_ai(prompt, api_key=api_key, timeout=60)
    return {"ok": ok, "content": res, "reasoning": reasoning}


def ai_generate_viral_hooks(
    topic_or_title: str,
    count: int = 5,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Tạo 5 câu Hook mở đầu 3 giây giữ chân người xem theo 5 tâm lý."""
    prompt = f"""Bạn là bậc thầy sáng tạo Hook câu view 3 giây đầu trên TikTok, Reels và YouTube Shorts.
Hãy tạo đúng {count} câu Hook mở đầu cực kỳ cuốn hút cho chủ đề: '{topic_or_title}'.

Chia thành 5 phong cách tâm lý:
1. 🕵️ PHONG CÁCH TÒ MÒ & BÍ ẨN: (Khơi gợi điều 99% mọi người chưa biết)
2. ⚡ PHONG CÁCH GÂY SỐC & CẢNH BÁO: (Dừng lại ngay, sự thật ngỡ ngàng)
3. ⏳ PHONG CÁCH FOMO & LỢI ÍCH CỰC ĐẠI: (Xem ngay kẻo bỏ lỡ cơ hội lớn)
4. 🥊 PHONG CÁCH THÁCH THỨC & TRANH LUẬN: (Ý kiến ngược số đông)
5. 😂 PHONG CÁCH HÀI HƯỚC & ĐỒNG CẢM: (Ai cũng từng trải qua tình huống này)

Dưới mỗi câu Hook, ghi kèm 1 dòng gợi ý hành động hình ảnh (Visual Action) tương ứng để đạt hiệu quả cao nhất.
"""
    ok, res, reasoning = call_atria_ai(prompt, api_key=api_key, timeout=50)
    return {"ok": ok, "content": res, "reasoning": reasoning}


def ai_generate_seo_metadata(
    topic_or_title: str,
    platform: str = "tiktok",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Tạo tiêu đề giật tít, mô tả chuẩn SEO và hashtag thịnh hành."""
    prompt = f"""Bạn là chuyên gia tối ưu hóa SEO video và thuật toán đề xuất cho {platform.upper()}.
Dựa trên chủ đề: '{topic_or_title}', hãy tạo bộ thông số hoàn hảo:

1. 🔥 5 TIÊU ĐỀ GIẬT TÍT (Click-through-rate cao, không vi phạm chính sách)
2. 📝 ĐOẠN MÔ TẢ VIDEO (Khoảng 3-4 dòng, kích thích tương tác bình luận)
3. 🏷️ 15 HASHTAG THỊNH HÀNH (Phân nhóm: 5 hashtag ngách, 5 hashtag phổ thông, 5 hashtag trending 2026)
4. ⏰ KHUNG GIỜ VÀNG ĐĂNG VIDEO KHUYẾN NGHỊ (Cho đối tượng khán giả Việt Nam)
"""
    ok, res, reasoning = call_atria_ai(prompt, api_key=api_key, timeout=50)
    return {"ok": ok, "content": res, "reasoning": reasoning}


def ai_chat_completion(
    messages: List[Dict[str, str]],
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Trợ lý trò chuyện sáng tạo AI hỗ trợ người dùng brainstorm ý tưởng video liên tục."""
    system_inst = "Bạn là trợ lý AI sáng tạo nội dung Video Pro Max Studio, am hiểu sâu sắc về TikTok, YouTube Shorts, Reels, kịch bản video và thuật toán viral 2026. Hãy trả lời thân thiện, hữu ích, trực tiếp và gợi ý các ý tưởng sáng tạo độc đáo bằng tiếng Việt."

    # Ghép lịch sử trò chuyện thành prompt ngữ cảnh
    convo_parts = [system_inst, "\nLịch sử trò chuyện:"]
    for m in messages[-8:]:  # Giữ 8 tin nhắn gần nhất
        role = "Khán giả" if m.get("role") == "user" else "Trợ lý Video Pro Max"
        convo_parts.append(f"{role}: {m.get('content', '')}")
    convo_parts.append("Trợ lý Video Pro Max:")

    prompt = "\n".join(convo_parts)
    ok, res, reasoning = call_atria_ai(prompt, api_key=api_key, timeout=60)
    return {"ok": ok, "content": res, "reasoning": reasoning}


# ─────────────────────────────────────────────────────────── TRỤ CỘT 2: CREATIVE RE-UP ENGINE (ANTI-CONTENT ID)
def process_reup_media(
    filename: str,
    options: Dict[str, Any],
    progress_cb: Optional[Callable[[Dict[str, Any]], None]] = None
) -> Dict[str, Any]:
    """
    Xử lý tái tạo và lách bản quyền video chuyên nghiệp:
    - flip_h: Lật gương khung hình
    - speed: Tinh chỉnh tốc độ vi mô (1.01x - 1.15x) giữ nguyên cao độ âm thanh
    - zoom: Cắt xén và phóng to vi mô (1.01x - 1.05x) chống nhận diện pixel
    - blur_canvas_916: Chuyển đổi video ngang 16:9 sang dọc 9:16 có nền mờ nghệ thuật
    - watermark_text: Chèn chữ bản quyền cá nhân vào góc
    - strip_metadata: Xóa exif cũ và spoof camera metadata mới
    - cut_start, cut_end: Cắt khoảng thời gian
    """
    safe_name = os.path.basename(filename)
    in_path = os.path.join(DOWNLOADS_DIR, safe_name)
    if not os.path.isfile(in_path):
        for root, _dirs, files in os.walk(DOWNLOADS_DIR):
            if safe_name in files:
                in_path = os.path.join(root, safe_name)
                break
        if not os.path.isfile(in_path):
            return {"ok": False, "error": f"Không tìm thấy tệp '{safe_name}' trong kho tải về."}

    ffmpeg_bin = find_ffmpeg()
    if not ffmpeg_bin:
        return {"ok": False, "error": "Chưa cài đặt FFmpeg trên hệ thống. Vui lòng cài đặt trước."}

    base, ext = os.path.splitext(safe_name)
    out_ext = ext.lower() if ext.lower() in (".mp4", ".mkv", ".webm", ".mov") else ".mp4"
    timestamp_tag = int(time.time())
    out_name = f"{base}_reup_{timestamp_tag}{out_ext}"
    out_path = os.path.join(DOWNLOADS_DIR, out_name)

    # Đọc các tùy chọn
    flip_h = bool(options.get("flip_h", False))
    speed = float(options.get("speed", 1.0))
    zoom = float(options.get("zoom", 1.0))
    blur_canvas_916 = bool(options.get("blur_canvas_916", False))
    watermark_text = str(options.get("watermark_text", "")).strip()
    strip_metadata = bool(options.get("strip_metadata", True))
    cut_start = options.get("cut_start")
    cut_end = options.get("cut_end")

    if progress_cb:
        progress_cb({"percent": 10, "message": "Đang phân tích định dạng và thiết lập bộ lọc..."})

    # Xây dựng chuỗi lọc video và âm thanh
    video_filters = []
    audio_filters = []

    # 1. Tốc độ vi mô (Speed)
    if 1.01 <= speed <= 1.25:
        video_filters.append(f"setpts=PTS/{speed:.3f}")
        audio_filters.append(f"atempo={speed:.3f}")

    # 2. Lật gương (Flip Horizontal)
    if flip_h:
        video_filters.append("hflip")

    # 3. Thu phóng vi mô (Zoom)
    if 1.01 <= zoom <= 1.10:
        crop_factor = 1.0 / zoom
        video_filters.append(f"crop=in_w*{crop_factor:.3f}:in_h*{crop_factor:.3f}:(in_w-out_w)/2:(in_h-out_h)/2,scale=in_w:in_h")

    # 4. Chèn watermark chữ
    if watermark_text:
        clean_text = watermark_text.replace("'", "").replace(":", "").replace("\\", "")
        video_filters.append(f"drawtext=text='{clean_text}':x=w-tw-25:y=h-th-25:fontsize=22:fontcolor=white@0.85:shadowcolor=black@0.6:shadowx=2:shadowy=2")

    # Xây dựng lệnh FFmpeg
    cmd = [ffmpeg_bin, "-y"]

    # Cắt khoảng thời gian
    if cut_start is not None and float(cut_start) > 0:
        cmd.extend(["-ss", str(cut_start)])
    if cut_end is not None and float(cut_end) > (float(cut_start) if cut_start else 0):
        cmd.extend(["-to", str(cut_end)])

    cmd.extend(["-i", in_path])

    # Xử lý trường hợp Blur Canvas 9:16 (Yêu cầu filter_complex riêng biệt)
    if blur_canvas_916:
        vf_chain = ("," + ",".join(video_filters)) if video_filters else ""
        filter_complex = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[bg];"
            f"[0:v]scale=1080:-2{vf_chain}[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[vout]"
        )
        cmd.extend(["-filter_complex", filter_complex, "-map", "[vout]", "-map", "0:a?"])
    else:
        if video_filters:
            cmd.extend(["-vf", ",".join(video_filters)])
        if audio_filters:
            cmd.extend(["-af", ",".join(audio_filters)])

    # Làm mới Metadata & Spoof Exif chống Content ID
    if strip_metadata:
        cmd.extend([
            "-map_metadata", "-1",
            "-metadata", f"title=Video_Studio_{timestamp_tag}",
            "-metadata", "artist=Studio Creator Pro",
            "-metadata", "comment=Shot on Apple iPhone 16 Pro Max",
            "-metadata", "encoder=Apple VideoToolbox HEVC Core v3.0",
        ])

    # Mã hóa chất lượng cao tương thích tuyệt đối
    cmd.extend([
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        out_path
    ])

    if progress_cb:
        progress_cb({"percent": 30, "message": "Đang khởi chạy FFmpeg Master Build xử lý tái tạo video..."})

    try:
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        _stdout, stderr = process.communicate()

        if process.returncode != 0:
            return {"ok": False, "error": f"FFmpeg xử lý thất bại: {stderr[-500:] if stderr else 'Mã lỗi'}"}

        if not os.path.isfile(out_path) or os.path.getsize(out_path) == 0:
            return {"ok": False, "error": "Tệp đầu ra rỗng hoặc không được tạo thành công."}

        out_size = os.path.getsize(out_path)
        if progress_cb:
            progress_cb({"percent": 100, "message": "Hoàn tất tái tạo video thành công!"})

        return {
            "ok": True,
            "filename": out_name,
            "filepath": out_path,
            "size": out_size,
            "size_str": human_size(out_size),
            "message": f"Tái tạo video lách bản quyền thành công: {out_name}"
        }

    except Exception as e:
        return {"ok": False, "error": f"Lỗi ngoại lệ khi xử lý video: {str(e)}"}


