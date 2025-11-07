#!/bin/bash
# Script chạy ứng dụng trên Linux/Mac

echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Starting application..."
python manga_downloader/main.py


