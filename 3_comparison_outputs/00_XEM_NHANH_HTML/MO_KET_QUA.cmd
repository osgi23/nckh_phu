@echo off
setlocal
if exist "%~dp000_XEM_KET_QUA.html" (
    start "" "%~dp000_XEM_KET_QUA.html"
) else if exist "%~dp0..\..\code\results\00_XEM_KET_QUA.html" (
    start "" "%~dp0..\..\code\results\00_XEM_KET_QUA.html"
) else (
    echo Chua tim thay trang ket qua HTML.
    pause
)
