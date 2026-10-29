@echo off
setlocal
cd /d "%~dp02_models_code"
echo Dang chay so sanh 10 dataset tren 9 mo hinh (che do tiet kiem CPU: 4 luong)...
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
