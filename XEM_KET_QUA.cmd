@echo off
setlocal
echo Dang mo trang xem ket qua truc quan va danh gia cac mo hinh...
if exist "%~dp03_comparison_outputs\00_XEM_NHANH_HTML\00_XEM_KET_QUA.html" (
    start "" "%~dp03_comparison_outputs\00_XEM_NHANH_HTML\00_XEM_KET_QUA.html"
) else if exist "%~dp0code\results\00_XEM_KET_QUA.html" (
    start "" "%~dp0code\results\00_XEM_KET_QUA.html"
) else (
    echo Khong tim thay file ket qua HTML.
    pause
)
