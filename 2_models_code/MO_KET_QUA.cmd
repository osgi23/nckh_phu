@echo off
setlocal
if exist "%~dp0results\00_XEM_KET_QUA.html" (
    start "" "%~dp0results\00_XEM_KET_QUA.html"
) else (
    echo Chua co trang ket qua. Hay chay CHAY_SO_SANH.cmd truoc.
    pause
)
