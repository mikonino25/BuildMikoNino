# MikoNino - Manga Downloader

Ứng dụng tải manga chuyên nghiệp với giao diện đẹp, đọc modules từ thư mục `modules/lua` để xác định cấu trúc web và tải manga.

![MikoNino](assets/Red-Eye-Anime.ico)

## Tính năng

- ✅ Giao diện đẹp với dark theme và màu sắc nhẹ nhàng
- ✅ Đọc modules Lua từ thư mục `modules/lua`
- ✅ Hỗ trợ nhiều trang web manga (HentaiFox, v.v.)
- ✅ Quản lý download queue với progress real-time
- ✅ Load links từ file TXT (hỗ trợ file lớn đến 100MB)
- ✅ Preview ảnh bìa với hover để phóng to
- ✅ Tự động lấy thông tin manga khi thêm URL
- ✅ Giữ code và modules bên ngoài để dễ cập nhật
- ✅ Build EXE với icon đẹp

## Cấu trúc thư mục

```
.
├── manga_downloader/          # Source code chính
│   ├── main.py                # Entry point
│   ├── core/                  # Core modules
│   │   ├── config_manager.py
│   │   ├── lua_module_loader.py
│   │   └── download_manager.py
│   └── gui/                   # GUI modules
│       └── main_window.py
├── modules/                   # Modules Lua (giữ bên ngoài)
│   └── lua/
│       ├── *.lua             # Các file module
│       └── metadata.json      # Metadata của modules
├── config.ini                 # File cấu hình
├── requirements.txt           # Python dependencies
├── build_exe.py              # Script build EXE
└── README.md                 # File này
```

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

Để tạo file EXE:

```bash
python build_exe.py
```

Script sẽ tự động:
- Kiểm tra và cài đặt PyInstaller nếu cần
- Include modules và config vào EXE
- Tạo file EXE trong thư mục `dist/`

**Lưu ý:**
- File EXE sẽ được tạo tại: `dist/MikoNino.exe`
- Modules và config được giữ bên ngoài EXE để dễ cập nhật
- Khi phân phối, copy thư mục `modules/` và `assets/` cùng với EXE

## Sử dụng

1. Mở ứng dụng
2. Nhập URL manga vào ô "Manga URL"
3. Click "Add" để thêm vào queue
4. Click "Start" để bắt đầu download
5. Xem tiến trình trong tab "Downloads"

## Cập nhật Modules

Để thêm hoặc cập nhật modules Lua:

1. Thêm file `.lua` mới vào thư mục `modules/lua/`
2. Cập nhật `metadata.json` nếu cần
3. Khởi động lại ứng dụng

Modules sẽ được tự động load khi ứng dụng khởi động.

## Cấu hình

Các cài đặt có thể thay đổi trong tab "Settings":
- Thư mục download
- Số lượng download đồng thời
- Các tùy chọn khác

## Phát triển

### Thêm module mới

1. Tạo file `.lua` trong `modules/lua/`
2. Implement các function:
   - `Register()` - Đăng ký module
   - `GetInfo()` - Lấy thông tin manga
   - `GetChapters()` - Lấy danh sách chapters
   - `GetPages()` - Lấy danh sách pages

3. Cập nhật `metadata.json`

### Cấu trúc Module Lua

Module Lua cần có cấu trúc tương tự HDoujin Downloader:

```lua
function Register()
    module.Name = 'Tên Module'
    module.Language = 'English'
    module.Domains.Add('example.com')
end

function GetInfo()
    info.Title = dom.SelectValue('//h1')
    -- ...
end

function GetChapters()
    -- ...
end

function GetPages()
    -- ...
end
```

## Giấy phép

Free Version - Sử dụng miễn phí

## Lưu ý

- Ứng dụng này là phiên bản đơn giản hóa
- Để thực thi đầy đủ các module Lua, cần implement Lua interpreter (có thể dùng lupa hoặc cách khác)
- Hiện tại chỉ parse thông tin cơ bản từ modules, chưa thực thi Lua script

## Tương lai

- [ ] Implement Lua interpreter để thực thi modules
- [ ] Hỗ trợ đầy đủ các API của HDoujin Downloader
- [ ] Thêm nhiều tính năng từ HDoujin Downloader
- [ ] Cải thiện UI/UX

"# BuildMikoNino" 
