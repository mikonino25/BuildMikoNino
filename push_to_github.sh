#!/bin/bash
# Script để push project lên GitHub
# Repository: mikonino25/BuildMikoNino

echo "========================================"
echo "Push Project to GitHub"
echo "========================================"
echo ""

# Kiểm tra git đã được cài đặt chưa
if ! command -v git &> /dev/null; then
    echo "[ERROR] Git chưa được cài đặt!"
    echo "Vui lòng cài đặt Git: https://git-scm.com/downloads"
    exit 1
fi

echo "[1/5] Kiểm tra git status..."
git status
echo ""

# Kiểm tra xem đã có remote chưa
if ! git remote get-url origin &> /dev/null; then
    echo "[2/5] Thêm remote origin..."
    git remote add origin git@github.com:mikonino25/BuildMikoNino.git
    if [ $? -ne 0 ]; then
        echo "[WARNING] Không thể thêm remote, có thể đã tồn tại"
    fi
else
    echo "[2/5] Remote đã tồn tại"
    git remote -v
fi
echo ""

echo "[3/5] Add tất cả file..."
git add .
if [ $? -ne 0 ]; then
    echo "[ERROR] Lỗi khi add file"
    exit 1
fi
echo ""

echo "[4/5] Commit changes..."
read -p "Nhập commit message (Enter để dùng mặc định): " commit_msg
if [ -z "$commit_msg" ]; then
    commit_msg="Update project"
fi
git commit -m "$commit_msg"
if [ $? -ne 0 ]; then
    echo "[WARNING] Không có thay đổi để commit hoặc đã commit rồi"
fi
echo ""

echo "[5/5] Push lên GitHub..."
git branch -M main
git push -u origin main
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Push thất bại!"
    echo ""
    echo "Có thể do:"
    echo "- Chưa cấu hình SSH key"
    echo "- Chưa có quyền truy cập repository"
    echo "- Network error"
    echo ""
    echo "Thử dùng HTTPS thay vì SSH:"
    echo "  git remote set-url origin https://github.com/mikonino25/BuildMikoNino.git"
    echo "  git push -u origin main"
else
    echo ""
    echo "========================================"
    echo "[SUCCESS] Đã push lên GitHub thành công!"
    echo "========================================"
    echo ""
    echo "Repository: https://github.com/mikonino25/BuildMikoNino"
fi

echo ""

