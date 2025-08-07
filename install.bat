@echo off
setlocal EnableExtensions
REM -----------------------------------------------------------------------------
REM  HASHIRU_6_1 - Install script (idempotent)
REM  - Creates/activates venv
REM  - Upgrades pip
REM  - Installs requirements
REM  - Prints next step
REM -----------------------------------------------------------------------------

REM --- Fixed paths for this project ---
set "ROOT=C:\Users\marco\agente_gemini\HASHIRU_6_1"
set "VENV=%ROOT%\hashiru_6_env"

REM --- Create venv if missing ---
if not exist "%VENV%\Scripts\python.exe" (
  echo [INFO] Creating virtual environment...
  python -m venv "%VENV%"
  if errorlevel 1 (
    echo [ERROR] Failed to create venv. Ensure Python 3.12 is on PATH.
    exit /b 1
  )
)

REM --- Activate venv ---
call "%VENV%\Scripts\activate"
if errorlevel 1 (
  echo [ERROR] Failed to activate venv.
  exit /b 1
)

REM --- Upgrade pip ---
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
  echo [WARN] pip upgrade returned an error. Continuing...
)

REM --- Install requirements ---
if exist "%ROOT%\requirements.txt" (
  echo [INFO] Installing dependencies from requirements.txt ...
  pip install -r "%ROOT%\requirements.txt"
  if errorlevel 1 (
    echo [ERROR] pip install failed. Check output above.
    exit /b 1
  )
) else (
  echo [WARN] requirements.txt not found at %ROOT%.
)

echo.
echo [OK] Installed. To run: startup.bat
endlocal
