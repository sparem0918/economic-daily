@echo off
REM ============================================================
REM Economic Daily Newsletter - Windows Launcher
REM Python 3.11.9 required
REM All Korean messages are printed by Python (UTF-8)
REM ============================================================

chcp 65001 > nul
setlocal enabledelayedexpansion

cd /d "%~dp0"

set "VENV_DIR=.venv"
set "PY_LAUNCHER=py -3.11"
set "PYTHON_EXE=python"

REM --- Step 1: Check Python ---
echo.
echo [STEP 1/4] Checking Python installation...
%PY_LAUNCHER% --version >nul 2>&1
if errorlevel 1 (
    echo.
    %PYTHON_EXE% -c "print('[ERROR] Python 3.11 launcher not found.'); print('Please install Python 3.11.9 from https://www.python.org/downloads/release/python-3119/'); print('Make sure to check Add Python to PATH during installation.')" 2>nul
    if errorlevel 1 (
        echo [ERROR] Python 3.11 not found. Please install Python 3.11.9.
        echo Download: https://www.python.org/downloads/release/python-3119/
    )
    pause
    exit /b 1
)
%PY_LAUNCHER% --version

REM --- Step 2: Create virtual environment if missing ---
echo.
echo [STEP 2/4] Checking virtual environment...
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment in %VENV_DIR% ...
    %PY_LAUNCHER% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"

REM --- Step 3: Install / update dependencies ---
echo.
echo [STEP 3/4] Installing dependencies...
"%VENV_PY%" -m pip install --upgrade pip --quiet
"%VENV_PY%" -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

REM --- Step 4: Run the app ---
echo.
echo [STEP 4/4] Starting the news app...
echo.
"%VENV_PY%" app.py

if errorlevel 1 (
    echo.
    echo [ERROR] The app exited with an error.
    pause
)

endlocal
