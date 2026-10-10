# 🚀 TOOL TẢI VIDEO PRO MAX v3.0.0 (ULTRA STUDIO EDITION)

> **Tác giả:** An Nguyễn  
> **Bản quyền:** © 2026 An Nguyễn — Bảo lưu mọi quyền  
> **Nền tảng hỗ trợ:** YouTube 4K, TikTok (No Watermark), Facebook Reels/Video, Instagram, Douyin HD, X (Twitter), Bilibili, Vimeo, Threads và hơn 1000 nền tảng trực tuyến.

---

## 🚀 HƯỚNG DẪN KHỞI CHẠY & SỬ DỤNG

### Cách 1: Khởi chạy Web Tool (Khuyên dùng nhất)
Nhấp đúp chuột vào tệp:
👉 **`start_web.bat`**

Hệ thống sẽ:
1. Tự động kiểm tra môi trường Python và cài đặt thư viện cần thiết.
2. Khởi động Web Server tại cổng `5000`.
3. Tự động mở trình duyệt web đến `http://localhost:5000`.
4. Hiển thị địa chỉ mạng LAN (ví dụ `http://192.168.1.74:5000`) cùng mã QR để bạn gửi cho bạn bè cùng dùng!

---

### Cách 2: Menu tổng hợp đa năng
Nhấp đúp chuột vào tệp **`start.bat`** để chọn chế độ:
- `[1]` Giao diện **WEB APP** (Khuyên dùng - Đẹp, Nhanh, Chia sẻ bạn bè).
- `[2]` Giao diện **Dòng lệnh (CLI Rich Console)**.
- `[3]` Giao diện **Đồ họa Cửa sổ (GUI PySide Desktop)**.
- `[4]` Tự động tải **FFmpeg Portable** vào `bin\`.
- `[5]` Cập nhật bộ thư viện mới nhất.

---

### Cách 3: Khởi chạy bằng lệnh Terminal
```bash
# Cài đặt thư viện phụ thuộc
py -m pip install -r requirements.txt

# Khởi chạy Web Server
py web_app.py

# Hoặc khởi chạy giao diện CLI truyền thống
py video_downloader.py

# Hoặc khởi chạy giao diện GUI Desktop
py gui_downloader.py
```

---

## 📱 HƯỚNG DẪN CHIA SẺ CHO BẠN BÈ

1. Đảm bảo máy tính của bạn và điện thoại/máy tính của bạn bè **đang kết nối cùng một mạng WiFi** (hoặc mở Điểm phát sóng di động Hotspot).
2. Chạy `start_web.bat`.
3. Chọn thẻ **"Mạng LAN & QR"** trên thanh điều hướng web.
4. Bảo bạn bè mở ứng dụng **Camera** trên điện thoại (iPhone hoặc Android) quét mã QR hiển thị trên màn hình, hoặc gõ địa chỉ IP được cấp (ví dụ: `http://192.168.1.74:5000`).
5. Bạn bè có thể dán link tải video và nhấn nút **"Tải về máy này"** để lưu video trực tiếp vào máy của họ!

---

## 🛠️ CẤU TRÚC THƯ MỤC DỰ ÁN

```text
Tool Downloads Video - Not Logo/
│
├── bin/                    # Thư mục chứa ffmpeg.exe & ffprobe.exe portable
├── downloads/              # Kho lưu trữ video & âm thanh tải về
├── web/                    # Giao diện Web Tool hiện đại (HTML5, CSS3, JS)
│   ├── index.html          # Trang chủ Web App Cyberpunk Glassmorphism
│   ├── css/style.css       # Hệ thống Design System & Stylesheet
│   └── js/app.js           # Controller WebSockets & REST API
├── engine.py               # Lõi xử lý tải đa luồng, FFmpeg & Toolbox tối ưu
├── web_app.py              # Máy chủ Web FastAPI, Streaming & WebSockets
├── video_downloader.py     # Giao diện CLI Rich Console
├── gui_downloader.py       # Giao diện GUI Desktop (PySide6)
├── requirements.txt        # Danh sách thư viện Python phụ thuộc
├── settings.json           # Tệp lưu trữ cấu hình người dùng
├── start_web.bat           # Trình khởi chạy 1-Click cho Web Tool
├── start.bat               # Trình khởi chạy tổng hợp đa năng
└── README.md               # Hướng dẫn sử dụng toàn diện
```

---

## ⚙️ CẤU HÌNH TÙY BIẾN (`settings.json`)

```json
{
  "default_quality": "best",
  "default_output": "downloads",
  "auto_open_folder": true,
  "merge_mp4": true,
  "embed_thumbnail": true,
  "add_metadata": true,
  "audio_bitrate": "192",
  "concurrent_fragments": 16,
  "check_updates": true,
  "server_port": 5000,
  "server_host": "0.0.0.0"
}
```

---
*© 2026 An Nguyễn — Chúc bạn và bạn bè có trải nghiệm tải video tuyệt vời!*
