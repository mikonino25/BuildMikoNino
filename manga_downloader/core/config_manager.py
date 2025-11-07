#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config Manager - Quản lý cấu hình ứng dụng
"""

import os
import sys
import configparser
from pathlib import Path

class ConfigManager:
    def __init__(self):
        # Xác định thư mục gốc
        if getattr(sys, 'frozen', False):
            # Chạy từ EXE
            self.config_dir = Path(sys.executable).parent
        else:
            # Chạy từ source
            self.config_dir = Path(__file__).parent.parent.parent
            
        self.config_file = self.config_dir / "config.ini"
        self.download_dir = self.config_dir / "Downloads"
        
        # Đảm bảo thư mục download tồn tại
        self.download_dir.mkdir(exist_ok=True)
        
        self.config = configparser.ConfigParser()
        self.load_config()
        
    def load_config(self):
        """Tải cấu hình từ file"""
        if self.config_file.exists():
            self.config.read(self.config_file, encoding='utf-8')
        else:
            self.create_default_config()
            
    def create_default_config(self):
        """Tạo cấu hình mặc định"""
        if not self.config.has_section('Directories'):
            self.config.add_section('Directories')
        self.config.set('Directories', 'DownloadDirectory', str(self.download_dir))
        
        if not self.config.has_section('Queuing & Error Handling'):
            self.config.add_section('Queuing & Error Handling')
        self.config.set('Queuing & Error Handling', 'DownloadsMax', '10')
        self.config.set('Queuing & Error Handling', 'PageDelay', '0')
        self.config.set('Queuing & Error Handling', 'RetryFailed', '3')
        
        self.save_config()
        
    def save_config(self):
        """Lưu cấu hình vào file"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)
            
    def get(self, section, key, fallback=None):
        """Lấy giá trị cấu hình"""
        return self.config.get(section, key, fallback=fallback)
        
    def set(self, section, key, value):
        """Đặt giá trị cấu hình"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
        self.save_config()
        
    def get_download_directory(self):
        """Lấy thư mục download"""
        download_dir = self.get('Directories', 'DownloadDirectory', str(self.download_dir))
        return Path(download_dir)
        
    def set_download_directory(self, path):
        """Đặt thư mục download"""
        self.set('Directories', 'DownloadDirectory', str(path))

