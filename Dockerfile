# Sử dụng Python 3.11 Slim nền Linux Debian
FROM python:3.11-slim

# Thiết lập biến môi trường
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Cài đặt FFmpeg và các thư viện hệ thống cần thiết
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy requirements và cài đặt Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn vào container
COPY . .

# Tạo các thư mục cần thiết
RUN mkdir -p downloads bin

# Mở cổng mặc định
EXPOSE 5000

# Chạy ứng dụng FastAPI qua Uvicorn
CMD ["python", "web_app.py"]
