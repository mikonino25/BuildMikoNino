@echo off
REM Script chạy ứng dụng trên Windows

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting application...
python manga_downloader/main.py

pause


