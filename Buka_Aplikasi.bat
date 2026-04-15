@echo off
setlocal enabledelayedexpansion

:: Set working directory to the folder where the script is located
cd /d "%~dp0"

:: Set window title
title Minilok DocGen Service - Portable Runner

:: Design Aesthetics (Header)
echo ===========================================================
echo            MINILOK DOCGEN - DOCUMENT GENERATOR
echo                    PORTABLE EDITION
echo ===========================================================
echo.

:: 1. Verify Virtual Environment
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual Environment (venv) tidak ditemukan!
    echo Pastikan Anda sudah menyalin seluruh isi folder aplikasi ke USB.
    echo Folder 'venv' sangat penting agar aplikasi bisa berjalan.
    echo.
    pause
    exit /b
)

:: 2. Verify .env File
if not exist ".env" (
    echo [PENTING] File .env tidak ditemukan!
    echo Aplikasi akan berjalan, tapi fitur AI Sumopod mungkin tidak aktif.
    echo.
)

:: 3. Check and free port 8000 if already used
echo [STEP 1] Menyiapkan environment... [OK]
echo [STEP 2] Memeriksa port 8000...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    echo [INFO] Port 8000 sedang dipakai, menutup proses lama ^(PID %%p^)...
    taskkill /PID %%p /F /T >nul 2>&1
)
timeout /t 1 /nobreak >nul
echo [STEP 3] Membuka Dashboard di Browser...

:: Launch browser after a short delay to ensure server is ready
:: This runs in the background
start /b cmd /c "timeout /t 3 /nobreak > nul && start http://localhost:8000/static/index.html"

echo [STEP 3] Menjalankan Server (FastAPI)...
echo.
echo -----------------------------------------------------------
echo API Aktif di: http://localhost:8000
echo UI Aktif di : http://localhost:8000/static/index.html
echo.
echo TIPS: Jangan tutup jendela hitam ini selama menggunakan aplikasi.
echo       Tutup jendela ini atau tekan CTRL+C untuk berhenti.
echo -----------------------------------------------------------
echo.

:: 4. Run the Application
venv\Scripts\python.exe main.py

:: If the app crashes or stops
echo.
echo Server telah berhenti.
pause
