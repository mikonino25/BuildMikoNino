# Hướng dẫn Upload Project lên GitHub

## Bước 1: Cài đặt Git (nếu chưa có)

1. Tải Git từ: https://git-scm.com/downloads
2. Cài đặt với các tùy chọn mặc định
3. Mở lại terminal/PowerShell sau khi cài đặt

## Bước 2: Cấu hình Git (lần đầu tiên)

```bash
git config --global user.name "mikonino25"
git config --global user.email "your-email@example.com"
```

## Bước 3: Khởi tạo Git Repository

Mở PowerShell hoặc Command Prompt trong thư mục project (`C:\Users\Administrator\Documents`) và chạy:

```bash
# Khởi tạo git repository
git init

# Thêm remote repository
git remote add origin git@github.com:mikonino25/BuildMikoNino.git
```

**Lưu ý:** Nếu chưa có SSH key, có thể dùng HTTPS:
```bash
git remote add origin https://github.com/mikonino25/BuildMikoNino.git
```

## Bước 4: Add và Commit files

```bash
# Add tất cả file (theo .gitignore)
git add .

# Commit với message
git commit -m "Initial commit: MikoNino Manga Downloader"
```

## Bước 5: Push lên GitHub

```bash
# Đổi branch sang main
git branch -M main

# Push lên GitHub
git push -u origin main
```

## Hoặc dùng Script tự động

### Windows:
Chạy file `push_to_github.bat`:
```bash
push_to_github.bat
```

### Linux/Mac:
Chạy file `push_to_github.sh`:
```bash
chmod +x push_to_github.sh
./push_to_github.sh
```

## Cấu hình SSH Key (khuyến nghị)

1. Tạo SSH key:
```bash
ssh-keygen -t ed25519 -C "your-email@example.com"
```

2. Copy public key:
```bash
cat ~/.ssh/id_ed25519.pub
```

3. Thêm vào GitHub:
   - Vào GitHub Settings > SSH and GPG keys
   - Click "New SSH key"
   - Paste public key và save

## Troubleshooting

### Lỗi: "Permission denied (publickey)"
- Chưa cấu hình SSH key → Dùng HTTPS thay vì SSH
- Hoặc cấu hình SSH key như hướng dẫn trên

### Lỗi: "Repository not found"
- Kiểm tra tên repository: `mikonino25/BuildMikoNino`
- Đảm bảo đã tạo repository trên GitHub trước
- Kiểm tra quyền truy cập

### Lỗi: "Large files"
- File quá lớn (>100MB) cần dùng Git LFS
- Hoặc thêm vào `.gitignore`

### Thay đổi từ HTTPS sang SSH:
```bash
git remote set-url origin git@github.com:mikonino25/BuildMikoNino.git
```

### Thay đổi từ SSH sang HTTPS:
```bash
git remote set-url origin https://github.com/mikonino25/BuildMikoNino.git
```

## Các lệnh Git hữu ích

```bash
# Xem trạng thái
git status

# Xem remote
git remote -v

# Xem log
git log --oneline

# Xem thay đổi
git diff

# Pull từ GitHub
git pull origin main

# Clone repository
git clone git@github.com:mikonino25/BuildMikoNino.git
```

## Files đã được ignore (không upload)

Theo `.gitignore`, các file sau sẽ KHÔNG được upload:
- `build/`, `dist/` - Build artifacts
- `__pycache__/` - Python cache
- `*.pyc`, `*.pyo` - Compiled Python
- `config.ini` - Config file (có thể thay đổi)
- `Downloads/` - Thư mục download
- `*.spec` - PyInstaller spec files
- `*.exe` - Executable files

## Files sẽ được upload

- `manga_downloader/` - Source code
- `modules/` - Lua modules
- `assets/` - Assets (icon, v.v.)
- `requirements.txt` - Dependencies
- `build_exe.py` - Build script
- `README.md` - Documentation
- `.gitignore` - Git ignore rules

## Sau khi push thành công

Repository sẽ có tại:
**https://github.com/mikonino25/BuildMikoNino**

Bạn có thể:
- Xem code online
- Clone về máy khác
- Tạo Issues và Pull Requests
- Cộng tác với người khác

