#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build Script - Tạo file EXE từ source code
"""

import os
import sys
import subprocess
from pathlib import Path

def check_pyinstaller():
    """Kiểm tra PyInstaller đã được cài đặt chưa"""
    try:
        import PyInstaller
        return True
    except ImportError:
        return False

def build_exe():
    """Build ứng dụng thành file EXE"""
    
    # Kiểm tra PyInstaller
    if not check_pyinstaller():
        print("PyInstaller chưa được cài đặt!")
        print("Đang cài đặt PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("Đã cài đặt PyInstaller!")
    
    # Import sau khi đã cài đặt
    import PyInstaller.__main__
    
    # Thư mục gốc
    base_dir = Path(__file__).parent
    
    # Tên ứng dụng
    app_name = "MikoNino"
    
    # Xác định separator dựa trên OS
    sep = ';' if os.name == 'nt' else ':'
    
    # Các file và thư mục cần include
    datas = []
    
    # Thêm modules nếu tồn tại
    modules_path = base_dir / "modules"
    if modules_path.exists():
        datas.append((str(modules_path), "modules"))
        print(f"✓ Tìm thấy modules: {modules_path}")
    else:
        print(f"⚠ Không tìm thấy modules: {modules_path}")
    
    # Thêm assets folder nếu tồn tại (để có thể load icon khi chạy)
    assets_path = base_dir / "assets"
    if assets_path.exists():
        datas.append((str(assets_path), "assets"))
        print(f"✓ Tìm thấy assets: {assets_path}")
    
    # Thêm config.ini nếu tồn tại
    config_path = base_dir / "config.ini"
    if config_path.exists():
        datas.append((str(config_path), "."))
        print(f"✓ Tìm thấy config: {config_path}")
    
    # Thêm icon nếu tồn tại - đảm bảo icon được embed vào EXE
    icon_path = base_dir / "assets" / "Red-Eye-Anime.ico"
    icon_option = []
    if icon_path.exists():
        # Sử dụng đường dẫn tuyệt đối để đảm bảo PyInstaller tìm được
        icon_abs_path = icon_path.resolve()
        icon_option = [f'--icon={icon_abs_path}']
        print(f"✓ Tìm thấy icon: {icon_abs_path}")
        print(f"  Icon sẽ được embed vào EXE")
    else:
        print(f"⚠ Không tìm thấy icon: {icon_path}")
        print(f"  EXE sẽ không có icon riêng")
    
    # PyInstaller options
    options = [
        '--name=' + app_name,
        '--onefile',
        '--windowed',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=requests',
        '--hidden-import=bs4',
        '--hidden-import=lxml',
        '--collect-all=tkinter',
    ]
    
    # Thêm icon option
    options.extend(icon_option)
    
    # Thêm --add-data cho mỗi item
    for src, dst in datas:
        options.append(f'--add-data={src}{sep}{dst}')
    
    # Thêm file main
    main_file = base_dir / "manga_downloader" / "main.py"
    if not main_file.exists():
        print(f"✗ Không tìm thấy file main: {main_file}")
        sys.exit(1)
    
    options.append(str(main_file))
    
    print("\n" + "="*50)
    print("Đang build ứng dụng...")
    print("="*50)
    print(f"Thư mục gốc: {base_dir}")
    print(f"File main: {main_file}")
    print()
    
    try:
        # Chạy PyInstaller
        PyInstaller.__main__.run(options)
        
        exe_path = base_dir / 'dist' / f'{app_name}.exe'
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print("\n" + "="*50)
            print("✓ Build thành công!")
            print("="*50)
            print(f"File EXE: {exe_path}")
            print(f"Tên ứng dụng: {app_name}")
            print(f"Kích thước: {size_mb:.2f} MB")
            if icon_path.exists():
                print(f"Icon: {icon_path}")
            print("\nLưu ý:")
            print("- Modules và config được giữ bên ngoài EXE")
            print("- Copy thư mục 'modules' cùng với EXE khi phân phối")
        else:
            print("\n✗ Build thất bại: Không tìm thấy file EXE")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Lỗi khi build: {e}")
        print("\nGợi ý:")
        print("- Kiểm tra Python và dependencies đã cài đầy đủ")
        print("- Thử chạy với quyền Administrator")
        sys.exit(1)

if __name__ == "__main__":
    build_exe()

