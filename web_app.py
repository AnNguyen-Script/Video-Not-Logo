# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║   TOOL TẢI VIDEO PRO v4.0 MAX — WEB SERVER & API                     ║
║   © Bản quyền: An Nguyễn                                             ║
║   FastAPI + Uvicorn + WebSockets + Streaming Media Range Server      ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import io
import json
import os
import re
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
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import (
    FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect,
    status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import engine

ROOT_DIR = engine.ROOT_DIR
main_loop: Optional[asyncio.AbstractEventLoop] = None


def open_browser_delayed():
    time.sleep(1.2)
    try:
        import webbrowser
        webbrowser.open("http://localhost:5000")
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    global main_loop
    main_loop = asyncio.get_running_loop()
    # Tự động mở trình duyệt web khi server sẵn sàng
    threading.Thread(target=open_browser_delayed, daemon=True).start()

    # Tự động bật Cloudflare Tunnel nếu chạy với cờ --public
    if "--public" in sys.argv:
        def auto_tunnel():
            time.sleep(0.8)
            cfg = engine.load_settings()
            port = int(cfg.get("server_port", 5000))
            ok, url = engine.start_public_tunnel(port=port)
            if ok:
                broadcast_sync({
                    "type": "tunnel_status",
                    "active": True,
                    "public_url": url
                })
                # Tự động copy link vào clipboard của Windows để người dùng chỉ việc Ctrl+V
                try:
                    import subprocess
                    subprocess.run(["clip"], input=url, text=True, check=False)
                    clip_notice = "  ✔ [ĐÃ TỰ ĐỘNG SAO CHÉP LINK VÀO CLIPBOARD - BẤM CTRL+V ĐỂ GỬI]"
                except Exception:
                    clip_notice = ""

                print("\n" + "=" * 65)
                print("  ★ LINK WEB CÔNG KHAI TOÀN CẦU (HTTPS) ĐÃ SẴN SÀNG!")
                print(f"  ► LINK CỦA BẠN:  {url}")
                if clip_notice:
                    print(clip_notice)
                print("  -------------------------------------------------------------")
                print("  💡 LƯU Ý: Không cần bôi đen bấm Ctrl+C (Ctrl+C sẽ TẮT server).")
                print("  💡 Bạn chỉ cần mở Zalo/Messenger/FB rồi bấm Ctrl+V để gửi!")
                print("=" * 65 + "\n")
        threading.Thread(target=auto_tunnel, daemon=True).start()

    yield
    # Dọn dẹp tunnel khi dừng server
    engine.stop_public_tunnel()


app = FastAPI(
    title="Tool Tải Video PRO Web Edition",
    description="Máy chủ API và Web Tool tải video/âm thanh không logo chất lượng cao",
    version=engine.VERSION,
    lifespan=lifespan,
)

# Cho phép CORS cho mọi nguồn (để dễ dàng chia sẻ và tích hợp)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────── QUẢN LÝ TÁC VỤ & WEBSOCKET
class ConnectionManager:
    """Quản lý các kết nối WebSocket thời gian thực."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = threading.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        with self._lock:
            self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Gửi dữ liệu tới tất cả client đang kết nối."""
        payload = json.dumps(message, ensure_ascii=False)
        disconnected = []
        with self._lock:
            conns = list(self.active_connections)

        for connection in conns:
            try:
                await connection.send_text(payload)
            except Exception:
                disconnected.append(connection)

        if disconnected:
            with self._lock:
                for c in disconnected:
                    if c in self.active_connections:
                        self.active_connections.remove(c)


ws_manager = ConnectionManager()


def broadcast_sync(message: Dict[str, Any]):
    """Gọi broadcast an toàn từ thread nền (Background Worker Thread)."""
    global main_loop
    if main_loop and main_loop.is_running():
        try:
            asyncio.run_coroutine_threadsafe(ws_manager.broadcast(message), main_loop)
        except Exception:
            pass


# Quản lý hàng đợi và trạng thái các tác vụ tải
tasks_db: Dict[str, Dict[str, Any]] = {}
tasks_cancel_flags: Dict[str, threading.Event] = {}
tasks_lock = threading.Lock()


# ─────────────────────────────────────────────────────────── PYDANTIC MODELS
class AnalyzeRequest(BaseModel):
    url: str
    browser: Optional[str] = None


class DownloadRequest(BaseModel):
    url: str
    quality: str = "best"
    audio_only: bool = False
    audio_bitrate: str = "192"
    cut_start: Optional[float] = None
    cut_end: Optional[float] = None
    subs_lang: Optional[str] = None
    is_playlist: bool = False


class BatchDownloadRequest(BaseModel):
    urls: List[str]
    quality: str = "best"
    audio_only: bool = False
    audio_bitrate: str = "192"


class CutRequest(BaseModel):
    filename: str
    start: float
    end: float


class ConvertRequest(BaseModel):
    filename: str
    target_format: str
    bitrate: str = "192k"


class SettingsRequest(BaseModel):
    settings: Dict[str, Any]


class AISummarizeRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    duration_str: Optional[str] = ""
    api_key: Optional[str] = None


class AIScriptRequest(BaseModel):
    topic: str
    style: Optional[str] = "viral"
    duration: Optional[int] = 60
    api_key: Optional[str] = None


class AIHooksRequest(BaseModel):
    topic: str
    count: Optional[int] = 5
    api_key: Optional[str] = None


class AISeoRequest(BaseModel):
    topic: str
    platform: Optional[str] = "tiktok"
    api_key: Optional[str] = None


class AIChatRequest(BaseModel):
    message: Optional[str] = None
    messages: Optional[List[Dict[str, str]]] = None
    api_key: Optional[str] = None


class AIPingRequest(BaseModel):
    api_key: Optional[str] = None


class ReupProcessRequest(BaseModel):
    filename: str
    flip_h: bool = False
    speed: float = 1.04
    zoom: float = 1.02
    blur_canvas_916: bool = False
    watermark_text: Optional[str] = ""
    strip_metadata: bool = True
    cut_start: Optional[float] = None
    cut_end: Optional[float] = None


# ─────────────────────────────────────────────────────────── BACKGROUND WORKER
def run_download_task(task_id: str, req: DownloadRequest):
    """Xử lý tải một link video/audio trong thread riêng."""
    cancel_flag = threading.Event()
    with tasks_lock:
        tasks_cancel_flags[task_id] = cancel_flag

    def on_progress(p_data: Dict[str, Any]):
        with tasks_lock:
            if task_id in tasks_db:
                tasks_db[task_id]["progress"] = p_data
                tasks_db[task_id]["stage"] = p_data.get("stage", "downloading")
                tasks_db[task_id]["updated_at"] = time.time()

        broadcast_sync({
            "type": "task_progress",
            "task_id": task_id,
            "data": p_data
        })

    cut_range = None
    if req.cut_end and req.cut_end > (req.cut_start or 0):
        cut_range = (req.cut_start or 0, req.cut_end)

    res = engine.download_media(
        url=req.url,
        quality=req.quality,
        audio_only=req.audio_only,
        audio_bitrate=req.audio_bitrate,
        out_dir=engine.DOWNLOADS_DIR,
        cut_range=cut_range,
        subs_lang=req.subs_lang,
        is_playlist=req.is_playlist,
        progress_cb=on_progress,
        cancel_flag=cancel_flag,
    )

    with tasks_lock:
        if task_id in tasks_db:
            tasks_db[task_id]["status"] = "completed" if res.get("ok") else "failed"
            tasks_db[task_id]["result"] = res
            tasks_db[task_id]["stage"] = "completed" if res.get("ok") else "error"
            tasks_db[task_id]["completed_at"] = time.time()
        if task_id in tasks_cancel_flags:
            del tasks_cancel_flags[task_id]

    broadcast_sync({
        "type": "task_completed",
        "task_id": task_id,
        "ok": res.get("ok", False),
        "result": res
    })


# ─────────────────────────────────────────────────────────── REST API ENDPOINTS
@app.get("/api/system/status")
def api_system_status():
    """Lấy thông tin hệ thống, FFmpeg và IP chia sẻ mạng LAN."""
    info = engine.get_system_info()
    return {"ok": True, "data": info}


@app.post("/api/analyze")
def api_analyze(req: AnalyzeRequest):
    """Phân tích đường link video/playlist để xem trước."""
    res = engine.analyze_url(req.url, browser=req.browser)
    return res


@app.post("/api/download")
def api_download(req: DownloadRequest):
    """Bắt đầu tác vụ tải xuống."""
    task_id = str(uuid.uuid4())[:8]
    task_info = {
        "id": task_id,
        "url": req.url,
        "quality": req.quality,
        "audio_only": req.audio_only,
        "audio_bitrate": req.audio_bitrate,
        "status": "running",
        "stage": "starting",
        "created_at": time.time(),
        "progress": {"percent": 0, "message": "Đang khởi tạo tác vụ..."},
        "result": None,
    }

    with tasks_lock:
        tasks_db[task_id] = task_info

    # Khởi chạy trong thread nền
    th = threading.Thread(target=run_download_task, args=(task_id, req), daemon=True)
    th.start()

    return {"ok": True, "task_id": task_id, "message": "Đã bắt đầu tác vụ tải xuống."}


@app.post("/api/download/batch")
def api_download_batch(req: BatchDownloadRequest):
    """Khởi chạy tải hàng loạt danh sách link."""
    task_ids = []
    for u in req.urls:
        u = u.strip()
        if not u or not u.startswith("http"):
            continue
        sub_req = DownloadRequest(
            url=u,
            quality=req.quality,
            audio_only=req.audio_only,
            audio_bitrate=req.audio_bitrate,
        )
        t_id = str(uuid.uuid4())[:8]
        with tasks_lock:
            tasks_db[t_id] = {
                "id": t_id,
                "url": u,
                "quality": req.quality,
                "audio_only": req.audio_only,
                "audio_bitrate": req.audio_bitrate,
                "status": "running",
                "stage": "starting",
                "created_at": time.time(),
                "progress": {"percent": 0, "message": "Đang chờ tải..."},
                "result": None,
            }
        th = threading.Thread(target=run_download_task, args=(t_id, sub_req), daemon=True)
        th.start()
        task_ids.append(t_id)

    return {"ok": True, "task_ids": task_ids, "count": len(task_ids)}


@app.get("/api/tasks")
def api_get_tasks():
    """Lấy danh sách toàn bộ tác vụ đang chạy hoặc đã xong."""
    with tasks_lock:
        items = list(tasks_db.values())
    items.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    return {"ok": True, "tasks": items}


@app.post("/api/tasks/{task_id}/cancel")
def api_cancel_task(task_id: str):
    """Hủy một tác vụ đang tải."""
    with tasks_lock:
        if task_id in tasks_cancel_flags:
            tasks_cancel_flags[task_id].set()
            if task_id in tasks_db:
                tasks_db[task_id]["status"] = "cancelled"
                tasks_db[task_id]["stage"] = "cancelled"
            return {"ok": True, "message": "Đã gửi lệnh hủy tác vụ."}
    return {"ok": False, "error": "Không tìm thấy tác vụ hoặc tác vụ đã kết thúc."}


@app.get("/api/files")
def api_list_files():
    """Liệt kê các tệp đã tải trong thư mục downloads/."""
    files = engine.list_downloaded_files()
    return {"ok": True, "files": files, "count": len(files)}


@app.get("/api/files/download/{filename:path}")
def api_download_file(filename: str):
    """Cho phép người dùng hoặc bạn bè tải trực tiếp file về thiết bị (Browser Download)."""
    import urllib.parse
    decoded_name = urllib.parse.unquote(filename)
    safe_name = os.path.basename(decoded_name)
    fpath = os.path.join(engine.DOWNLOADS_DIR, safe_name)
    if not os.path.isfile(fpath):
        # Thử tìm đệ quy trong thư mục con (ví dụ playlist)
        found = None
        for root, _dirs, files in os.walk(engine.DOWNLOADS_DIR):
            if safe_name in files:
                found = os.path.join(root, safe_name)
                break
        if not found:
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp.")
        fpath = found

    return FileResponse(
        path=fpath,
        filename=safe_name,
        media_type="application/octet-stream"
    )


@app.get("/api/files/stream/{filename:path}")
def api_stream_file(filename: str, request: Request):
    """
    Phát trực tuyến video/audio mượt mà với hỗ trợ HTTP 206 Partial Content (Range Request).
    Hỗ trợ tua nhanh, phát trên Safari iOS, Chrome Android, máy tính.
    """
    import urllib.parse
    decoded_name = urllib.parse.unquote(filename)
    safe_name = os.path.basename(decoded_name)
    fpath = os.path.join(engine.DOWNLOADS_DIR, safe_name)
    if not os.path.isfile(fpath):
        for root, _dirs, files in os.walk(engine.DOWNLOADS_DIR):
            if safe_name in files:
                fpath = os.path.join(root, safe_name)
                break
        if not os.path.isfile(fpath):
            raise HTTPException(status_code=404, detail="Không tìm thấy tệp.")

    file_size = os.path.getsize(fpath)
    range_header = request.headers.get("Range")

    ext = os.path.splitext(safe_name)[1].lower()
    media_types = {
        ".mp4": "video/mp4",
        ".mkv": "video/x-matroska",
        ".webm": "video/webm",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".wav": "audio/wav",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
    }
    content_type = media_types.get(ext, "application/octet-stream")

    if not range_header:
        return FileResponse(path=fpath, media_type=content_type)

    # Xử lý HTTP Range header
    try:
        range_match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if not range_match:
            return FileResponse(path=fpath, media_type=content_type)

        start_str, end_str = range_match.groups()
        start = int(start_str)
        end = int(end_str) if end_str else file_size - 1

        if start >= file_size or end >= file_size or start > end:
            return Response(
                status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                headers={"Content-Range": f"bytes */{file_size}"}
            )

        chunk_size = end - start + 1

        def iterfile():
            with open(fpath, "rb") as f:
                f.seek(start)
                bytes_left = chunk_size
                while bytes_left > 0:
                    read_len = min(64 * 1024, bytes_left)
                    data = f.read(read_len)
                    if not data:
                        break
                    bytes_left -= len(data)
                    yield data

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
            "Content-Type": content_type,
        }
        return StreamingResponse(iterfile(), status_code=206, headers=headers)

    except Exception:
        return FileResponse(path=fpath, media_type=content_type)


@app.delete("/api/files/{filename:path}")
def api_delete_file(filename: str):
    """Xóa một tệp trong kho downloads/ với cơ chế xử lý file locking an toàn trên Windows."""
    import urllib.parse
    import gc
    decoded_name = urllib.parse.unquote(filename)
    safe_name = os.path.basename(decoded_name)
    fpath = os.path.join(engine.DOWNLOADS_DIR, safe_name)
    if not os.path.isfile(fpath):
        for root, _dirs, files in os.walk(engine.DOWNLOADS_DIR):
            if safe_name in files:
                fpath = os.path.join(root, safe_name)
                break
        if not os.path.isfile(fpath):
            raise HTTPException(status_code=404, detail="Tệp không tồn tại.")

    # Thu gom rác để đóng các file handle còn mở dở
    gc.collect()

    # Thử xóa với cơ chế retry (chờ các socket/stream vừa ngắt đóng hẳn handle)
    last_err = None
    for attempt in range(8):
        try:
            os.remove(fpath)
            return {"ok": True, "message": f"Đã xóa thành công {safe_name}"}
        except PermissionError as e:
            last_err = e
            time.sleep(0.35)
            gc.collect()
        except OSError as e:
            last_err = e
            time.sleep(0.35)
            gc.collect()

    # Nếu vẫn bị khóa tạm thời, thử đổi tên sang file ẩn rồi xóa
    try:
        tmp_del_name = os.path.join(os.path.dirname(fpath), f".trash_{int(time.time())}_{safe_name}")
        os.rename(fpath, tmp_del_name)
        try:
            os.remove(tmp_del_name)
        except Exception:
            pass
        return {"ok": True, "message": f"Đã xóa thành công {safe_name}"}
    except Exception:
        pass

    return {"ok": False, "error": f"Tệp đang được mở hoặc xem trước. Vui lòng thử lại sau 1-2 giây: {str(last_err)}"}


# ─────────────────────────────────────────────────────────── HỘP CÔNG CỤ TOOLBOX API
@app.post("/api/toolbox/cut")
def api_toolbox_cut(req: CutRequest):
    """Cắt file theo số giây."""
    fpath = os.path.join(engine.DOWNLOADS_DIR, os.path.basename(req.filename))
    if not os.path.isfile(fpath):
        return {"ok": False, "error": "Tệp không tồn tại trong thư mục tải về."}

    try:
        out = engine.cut_media_file(fpath, req.start, req.end)
        return {
            "ok": True,
            "output_file": os.path.basename(out),
            "size": os.path.getsize(out),
            "size_str": engine.human_size(os.path.getsize(out)),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/toolbox/convert")
def api_toolbox_convert(req: ConvertRequest):
    """Chuyển đổi định dạng file."""
    fpath = os.path.join(engine.DOWNLOADS_DIR, os.path.basename(req.filename))
    if not os.path.isfile(fpath):
        return {"ok": False, "error": "Tệp không tồn tại trong thư mục tải về."}

    try:
        out = engine.convert_media_file(fpath, req.target_format, req.bitrate)
        return {
            "ok": True,
            "output_file": os.path.basename(out),
            "size": os.path.getsize(out),
            "size_str": engine.human_size(os.path.getsize(out)),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ─────────────────────────────────────────────────────────── TRỤ CỘT 1: ATRIA DAWN AI STUDIO API
@app.post("/api/ai/ping")
def api_ai_ping(req: Optional[AIPingRequest] = None):
    """Kiểm tra tín hiệu kết nối tới Atria AI."""
    api_key = req.api_key if req else None
    res = engine.test_atria_api_key(api_key=api_key)
    return res


@app.post("/api/ai/summarize")
def api_ai_summarize(req: AISummarizeRequest):
    """Tóm tắt video chuyên sâu bằng Atria AI Reasoning."""
    res = engine.ai_summarize_video(
        title=req.title,
        description=req.description or "",
        duration_str=req.duration_str or "",
        api_key=req.api_key
    )
    return res


@app.post("/api/ai/script")
def api_ai_script(req: AIScriptRequest):
    """Sinh kịch bản video ngắn triệu view bằng Atria AI."""
    res = engine.ai_generate_shorts_script(
        topic_or_title=req.topic,
        style=req.style or "viral",
        duration=req.duration or 60,
        api_key=req.api_key
    )
    return res


@app.post("/api/ai/hooks")
def api_ai_hooks(req: AIHooksRequest):
    """Tạo 5 Hook mở đầu 3 giây giữ chân người xem bằng Atria AI."""
    res = engine.ai_generate_viral_hooks(
        topic_or_title=req.topic,
        count=req.count or 5,
        api_key=req.api_key
    )
    return res


@app.post("/api/ai/seo")
def api_ai_seo(req: AISeoRequest):
    """Tạo tiêu đề giật tít, mô tả và hashtag SEO bằng Atria AI."""
    res = engine.ai_generate_seo_metadata(
        topic_or_title=req.topic,
        platform=req.platform or "tiktok",
        api_key=req.api_key
    )
    return res


@app.post("/api/ai/chat")
def api_ai_chat(req: AIChatRequest):
    """Trợ lý sáng tạo AI đối thoại đa lượt."""
    if req.message and not req.messages:
        msgs = [{"role": "user", "content": req.message}]
    else:
        msgs = req.messages or []
    res = engine.ai_chat_completion(
        messages=msgs,
        api_key=req.api_key
    )
    return res


# ─────────────────────────────────────────────────────────── TRỤ CỘT 2: CREATIVE RE-UP STUDIO API
@app.post("/api/reup/process")
def api_reup_process(req: ReupProcessRequest):
    """Xử lý tái tạo và lách bản quyền video."""
    options = {
        "flip_h": req.flip_h,
        "speed": req.speed,
        "zoom": req.zoom,
        "blur_canvas_916": req.blur_canvas_916,
        "watermark_text": req.watermark_text,
        "strip_metadata": req.strip_metadata,
        "cut_start": req.cut_start,
        "cut_end": req.cut_end,
    }
    res = engine.process_reup_media(req.filename, options)
    if res.get("ok"):
        broadcast_sync({
            "type": "reup_completed",
            "filename": res.get("filename"),
            "size_str": res.get("size_str"),
            "message": res.get("message")
        })
    return res


# ─────────────────────────────────────────────────────────── TÌM KIẾM Ý TƯỞNG & GOOGLE / INTERNET API
@app.get("/api/ideas/suggestions")
def api_ideas_suggestions(q: str = "", lang: str = "vi"):
    """Gợi ý từ khóa tìm kiếm Google Autocomplete theo thời gian thực."""
    suggestions = engine.fetch_google_suggestions(q, lang=lang)
    return {"ok": True, "query": q, "suggestions": suggestions}


@app.get("/api/ideas/search")
def api_ideas_search(q: str = "", limit: int = 12):
    """Tìm kiếm video/audio trên Internet & YouTube dựa trên từ khóa."""
    if not q.strip():
        return {"ok": True, "results": [], "count": 0}
    results = engine.search_internet_videos(q, limit=limit)
    return {"ok": True, "query": q, "results": results, "count": len(results)}


@app.get("/api/ideas/trending")
def api_ideas_trending():
    """Lấy danh sách các danh mục xu hướng và ý tưởng video hot."""
    presets = engine.get_trending_presets()
    return {"ok": True, "presets": presets}


@app.get("/api/ideas/prompts")
def api_ideas_prompts(topic: str = "làm video triệu view"):
    """Tạo câu Hook mở đầu, kịch bản mẫu và bộ hashtag cho chủ đề video."""
    prompts = engine.generate_creative_prompts(topic)
    return {"ok": True, "prompts": prompts}


# ─────────────────────────────────────────────────────────── CÀI ĐẶT & HỆ THỐNG API
@app.get("/api/settings")
def api_get_settings():
    """Lấy cấu hình hiện tại."""
    return {"ok": True, "settings": engine.load_settings()}


@app.post("/api/settings")
def api_update_settings(req: SettingsRequest):
    """Cập nhật cấu hình."""
    cfg = engine.load_settings()
    cfg.update(req.settings)
    ok = engine.save_settings(cfg)
    return {"ok": ok, "settings": cfg}


@app.post("/api/system/ffmpeg/download")
def api_download_ffmpeg():
    """Khởi chạy tải FFmpeg Portable vào bin/ với WebSocket broadcast."""
    def worker():
        def on_prog(pct, msg):
            broadcast_sync({
                "type": "ffmpeg_download_progress",
                "percent": pct,
                "message": msg
            })
        ok, res = engine.download_portable_ffmpeg(progress_cb=on_prog)
        broadcast_sync({
            "type": "ffmpeg_download_completed",
            "ok": ok,
            "message": "FFmpeg đã cài đặt thành công!" if ok else res
        })

    th = threading.Thread(target=worker, daemon=True)
    th.start()
    return {"ok": True, "message": "Đã bắt đầu tiến trình tải FFmpeg."}


@app.post("/api/system/ytdlp/update")
def api_update_ytdlp():
    """Cập nhật engine yt-dlp lên bản mới nhất."""
    ok, msg = engine.update_ytdlp()
    return {"ok": ok, "message": msg}


@app.post("/api/system/tunnel/start")
def api_start_tunnel():
    """Khởi chạy Cloudflare Tunnel để tạo public link."""
    cfg = engine.load_settings()
    port = int(cfg.get("server_port", 5000))
    ok, url_or_err = engine.start_public_tunnel(port=port)
    if ok:
        broadcast_sync({
            "type": "tunnel_status",
            "active": True,
            "public_url": url_or_err
        })
        return {"ok": True, "public_url": url_or_err}
    return {"ok": False, "error": url_or_err}


@app.post("/api/system/tunnel/stop")
def api_stop_tunnel():
    """Dừng Cloudflare Tunnel."""
    engine.stop_public_tunnel()
    broadcast_sync({
        "type": "tunnel_status",
        "active": False,
        "public_url": None
    })
    return {"ok": True, "message": "Đã dừng link công khai."}


# ─────────────────────────────────────────────────────────── WEBSOCKET ROUTE
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Gửi trạng thái ban đầu
        await websocket.send_text(json.dumps({
            "type": "init",
            "system": engine.get_system_info(),
            "time": time.time(),
        }, ensure_ascii=False))

        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                # Phản hồi ping/pong
                if msg.get("action") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "time": time.time()}))
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


# ─────────────────────────────────────────────────────────── PHỤC VỤ GIAO DIỆN WEB (STATIC)
WEB_DIR = os.path.join(ROOT_DIR, "web")
os.makedirs(WEB_DIR, exist_ok=True)
os.makedirs(os.path.join(WEB_DIR, "css"), exist_ok=True)
os.makedirs(os.path.join(WEB_DIR, "js"), exist_ok=True)

# Gắn thư mục tĩnh
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/favicon.ico")
def serve_favicon():
    return Response(status_code=204)


@app.get("/")
def serve_index():
    """Trả về trang web ứng dụng."""
    index_file = os.path.join(WEB_DIR, "index.html")
    if os.path.isfile(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Tool Tải Video PRO - Web Server Running</h1>")


def start_server(host: str = "0.0.0.0", port: int = 5000):
    """Khởi động máy chủ web uvicorn."""
    import uvicorn
    local_ip = engine.get_local_ip()
    print("=" * 65)
    print(f"  ★ TOOL TẢI VIDEO PRO MAX v{engine.VERSION}")
    print(f"  ★ Đã khởi động máy chủ Web thành công!")
    print(f"  ► Truy cập cục bộ (Máy này):   http://localhost:{port}")
    print(f"  ► Chia sẻ cho bạn bè (Mạng LAN): http://{local_ip}:{port}")
    print("=" * 65)
    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
    except (KeyboardInterrupt, SystemExit):
        print("\n[INFO] Đã dừng máy chủ an toàn.")
    except Exception as e:
        print(f"\n[LỖI] Máy chủ dừng lại: {e}")


if __name__ == "__main__":
    cfg = engine.load_settings()
    host = cfg.get("server_host", "0.0.0.0")
    env_port = os.environ.get("PORT")
    port = int(env_port) if env_port else int(cfg.get("server_port", 5000))
    start_server(host=host, port=port)
