# Manga Downloader - Tiếng Việt

Ứng dụng tải manga với giao diện giống HDoujin Downloader, đọc modules từ thư mục `modules/lua` để xác định cấu trúc web và tải manga.

## Tính năng

- ✅ Giao diện giống HDoujin Downloader
- ✅ Đọc modules Lua từ thư mục `modules/lua`
- ✅ Hỗ trợ nhiều trang web manga
- ✅ Quản lý download queue
- ✅ Giữ code và modules bên ngoài để dễ cập nhật
- ✅ Build EXE không giải nén khi chạy

## Cài đặt

### Yêu cầu

- Python 3.8 trở lên
- pip

### Các bước

1. Clone hoặc tải project về
2. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

3. Chạy ứng dụng:
```bash
python manga_downloader/main.py
```

## Build EXE

### Build EXE không giải nén (Khuyến nghị)

**Windows:**
```bash
build_exe_simple.bat
```

Chọn option **1** (Nuitka)

**Ưu điểm:**
- ✅ Không giải nén file tạm khi chạy
- ✅ Native code, chạy nhanh
- ✅ Một file EXE duy nhất
- ✅ Modules được embed trong EXE

**Kết quả:**
- File EXE: `dist/MangaDownloader.exe`
- Có thể copy đi bất kỳ đâu và chạy trực tiếp
- Không cần Python hoặc dependencies

### Build với PyInstaller

```bash
python build_exe.py
```

**Lưu ý:** PyInstaller vẫn giải nén tạm vào temp folder khi chạy.

Xem chi tiết trong [BUILD.md](BUILD.md)

## Sử dụng

1. Mở ứng dụng
2. Nhập URL manga vào ô "Manga URL"
3. Click "Add" để thêm vào queue
4. Click "Start" để bắt đầu download
5. Xem tiến trình trong tab "Downloads"

## Cập nhật Modules

Với EXE từ Nuitka:
- Modules được embed trong EXE
- Cần build lại để cập nhật modules

Với EXE từ PyInstaller:
- Có thể cập nhật modules trong thư mục `modules/` bên ngoài
- Không cần build lại

## Cấu hình

Các cài đặt có thể thay đổi trong tab "Settings":
- Thư mục download
- Số lượng download đồng thời
- Các tùy chọn khác

## Cấu trúc thư mục

```
.
├── manga_downloader/          # Source code chính
│   ├── main.py                # Entry point
│   ├── core/                  # Core modules
│   └── gui/                   # GUI modules
├── modules/                   # Modules Lua
│   └── lua/
│       ├── *.lua             # Các file module
│       └── metadata.json      # Metadata
├── config.ini                 # File cấu hình
├── build_exe_standalone.py    # Script build EXE (Nuitka)
├── build_exe.py               # Script build EXE (PyInstaller)
├── build_exe_simple.bat       # Script build đơn giản (Windows)
└── requirements.txt           # Dependencies
```

## Troubleshooting

### EXE không chạy

- Kiểm tra Windows Defender/Antivirus
- Chạy với quyền Administrator
- Kiểm tra log để xem lỗi

### Build thất bại

**Nuitka:**
- Cài Visual Studio Build Tools (Windows)
- Hoặc `build-essential` (Linux)

**PyInstaller:**
- Kiểm tra `pip install pyinstaller`
- Xem log để biết lỗi chi tiết

## Lưu ý

- Ứng dụng này là phiên bản đơn giản hóa
- Để thực thi đầy đủ các module Lua, cần implement Lua interpreter
- Hiện tại chỉ parse thông tin cơ bản từ modules

## Giấy phép

Free Version - Sử dụng miễn phí


