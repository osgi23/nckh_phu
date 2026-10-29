@echo off
setlocal
cd /d "%~dp0"
echo Dang chay so sanh cac mo hinh (4 luong, tiet kiem CPU)...
if exist ".venv\Scripts\python.exe" (
    start /b /belownormal "" ".venv\Scripts\python.exe" -u run_visual_comparison.py --jobs 4 %*
) else (
    start /b /belownormal "" python -u run_visual_comparison.py --jobs 4 %*
)
if errorlevel 1 (
    echo Chay that bai. Xem thong bao loi phia tren.
    pause
    exit /b 1
)
