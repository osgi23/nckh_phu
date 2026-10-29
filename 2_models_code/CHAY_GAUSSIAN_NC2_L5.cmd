@echo off
setlocal
cd /d "%~dp0"
echo Dang chay thu nghiem Gaussian (4 luong, tiet kiem CPU)...
if exist ".venv\Scripts\python.exe" (
  start /b /belownormal "" ".venv\Scripts\python.exe" -u run_gaussian_outliers.py --nc 2 --features 5 --jobs 4 %*
) else (
  start /b /belownormal "" python -u run_gaussian_outliers.py --nc 2 --features 5 --jobs 4 %*
)
if errorlevel 1 (
  pause
  exit /b 1
)
