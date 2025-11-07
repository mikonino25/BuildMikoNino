@echo off
REM Script để push project lên GitHub
REM Repository: mikonino25/BuildMikoNino

echo ========================================
echo Push Project to GitHub
echo ========================================
echo.

REM Kiểm tra git đã được cài đặt chưa
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git chua duoc cai dat!
    echo Vui long cai dat Git: https://git-scm.com/downloads
    pause
    exit /b 1
)

echo [1/5] Kiem tra git status...
git status
echo.

REM Kiểm tra xem đã có remote chưa
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo [2/5] Them remote origin...
    git remote add origin git@github.com:mikonino25/BuildMikoNino.git
    if errorlevel 1 (
        echo [WARNING] Khong the them remote, co the da ton tai
    )
) else (
    echo [2/5] Remote da ton tai
    git remote -v
)
echo.

echo [3/5] Add tat ca file...
git add .
if errorlevel 1 (
    echo [ERROR] Loi khi add file
    pause
    exit /b 1
)
echo.

echo [4/5] Commit changes...
set /p commit_msg="Nhap commit message (Enter de dung mac dinh): "
if "%commit_msg%"=="" set commit_msg=Update project
git commit -m "%commit_msg%"
if errorlevel 1 (
    echo [WARNING] Khong co thay doi de commit hoac da commit roi
)
echo.

echo [5/5] Push len GitHub...
git branch -M main
git push -u origin main
if errorlevel 1 (
    echo.
    echo [ERROR] Push that bai!
    echo.
    echo Co the do:
    echo - Chua cau hinh SSH key
    echo - Chua co quyen truy cap repository
    echo - Network error
    echo.
    echo Thu dung HTTPS thay vi SSH:
    echo   git remote set-url origin https://github.com/mikonino25/BuildMikoNino.git
    echo   git push -u origin main
) else (
    echo.
    echo ========================================
    echo [SUCCESS] Da push len GitHub thanh cong!
    echo ========================================
    echo.
    echo Repository: https://github.com/mikonino25/BuildMikoNino
)

echo.
pause

