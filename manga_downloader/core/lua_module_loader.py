#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lua Module Loader - Đọc và quản lý các module Lua từ modules/lua
"""

import os
import sys
import json
from pathlib import Path
from urllib.parse import urlparse

class LuaModuleLoader:
    def __init__(self):
        # Xác định thư mục gốc - thử nhiều vị trí
        self.base_dir = self._find_base_directory()
        self.modules_dir = self.base_dir / "modules" / "lua"
        self.metadata_file = self.modules_dir / "metadata.json"
        
        self.modules = {}
        self.metadata = {}
        
        # Kiểm tra và thông báo nếu không tìm thấy modules
        if not self.modules_dir.exists():
            print(f"⚠ Cảnh báo: Không tìm thấy thư mục modules tại: {self.modules_dir}")
            print(f"   Đang tìm kiếm ở các vị trí khác...")
            # Thử tìm ở các vị trí khác
            found_dir = self._find_modules_directory()
            if found_dir:
                self.modules_dir = found_dir
                self.base_dir = found_dir.parent.parent  # Update base_dir
        
        # Update metadata_file path sau khi đã tìm được modules_dir
        if self.modules_dir and self.modules_dir.exists():
            self.metadata_file = self.modules_dir / "metadata.json"
            print(f"✓ Tìm thấy modules tại: {self.modules_dir}")
            self.load_metadata()
            self.load_modules()
            print(f"✓ Đã load {len(self.modules)} modules")
        else:
            print(f"✗ Không tìm thấy thư mục modules!")
            print(f"   Vui lòng đảm bảo thư mục 'modules/lua/' tồn tại.")
            print(f"   Đã tìm tại: {self.modules_dir}")
    
    def _find_base_directory(self):
        """Tìm thư mục gốc của ứng dụng"""
        # Thử các vị trí theo thứ tự ưu tiên
        
        # 1. Nếu chạy từ EXE (PyInstaller)
        if getattr(sys, 'frozen', False):
            # Thư mục chứa EXE
            exe_dir = Path(sys.executable).parent
            if (exe_dir / "modules" / "lua").exists():
                return exe_dir
            
            # Thử _MEIPASS (PyInstaller temp folder)
            if hasattr(sys, '_MEIPASS'):
                meipass_dir = Path(sys._MEIPASS)
                if (meipass_dir / "modules" / "lua").exists():
                    return meipass_dir
                # Hoặc thư mục gốc của _MEIPASS
                meipass_parent = meipass_dir.parent
                if (meipass_parent / "modules" / "lua").exists():
                    return meipass_parent
            
            return exe_dir
        
        # 2. Chạy từ source
        # Thử thư mục chứa file này
        current_file_dir = Path(__file__).parent.parent.parent
        if (current_file_dir / "modules" / "lua").exists():
            return current_file_dir
        
        # Thử thư mục làm việc hiện tại
        cwd = Path.cwd()
        if (cwd / "modules" / "lua").exists():
            return cwd
        
        # Mặc định: thư mục chứa file này
        return current_file_dir
    
    def _find_modules_directory(self):
        """Tìm thư mục modules ở các vị trí khác"""
        search_paths = [
            # Thư mục EXE
            Path(sys.executable).parent / "modules" / "lua" if getattr(sys, 'frozen', False) else None,
            # Thư mục hiện tại
            Path.cwd() / "modules" / "lua",
            # Thư mục chứa script
            Path(__file__).parent.parent.parent / "modules" / "lua",
            # Thư mục user
            Path.home() / "Documents" / "MangaDownloader" / "modules" / "lua",
        ]
        
        for path in search_paths:
            if path and path.exists():
                print(f"✓ Tìm thấy modules tại: {path}")
                return path
        
        return None
        
    def load_metadata(self):
        """Tải metadata từ file JSON"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                print(f"Lỗi khi tải metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {}
            
    def load_modules(self):
        """Tải danh sách các module Lua"""
        if not self.modules_dir or not self.modules_dir.exists():
            print(f"✗ Không thể load modules: thư mục không tồn tại")
            return
        
        lua_files = list(self.modules_dir.glob("*.lua"))
        if not lua_files:
            print(f"⚠ Không tìm thấy file .lua nào trong {self.modules_dir}")
            return
        
        print(f"Đang load {len(lua_files)} module(s)...")
        loaded_count = 0
        
        for lua_file in lua_files:
            module_name = lua_file.stem
            try:
                with open(lua_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # Parse thông tin cơ bản từ file Lua
                module_info = self.parse_lua_module(content, module_name)
                if module_info:
                    self.modules[module_name] = {
                        'file': lua_file,
                        'content': content,
                        'info': module_info,
                        'metadata': self.metadata.get(f"{module_name}.lua", {})
                    }
                    loaded_count += 1
                    # Debug: in thông tin module đã load
                    domains = module_info.get('domains', [])
                    if domains:
                        print(f"  ✓ {module_name}: {len(domains)} domain(s) - {', '.join(domains[:3])}{'...' if len(domains) > 3 else ''}")
                    else:
                        print(f"  ⚠ {module_name}: Không tìm thấy domains!")
            except Exception as e:
                print(f"⚠ Lỗi khi tải module {module_name}: {e}")
        
        if loaded_count > 0:
            print(f"✓ Đã load thành công {loaded_count}/{len(lua_files)} modules")
        else:
            print(f"✗ Không load được module nào!")
                
    def parse_lua_module(self, content, module_name):
        """Parse thông tin cơ bản từ nội dung file Lua"""
        info = {
            'name': module_name,
            'domains': [],
            'language': 'Unknown'
        }
        
        # Tìm function Register()
        if 'function Register()' in content:
            lines = content.split('\n')
            in_register = False
            
            for line in lines:
                if 'function Register()' in line:
                    in_register = True
                    continue
                    
                if in_register:
                    if line.strip().startswith('end') and 'Register' not in line:
                        break
                        
                    # Parse module.Name
                    if 'module.Name' in line:
                        try:
                            name = line.split('=')[1].strip().strip("'\"")
                            info['name'] = name
                        except:
                            pass
                            
                    # Parse module.Language
                    if 'module.Language' in line:
                        try:
                            lang = line.split('=')[1].strip().strip("'\"")
                            info['language'] = lang
                        except:
                            pass
                            
                    # Parse module.Domains
                    # Hỗ trợ cả module.Domains.Add và module.Domains:Add
                    if 'module.Domains' in line and ('Add' in line or 'add' in line):
                        try:
                            # Format: module.Domains.Add('domain.com') hoặc module.Domains:Add('domain.com')
                            # Có thể có 2 tham số: module.Domains.Add('domain.com', 'Display Name')
                            # Chỉ lấy domain (tham số đầu tiên)
                            if "'" in line:
                                # Tìm text trong dấu nháy đơn
                                parts = line.split("'")
                                if len(parts) >= 2:
                                    domain = parts[1]
                                    if domain:
                                        info['domains'].append(domain)
                            elif '"' in line:
                                # Tìm text trong dấu nháy kép
                                parts = line.split('"')
                                if len(parts) >= 2:
                                    domain = parts[1]
                                    if domain:
                                        info['domains'].append(domain)
                        except Exception as e:
                            print(f"Lỗi parse domain từ dòng: {line.strip()[:50]}... - {e}")
                            pass
                            
        return info
        
    def find_module_for_url(self, url):
        """Tìm module phù hợp cho URL"""
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                print(f"⚠ URL không hợp lệ (không có netloc): {url}")
                return None
                
            domain = parsed.netloc.lower().replace('www.', '')
            print(f"🔍 Đang tìm module cho domain: {domain}")
            
            # Debug: in tất cả domains đã load
            if not self.modules:
                print("⚠ Không có modules nào được load!")
                return None
            
            # Tìm exact match trước
            for module_name, module_data in self.modules.items():
                module_domains = module_data['info'].get('domains', [])
                if not module_domains:
                    continue
                    
                for module_domain in module_domains:
                    module_domain_clean = module_domain.lower().replace('www.', '')
                    if domain == module_domain_clean:
                        print(f"✓ Tìm thấy module: {module_name} (exact match: {module_domain})")
                        return module_data
            
            # Tìm partial match (subdomain)
            for module_name, module_data in self.modules.items():
                module_domains = module_data['info'].get('domains', [])
                if not module_domains:
                    continue
                    
                for module_domain in module_domains:
                    module_domain_clean = module_domain.lower().replace('www.', '')
                    if domain.endswith('.' + module_domain_clean) or domain == module_domain_clean:
                        print(f"✓ Tìm thấy module: {module_name} (partial match: {module_domain})")
                        return module_data
            
            # Không tìm thấy
            print(f"✗ Không tìm thấy module cho domain: {domain}")
            print(f"  Các domains đã load:")
            for module_name, module_data in self.modules.items():
                domains = module_data['info'].get('domains', [])
                if domains:
                    print(f"    - {module_name}: {', '.join(domains)}")
                        
        except Exception as e:
            print(f"Lỗi khi tìm module cho URL {url}: {e}")
            import traceback
            traceback.print_exc()
            
        return None
        
    def get_all_modules(self):
        """Lấy danh sách tất cả các module"""
        return list(self.modules.values())
        
    def get_module(self, module_name):
        """Lấy module theo tên"""
        return self.modules.get(module_name)

