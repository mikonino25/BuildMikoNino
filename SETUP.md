# Hướng dẫn Setup và Build

## Yêu cầu hệ thống

- Python 3.8 trở lên
- pip (Python package manager)
- Windows/Linux/Mac

## Cài đặt

### Bước 1: Clone/Download project

```bash
# Nếu dùng git
git clone <repository-url>
cd manga-downloader

# Hoặc download và giải nén
```

### Bước 2: Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### Bước 3: Kiểm tra cấu trúc thư mục

Đảm bảo có cấu trúc sau:

```
.
├── manga_downloader/
│   ├── main.py
│   ├── core/
│   └── gui/
├── modules/
│   └── lua/
│       ├── *.lua
│       └── metadata.json
├── config.ini (sẽ được tạo tự động)
├── requirements.txt
└── build_exe.py
```

## Chạy ứng dụng

### Cách 1: Chạy từ source (Development)

**Windows:**
```bash
run.bat
```

**Linux/Mac:**
```bash
chmod +x run.sh
./run.sh
```

**Hoặc trực tiếp:**
```bash
python manga_downloader/main.py
```

### Cách 2: Build thành EXE

**Bước 1: Cài đặt PyInstaller**
```bash
pip install pyinstaller
```

**Bước 2: Build EXE**
```bash
python build_exe.py
```

**Bước 3: Tìm file EXE**
File EXE sẽ ở: `dist/MangaDownloader.exe`

**Bước 4: Chuẩn bị để chạy EXE**

Khi chạy EXE, cần đảm bảo có cấu trúc:

```
MangaDownloader.exe
modules/
  lua/
    *.lua
    metadata.json
config.ini (sẽ được tạo tự động)
```

**Lưu ý quan trọng:**
- Modules và config được giữ BÊN NGOÀI EXE
- Có thể cập nhật modules mà không cần build lại
- Copy thư mục `modules/` cùng với EXE

## Cấu hình

### File config.ini

File này sẽ được tạo tự động khi chạy lần đầu. Có thể chỉnh sửa:

```ini
[Directories]
DownloadDirectory=C:\Downloads\Manga

[Queuing & Error Handling]
DownloadsMax=2
PageDelay=0
RetryFailed=3
```

### Thay đổi trong ứng dụng

1. Mở ứng dụng
2. Vào tab "Settings"
3. Thay đổi các tùy chọn
4. Click "Save Settings"

## Troubleshooting

### Lỗi import module

**Lỗi:** `ModuleNotFoundError: No module named 'core'`

**Giải pháp:**
- Đảm bảo đang chạy từ thư mục gốc của project
- Kiểm tra cấu trúc thư mục
- Thử: `python -m manga_downloader.main`

### Lỗi không tìm thấy modules

**Lỗi:** `modules/lua directory not found`

**Giải pháp:**
- Đảm bảo thư mục `modules/lua/` tồn tại
- Kiểm tra path trong code
- Khi chạy EXE, đảm bảo `modules/` cùng thư mục với EXE

### EXE không chạy

**Giải pháp:**
1. Kiểm tra Windows Defender/Antivirus
2. Chạy với quyền Administrator
3. Kiểm tra log/console để xem lỗi
4. Đảm bảo có đầy đủ `modules/` và `config.ini`

### Build EXE thất bại

**Lỗi:** `PyInstaller not found`

**Giải pháp:**
```bash
pip install pyinstaller
```

**Lỗi:** `Cannot find module`

**Giải pháp:**
- Kiểm tra `requirements.txt` đã cài đầy đủ
- Thử build với `--debug=all` để xem chi tiết

## Development

### Cấu trúc code

```
manga_downloader/
├── main.py              # Entry point
├── core/                # Core logic
│   ├── config_manager.py
│   ├── lua_module_loader.py
│   └── download_manager.py
└── gui/                 # GUI components
    └── main_window.py
```

### Thêm tính năng mới

1. Thêm code vào module tương ứng
2. Test với `python manga_downloader/main.py`
3. Build lại EXE nếu cần

### Debug

Để debug, chạy với console:

```bash
# Sửa build_exe.py: bỏ --windowed
python manga_downloader/main.py
```

Hoặc thêm print statements trong code.

## Notes

- Ứng dụng này là phiên bản đơn giản hóa
- Để thực thi đầy đủ Lua modules, cần implement Lua interpreter
- Hiện tại chỉ parse thông tin cơ bản từ modules
- Modules được giữ bên ngoài để dễ cập nhật


