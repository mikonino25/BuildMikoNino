# Hướng dẫn nhanh

## Chạy ứng dụng

### Cách 1: Chạy trực tiếp từ source

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Chạy ứng dụng
python manga_downloader/main.py
```

### Cách 2: Build thành EXE

```bash
# Cài đặt PyInstaller nếu chưa có
pip install pyinstaller

# Build EXE
python build_exe.py

# Chạy EXE từ thư mục dist/
```

## Cấu trúc khi chạy EXE

Khi build EXE, cấu trúc thư mục nên như sau:

```
MangaDownloader.exe
modules/
  lua/
    *.lua
    metadata.json
config.ini
```

**Quan trọng:** Modules và config được giữ bên ngoài EXE để dễ cập nhật!

## Sử dụng

1. **Thêm manga:**
   - Nhập URL vào ô "Manga URL"
   - Click "Add"

2. **Quản lý download:**
   - Click "Start" để bắt đầu
   - Click "Pause" để tạm dừng
   - Click "Remove" để xóa

3. **Cài đặt:**
   - Vào tab "Settings"
   - Chọn thư mục download
   - Đặt số lượng download đồng thời
   - Click "Save Settings"

## Cập nhật Modules

Để cập nhật hoặc thêm module mới:

1. Thêm file `.lua` vào `modules/lua/`
2. Cập nhật `metadata.json` (tùy chọn)
3. Khởi động lại ứng dụng

Không cần build lại EXE!

## Troubleshooting

### Lỗi: "Không tìm thấy module phù hợp"

- Kiểm tra xem URL có đúng định dạng không
- Kiểm tra xem có module trong `modules/lua/` hỗ trợ domain này không
- Thử thêm module mới nếu cần

### Lỗi: "Module không load được"

- Kiểm tra cú pháp file Lua
- Kiểm tra encoding (phải là UTF-8)
- Xem console/log để biết lỗi chi tiết

### EXE không chạy

- Đảm bảo có đầy đủ thư mục `modules/` và file `config.ini`
- Kiểm tra Windows Defender/Antivirus có block không
- Thử chạy với quyền Administrator

## Ghi chú

- Ứng dụng này là phiên bản đơn giản hóa
- Để thực thi đầy đủ Lua modules, cần implement Lua interpreter
- Hiện tại chỉ parse thông tin cơ bản từ modules


