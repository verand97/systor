@echo off
setlocal

:: Menangkap Argumen
set ARG1=%1
set ARG2=%2

if /I "%ARG1%"=="run" (
    if /I "%ARG2%"=="systor" (
        python "c:\Users\verand\dev\systor\monitor.py"
        goto :eof
    ) else if /I "%ARG2%"=="dev" (
        python "c:\Users\verand\dev\systor\monitor.py"
        goto :eof
    ) else if /I "%ARG2%"=="crypto" (
        python "c:\Users\verand\dev\systor\monitor.py"
        goto :eof
    ) else (
        echo.
        echo [Verand CLI] Error: Sub-perintah tidak dikenali.
        echo Gunakan: verand run systor
        echo.
        goto :eof
    )
) else if /I "%ARG1%"=="start" (
    python "c:\Users\verand\dev\systor\monitor.py"
    goto :eof
) else if /I "%ARG1%"=="help" (
    goto :show_help
) else (
    goto :show_help
)

:show_help
echo.
echo =======================================================
echo          V E R A N D   C L I   -   v1.0.0
echo =======================================================
echo Penggunaan: verand ^<command^> [options]
echo.
echo Available Commands (Perintah):
echo   run systor    : Membuka Menu Utama (System ^& Crypto)
echo   run crypto    : Membuka Menu Utama langsung
echo   run dev       : Membuka System Monitor mode Development
echo   start         : Alias cepat untuk menjalankan layanan utama
echo   help          : Menampilkan panduan baris perintah ini
echo.
echo Contoh Penggunaan:
echo   $ verand run systor
echo   $ verand start
echo =======================================================
