@echo off
REM SuperEzio Dialog Cockpit - One-Click Launcher
echo [SuperEzio] Starting the complete trading system...
echo.

REM Get the directory of the batch file to ensure paths are correct
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo [SuperEzio] Checking and installing dependencies from requirements.txt...
pip install -r requirements.txt

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [SuperEzio] ERROR: Failed to install dependencies.
    echo Please ensure you have Python and pip installed and configured correctly.
    echo You may need to run this script as an administrator.
    pause
    exit /b 1
)

echo.
echo [SuperEzio] Dependencies are up to date.
echo [SuperEzio] Launching the Dialog Cockpit...
echo.

REM Run the main Python launcher script
python run_complete_system.py

echo.
echo [SuperEzio] System has been shut down.
pause
