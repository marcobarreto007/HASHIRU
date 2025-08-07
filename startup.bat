@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM -----------------------------------------------------------------------------
REM  HASHIRU_6_1 - Startup script
REM  - Ensures venv exists (creates if missing)
REM  - Activates venv
REM  - Installs requirements (idempotent)
REM  - Ensures .env exists (copies from .env.example if missing)
REM  - Reads HOST/PORT from .env (fallbacks to localhost:8080)
REM  - Launches Chainlit (prefer CLI; fallback to python -m)
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

REM --- Install requirements (idempotent) ---
if exist "%ROOT%\requirements.txt" (
  echo [INFO] Installing dependencies from requirements.txt ...
  pip install -r "%ROOT%\requirements.txt"
  if errorlevel 1 (
    echo [WARN] pip install returned an error. Check output above.
  )
) else (
  echo [WARN] requirements.txt not found at %ROOT%.
)

REM --- Ensure .env exists; if not, copy from example and open for editing ---
if not exist "%ROOT%\.env" (
  if exist "%ROOT%\.env.example" (
    copy /Y "%ROOT%\.env.example" "%ROOT%\.env" >nul
    echo [INFO] Created .env from .env.example. Opening for review...
    start notepad "%ROOT%\.env"
  ) else (
    echo [WARN] .env and .env.example not found. Proceeding with defaults.
  )
)

REM --- Defaults for HOST/PORT ---
set "HOST=localhost"
set "PORT=8080"

REM --- Read HOST/PORT from .env if present (simple parser) ---
if exist "%ROOT%\.env" (
  for /f "usebackq tokens=1,* delims==" %%A in ("%ROOT%\.env") do (
    set "k=%%A"
    set "v=%%B"
    if /i "!k!"=="HOST" set "HOST=!v!"
    if /i "!k!"=="PORT" set "PORT=!v!"
  )
  REM strip optional quotes and spaces
  for /f "tokens=* delims= " %%H in ("!HOST!") do set "HOST=%%~H"
  for /f "tokens=* delims= " %%P in ("!PORT!") do set "PORT=%%~P"
  set "HOST=!HOST:"=!"
  set "PORT=!PORT:"=!"
)

REM --- Move to project root ---
cd /d "%ROOT%"

REM --- Launch Chainlit (prefer CLI, fallback to python -m) ---
where chainlit >nul 2>nul
if %errorlevel%==0 (
  echo [INFO] Starting Chainlit via CLI on !HOST!:!PORT! ...
  chainlit run "%ROOT%\main_agent.py" --host !HOST! --port !PORT!
) else (
  echo [INFO] Starting Chainlit via python -m on !HOST!:!PORT! ...
  python -m chainlit run "%ROOT%\main_agent.py" --host !HOST! --port !PORT!
)

endlocal
