# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║   TOOL TẢI VIDEO PRO v4.0 MAX — GIAO DIỆN ĐỒ HOẠ (GUI)               ║
║   © Bản quyền: An Nguyễn • Thiết kế phong cách Modern Dark Theme     ║
╚══════════════════════════════════════════════════════════════════════╝
Cách chạy:
    py gui_downloader.py  (hoặc: python gui_downloader.py)
"""

import json
import os
import shutil
import subprocess
import sys
import time

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import QThread, Signal, Qt
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox,
        QCheckBox, QProgressBar, QFileDialog, QMessageBox, QGroupBox,
        QTabWidget, QSplitter
    )
except ImportError:
    try:
        from PyQt6 import QtCore, QtGui, QtWidgets
        from PyQt6.QtCore import QThread, pyqtSignal as Signal, Qt
        from PyQt6.QtWidgets import (
            QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
            QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox,
            QCheckBox, QProgressBar, QFileDialog, QMessageBox, QGroupBox,
            QTabWidget, QSplitter
        )
    except ImportError:
        print("[LỖI] Cần cài đặt PySide6 hoặc PyQt6 để chạy giao diện đồ hoạ!")
        print("Chạy lệnh: py -m pip install PySide6")
        sys.exit(1)

import video_downloader as core

DARK_STYLESHEET = """
QMainWindow {
    background-color: #0f172a;
}
QWidget {
    background-color: #0f172a;
    color: #e2e8f0;
    font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #334155;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 14px;
    font-weight: bold;
    color: #38bdf8;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background-color: #0f172a;
}
QLineEdit, QTextEdit, QComboBox {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    color: #f8fafc;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #38bdf8;
    background-color: #1e293b;
}
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QPushButton:pressed {
    background-color: #1e40af;
}
QPushButton#btnPrimary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #06b6d4, stop:1 #3b82f6);
    color: #ffffff;
    font-size: 15px;
    padding: 12px;
    border-radius: 8px;
}
QPushButton#btnPrimary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0891b2, stop:1 #2563eb);
}
QPushButton#btnSecondary {
    background-color: #334155;
    color: #f1f5f9;
}
QPushButton#btnSecondary:hover {
    background-color: #475569;
}
QPushButton#btnDanger {
    background-color: #dc2626;
    color: #ffffff;
}
QPushButton#btnDanger:hover {
    background-color: #b91c1c;
}
QProgressBar {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    text-align: center;
    color: #f8fafc;
    font-weight: bold;
    height: 22px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #06b6d4);
    border-radius: 5px;
}
QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #475569;
    border-radius: 4px;
    background-color: #1e293b;
}
QCheckBox::indicator:checked {
    background-color: #06b6d4;
    border: 1px solid #0891b2;
}
QScrollBar:vertical {
    background: #0f172a;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #334155;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #475569;
}
"""


class DownloadWorker(QThread):
    progress_signal = Signal(int, str, str)  # percent, speed, status_text
    log_signal = Signal(str)
    finished_signal = Signal(list)

    def __init__(self, urls, quality, audio, out_dir, ffmpeg_path, subs=None, audio_bitrate="192", is_playlist=False):
        super().__init__()
        self.urls = urls
        self.quality = quality
        self.audio = audio
        self.out_dir = out_dir
        self.ffmpeg_path = ffmpeg_path
        self.subs = subs
        self.audio_bitrate = audio_bitrate
        self.is_playlist = is_playlist
        self.is_canceled = False

    def run(self):
        results = []

        def hook(d):
            if self.is_canceled:
                raise KeyboardInterrupt("Đã hủy lượt tải.")
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes", 0)
                speed = d.get("speed") or 0
                percent = int(downloaded * 100 / total) if total > 0 else 0
                speed_str = f"{core.human_size(speed)}/s" if speed else "—"
                fname = os.path.basename(d.get("filename", ""))
                self.progress_signal.emit(percent, speed_str, f"Đang tải: {fname[:35]}...")
            elif d["status"] == "finished":
                self.progress_signal.emit(100, "Hoàn tất tải", "Đang xử lý sau khi tải...")

        def pp_hook(d):
            if d.get("status") == "started":
                pp = d.get("postprocessor", "")
                if pp == "ExtractAudio":
                    self.log_signal.emit("  ► Đang xuất tệp âm thanh MP3...")
                elif pp == "Merger":
                    self.log_signal.emit("  ► Đang chuẩn hóa tệp video sang MP4...")

        opts = core.build_ydl_opts(
            self.quality, self.audio, self.out_dir, self.ffmpeg_path,
            subs=self.subs, audio_bitrate=self.audio_bitrate,
            progress_hook=hook, pp_hook=pp_hook, is_playlist=self.is_playlist
        )

        try:
            from yt_dlp import YoutubeDL
            with YoutubeDL(opts) as ydl:
                for idx, url in enumerate(self.urls, 1):
                    if self.is_canceled:
                        break
                    self.log_signal.emit(f"\n[Mục {idx}/{len(self.urls)}] {url}")
                    t0 = time.time()
                    try:
                        self.log_signal.emit("  ► Đang phân tích thông tin video...")
                        inf = ydl.extract_info(url, download=True)
                        elapsed = time.time() - t0
                        video_id = inf.get("id", "")
                        fpath = core.find_result_file(self.out_dir, video_id)
                        fsize = os.path.getsize(fpath) if fpath and os.path.exists(fpath) else 0
                        results.append({
                            "title": inf.get("title", "?"),
                            "platform": str(inf.get("extractor_key", "?")).title(),
                            "size": fsize, "time": elapsed, "ok": True, "file": fpath
                        })
                        self.log_signal.emit(f"  [OK] Hoàn tất tải: {inf.get('title', '?')} ({core.human_size(fsize)})")
                    except Exception as e:
                        elapsed = time.time() - t0
                        err_msg = str(e).split("\n")[0][:100]
                        results.append({
                            "title": url, "platform": "—", "size": 0,
                            "time": elapsed, "ok": False, "file": err_msg
                        })
                        self.log_signal.emit(f"  [LỖI] {err_msg}")
        except Exception as ex:
            self.log_signal.emit(f"Lỗi phiên làm việc: {ex}")

        core.record_speeds(results)
        self.finished_signal.emit(results)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Tool Tải Video PRO v{core.VERSION} — An Nguyễn")
        self.resize(880, 680)
        self.setMinimumSize(780, 580)
        self.setStyleSheet(DARK_STYLESHEET)

        self.ffmpeg_path = core.find_ffmpeg()
        self.cfg = core.load_settings()
        self.worker = None

        self.setup_ui()
        self.update_ffmpeg_status()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(14)

        # Header Title Banner
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel(f"TOOL TẢI VIDEO PRO v{core.VERSION}")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #38bdf8;")
        subtitle = QLabel("Tải video Không Logo • YouTube • TikTok • Facebook • Instagram • Douyin • MP3 / MP4")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 12px;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        header.addStretch()

        # FFmpeg status badge
        self.ffmpeg_badge = QLabel()
        self.ffmpeg_badge.setStyleSheet("padding: 6px 12px; border-radius: 6px; font-weight: bold;")
        header.addWidget(self.ffmpeg_badge)

        self.btn_dl_ffmpeg = QPushButton("Tải FFmpeg")
        self.btn_dl_ffmpeg.setObjectName("btnSecondary")
        self.btn_dl_ffmpeg.clicked.connect(self.download_ffmpeg_action)
        self.btn_dl_ffmpeg.hide()
        header.addWidget(self.btn_dl_ffmpeg)

        main_layout.addLayout(header)

        # Input links section
        input_group = QGroupBox("1. DANH SÁCH LINK VIDEO")
        input_layout = QVBoxLayout(input_group)
        self.url_edit = QTextEdit()
        self.url_edit.setPlaceholderText("Dán 1 hoặc nhiều đường link vào đây (mỗi dòng 1 link hoặc cách nhau bằng dấu cách)...")
        self.url_edit.setMinimumHeight(85)
        input_layout.addWidget(self.url_edit)

        btn_row = QHBoxLayout()
        btn_paste_clip = QPushButton("📋 Dán từ Clipboard")
        btn_paste_clip.setObjectName("btnSecondary")
        btn_paste_clip.clicked.connect(self.paste_from_clipboard)
        btn_row.addWidget(btn_paste_clip)

        btn_load_file = QPushButton("📁 Đọc từ links.txt")
        btn_load_file.setObjectName("btnSecondary")
        btn_load_file.clicked.connect(self.load_from_file)
        btn_row.addWidget(btn_load_file)

        btn_clear = QPushButton("✖ Xóa trắng")
        btn_clear.setObjectName("btnSecondary")
        btn_clear.clicked.connect(lambda: self.url_edit.clear())
        btn_row.addWidget(btn_clear)
        btn_row.addStretch()

        input_layout.addLayout(btn_row)
        main_layout.addWidget(input_group)

        # Options Section (Format, Quality, Folder)
        opts_group = QGroupBox("2. TÙY CHỌN TẢI & CHẤT LƯỢNG")
        opts_layout = QVBoxLayout(opts_group)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Định dạng:"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Video (MP4)", "Chỉ lấy Âm thanh (MP3)"])
        self.combo_mode.currentIndexChanged.connect(self.on_mode_changed)
        row1.addWidget(self.combo_mode)

        self.lbl_quality = QLabel("Chất lượng:")
        row1.addWidget(self.lbl_quality)
        self.combo_quality = QComboBox()
        for code, label in core.QUALITIES:
            self.combo_quality.addItem(label, code)
        row1.addWidget(self.combo_quality)

        self.lbl_bitrate = QLabel("Bitrate MP3:")
        self.lbl_bitrate.hide()
        row1.addWidget(self.lbl_bitrate)
        self.combo_bitrate = QComboBox()
        for code, label in core.AUDIO_BITRATES:
            self.combo_bitrate.addItem(label, code)
        self.combo_bitrate.setCurrentIndex(1)
        self.combo_bitrate.hide()
        row1.addWidget(self.combo_bitrate)

        opts_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Thư mục lưu:"))
        self.edit_output = QLineEdit(os.path.abspath(self.cfg.get("default_output", "downloads")))
        row2.addWidget(self.edit_output)

        btn_browse = QPushButton("Chọn...")
        btn_browse.setObjectName("btnSecondary")
        btn_browse.clicked.connect(self.browse_folder)
        row2.addWidget(btn_browse)

        btn_open_folder = QPushButton("Mở thư mục")
        btn_open_folder.setObjectName("btnSecondary")
        btn_open_folder.clicked.connect(self.open_current_folder)
        row2.addWidget(btn_open_folder)

        opts_layout.addLayout(row2)

        # Advanced checkboxes
        row3 = QHBoxLayout()
        self.chk_merge_mp4 = QCheckBox("Tự động gộp chuẩn MP4 (Tương thích 100%)")
        self.chk_merge_mp4.setChecked(self.cfg.get("merge_mp4", True))
        row3.addWidget(self.chk_merge_mp4)

        self.chk_embed_thumb = QCheckBox("Nhúng ảnh bìa vào MP3")
        self.chk_embed_thumb.setChecked(self.cfg.get("embed_thumbnail", True))
        row3.addWidget(self.chk_embed_thumb)

        self.chk_playlist = QCheckBox("Tải toàn bộ Playlist (nếu phát hiện)")
        self.chk_playlist.setChecked(False)
        row3.addWidget(self.chk_playlist)
        row3.addStretch()

        opts_layout.addLayout(row3)
        main_layout.addWidget(opts_group)

        # Progress & Action Buttons
        act_row = QHBoxLayout()
        self.btn_download = QPushButton("▶ BẮT ĐẦU TẢI XUỐNG")
        self.btn_download.setObjectName("btnPrimary")
        self.btn_download.setMinimumHeight(44)
        self.btn_download.clicked.connect(self.start_download)
        act_row.addWidget(self.btn_download, 3)

        self.btn_cancel = QPushButton("Dừng / Hủy")
        self.btn_cancel.setObjectName("btnDanger")
        self.btn_cancel.setMinimumHeight(44)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_download)
        act_row.addWidget(self.btn_cancel, 1)

        main_layout.addLayout(act_row)

        # Progress Bar & Status Text
        prog_box = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        prog_box.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Sẵn sàng.")
        self.lbl_status.setStyleSheet("color: #94a3b8; font-size: 12px;")
        prog_box.addWidget(self.lbl_status)
        main_layout.addLayout(prog_box)

        # Real-time Log Box
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #0b1120; border: 1px solid #1e293b; font-family: Consolas, monospace; font-size: 12px;")
        main_layout.addWidget(self.log_text)

    def update_ffmpeg_status(self):
        self.ffmpeg_path = core.find_ffmpeg()
        if self.ffmpeg_path:
            self.ffmpeg_badge.setText("● FFmpeg Sẵn Sàng")
            self.ffmpeg_badge.setStyleSheet("background-color: #065f46; color: #34d399; padding: 6px 12px; border-radius: 6px; font-weight: bold;")
            self.btn_dl_ffmpeg.hide()
        else:
            self.ffmpeg_badge.setText("● Thiếu FFmpeg")
            self.ffmpeg_badge.setStyleSheet("background-color: #7f1d1d; color: #f87171; padding: 6px 12px; border-radius: 6px; font-weight: bold;")
            self.btn_dl_ffmpeg.show()

    def download_ffmpeg_action(self):
        reply = QMessageBox.question(
            self, "Tải FFmpeg Portable",
            "Bạn có muốn tự động tải FFmpeg Portable vào thư mục `bin/` không?\nQuá trình này không cần quyền Admin.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.log_text.append("[HỆ THỐNG] Đang tải FFmpeg Portable...")
            self.lbl_status.setText("Đang tải FFmpeg Essentials...")
            QApplication.processEvents()
            res = core.download_portable_ffmpeg()
            if res:
                self.update_ffmpeg_status()
                QMessageBox.information(self, "Thành công", "Đã tải và cài đặt FFmpeg thành công!")
            else:
                QMessageBox.warning(self, "Thất bại", "Không thể tải FFmpeg. Vui lòng kiểm tra kết nối mạng.")

    def on_mode_changed(self, idx):
        is_audio = (idx == 1)
        self.lbl_quality.setVisible(not is_audio)
        self.combo_quality.setVisible(not is_audio)
        self.lbl_bitrate.setVisible(is_audio)
        self.combo_bitrate.setVisible(is_audio)

    def paste_from_clipboard(self):
        urls = core.load_urls_from_clipboard()
        if urls:
            current = self.url_edit.toPlainText().strip()
            joined = "\n".join(urls)
            self.url_edit.setPlainText(f"{current}\n{joined}".strip())
            self.log_text.append(f"[CLIPBOARD] Đã dán {len(urls)} link.")
        else:
            QMessageBox.information(self, "Thông báo", "Không tìm thấy liên kết hợp lệ trong Clipboard!")

    def load_from_file(self):
        urls = core.load_urls_from_file("links.txt")
        if urls:
            self.url_edit.setPlainText("\n".join(urls))
            self.log_text.append(f"[TẬP TIN] Đã nạp {len(urls)} link từ links.txt.")
        else:
            QMessageBox.information(self, "Thông báo", "File links.txt chưa có đường link nào!")

    def browse_folder(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu file", self.edit_output.text())
        if dir_path:
            self.edit_output.setText(dir_path)

    def open_current_folder(self):
        out_dir = self.edit_output.text()
        os.makedirs(out_dir, exist_ok=True)
        try:
            subprocess.Popen(f'explorer "{out_dir}"')
        except Exception:
            pass

    def start_download(self):
        raw = self.url_edit.toPlainText()
        urls = core.parse_urls_from_text(raw)
        if not urls:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập ít nhất một đường link video hợp lệ!")
            return

        is_audio = (self.combo_mode.currentIndex() == 1)
        quality = self.combo_quality.currentData()
        bitrate = self.combo_bitrate.currentData()
        out_dir = self.edit_output.text()
        is_playlist = self.chk_playlist.isChecked()

        self.btn_download.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_text.append(f"\n[BẮT ĐẦU] Chuẩn bị tải {len(urls)} liên kết...")

        self.worker = DownloadWorker(
            urls=urls, quality=quality, audio=is_audio, out_dir=out_dir,
            ffmpeg_path=self.ffmpeg_path, audio_bitrate=bitrate,
            is_playlist=is_playlist
        )
        self.worker.progress_signal.connect(self.on_worker_progress)
        self.worker.log_signal.connect(self.on_worker_log)
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.start()

    def cancel_download(self):
        if self.worker and self.worker.isRunning():
            self.worker.is_canceled = True
            self.log_text.append("[HỦY] Đang dừng tiến trình tải...")
            self.btn_cancel.setEnabled(False)

    def on_worker_progress(self, percent, speed, status):
        self.progress_bar.setValue(percent)
        self.lbl_status.setText(f"{status} | Tốc độ: {speed}")

    def on_worker_log(self, text):
        self.log_text.append(text)
        sb = self.log_text.verticalScrollBar()
        sb.setValue(sb.maximum())

    def on_worker_finished(self, results):
        self.btn_download.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setValue(100)
        self.lbl_status.setText("Tất cả đã hoàn tất!")

        ok_count = sum(1 for r in results if r.get("ok"))
        total = len(results)
        self.log_text.append(f"\n[KẾT THÚC] Thành công: {ok_count}/{total} mục.")

        out_dir = self.edit_output.text()
        if self.cfg.get("auto_open_folder", True):
            core.open_result_folder(results, out_dir)

        QMessageBox.information(
            self, "Hoàn tất",
            f"Đã hoàn thành lượt tải!\n• Thành công: {ok_count}/{total} mục\n• Thư mục: {out_dir}"
        )


def run():
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
