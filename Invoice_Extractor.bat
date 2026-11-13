@echo off
cd /d "%~dp0"
chcp 65001 >nul
title Invoice Extraction and GST Validation Bot - CA Automation
color 0B

echo ==============================================================================
echo                INVOICE EXTRACTION ^& GST VALIDATION BOT
echo                 Chartered Accountancy Automation Tool
echo ==============================================================================
echo [ADVISORY] Best results with digital PDFs (from ERPs, SAP, Tally, Zoho).
echo            Scanned/photo vouchers are flagged for manual verification.
echo ==============================================================================
echo.

:: 1. Check whether Python, py launcher, or direct AppData Python is available
set PYTHON_CMD=

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    goto :PYTHON_FOUND
)

py -3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py -3
    goto :PYTHON_FOUND
)

if exist "%LOCALAPPDATA%\Programs\Python\Python315\python.exe" (
    set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python315\python.exe"
    goto :PYTHON_FOUND
)

for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" (
        set PYTHON_CMD="%%D\python.exe"
        goto :PYTHON_FOUND
    )
)

:: If Python was not detected
echo [ERROR] Python is not installed or not added to your system PATH!
echo.
echo ==============================================================================
echo HOW TO SET UP PYTHON (ONE-TIME STEP):
echo 1. Download Python 3.10+ from: https://www.python.org/downloads/
echo 2. Run the installer and IMPORTANT:
echo    [x] Check the box: "Add python.exe to PATH" at the bottom!
echo 3. Disable Windows App Store alias:
echo    - Open Windows Settings -^> Apps -^> Advanced app settings -^> App execution aliases
echo    - Toggle OFF "App Installer (python.exe)" and "App Installer (python3.exe)"
echo ==============================================================================
echo.
pause
exit /b 1

:PYTHON_FOUND
echo [INFO] Python environment verified: %PYTHON_CMD%

:: 2. Check required dependencies
%PYTHON_CMD% -c "import pdfplumber, openpyxl, pandas, PIL" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Required Python libraries not detected!
    echo [INFO] Installing required dependencies from requirements.txt...
    %PYTHON_CMD% -m pip install -r "%~dp0requirements.txt"
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies. Please check your internet connection.
        pause
        exit /b 1
    )
)

:: 3. Automatically ensure project folders exist
if not exist "%~dp0input\invoices" mkdir "%~dp0input\invoices"
if not exist "%~dp0output" mkdir "%~dp0output"
if not exist "%~dp0processed" mkdir "%~dp0processed"
if not exist "%~dp0exceptions" mkdir "%~dp0exceptions"
if not exist "%~dp0logs" mkdir "%~dp0logs"
if not exist "%~dp0modules" mkdir "%~dp0modules"

:: 4. Run the main program
echo [INFO] Launching Invoice Extraction Engine...
echo.
%PYTHON_CMD% "%~dp0main.py"

echo.
echo ==============================================================================
echo Press any key to exit...
echo ==============================================================================
pause >nul
