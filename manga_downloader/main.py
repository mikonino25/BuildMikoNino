#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manga Downloader - Ứng dụng tải manga với giao diện giống HDoujin Downloader
Đọc modules từ thư mục modules/lua để xác định cấu trúc web và tải
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import json
import threading
from pathlib import Path

# Xác định thư mục gốc của ứng dụng
if getattr(sys, 'frozen', False):
    # Chạy từ EXE (PyInstaller)
    BASE_DIR = Path(sys.executable).parent
else:
    # Chạy từ source
    BASE_DIR = Path(__file__).parent.parent

# Thêm thư mục gốc vào path để import các module
sys.path.insert(0, str(BASE_DIR / "manga_downloader"))

from gui.main_window import MainWindow
from core.config_manager import ConfigManager
from core.lua_module_loader import LuaModuleLoader
from core.download_manager import DownloadManager

class MangaDownloaderApp:
    def __init__(self):
        self.root = tk.Tk()
        self.config_manager = ConfigManager()
        self.lua_loader = LuaModuleLoader()
        
        # Tạo download manager (callback sẽ được set sau khi GUI tạo xong)
        self.download_manager = DownloadManager(self.config_manager, None)
        
        # Khởi tạo GUI
        self.main_window = MainWindow(
            self.root,
            self.config_manager,
            self.lua_loader,
            self.download_manager
        )
        
    def run(self):
        """Chạy ứng dụng"""
        self.root.mainloop()

if __name__ == "__main__":
    app = MangaDownloaderApp()
    app.run()

