@echo off
setlocal EnableDelayedExpansion
title Kllama — Setup ^& Launch

REM ── UTF-8 console + Python UTF-8 mode ────────────────────────────────────────
REM    chcp 65001  : switches cmd.exe to UTF-8 so Python's print() never throws
REM                  UnicodeEncodeError on special characters.
REM    PYTHONUTF8  : forces Python I/O layer to use UTF-8 regardless of locale.
REM    PIP_DISABLE_PIP_VERSION_CHECK : suppresses pip's "[notice] new pip/package
REM                  available" messages that appear even with --quiet in pip 23+.
chcp 65001 > nul 2>&1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PIP_DISABLE_PIP_VERSION_CHECK=1

REM =============================================================================
REM  1Click-Kllama.bat  —  Kllama  |  Windows double-click launcher
REM
REM  USAGE
REM    Double-click this file from Windows Explorer.
REM    A terminal window will open showing setup progress, then the app
REM    will start and open automatically in your default browser.
REM
REM  WHAT IT DOES
REM    1. Checks that Python 3.10+ is on PATH
REM    2. Creates a Python virtual environment at .venv\  (first run only)
REM    3. Installs packages from requirements.txt         (first run only)
REM    4. On later runs: quickly verifies packages are present
REM    5. Launches Streamlit on http://localhost:8501
REM    6. Opens the app in your default browser
REM    7. Keeps this window open — press Ctrl+C to stop the server
REM
REM  ENVIRONMENT VARIABLES (all optional)
REM    STREAMLIT_PORT  — Port for the server  (default: 8501)
REM    RECREATE_VENV   — Set to 1 to delete and rebuild .venv
REM =============================================================================

REM ── Always run from the project root (parent of the scripts\ folder) ──────────
cd /d "%~dp0.."

REM ── Validate required project files are present ──────────────────────────────
if not exist "kllama.py" (
    echo.
    echo  [ERROR] kllama.py not found in the current directory.
    echo          Please run 1Click-Kllama.bat from inside the project folder.
    echo.
    goto :error
)
if not exist "requirements.txt" (
    echo.
    echo  [ERROR] requirements.txt not found in the current directory.
    echo          Please run 1Click-Kllama.bat from inside the project folder.
    echo.
    goto :error
)

REM ── Optional port override ───────────────────────────────────────────────────
if "%STREAMLIT_PORT%"=="" set STREAMLIT_PORT=8501

echo.
echo  +----------------------------------------------------------+
echo  ^|   🦙  Kllama  ^|  Windows Setup ^& Launcher               ^|
echo  +----------------------------------------------------------+
echo.

REM =============================================================================
REM  STEP 1 — Verify Python 3 is available
REM =============================================================================
echo  [1/4] Checking Python...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Python was not found on PATH.
    echo.
    echo          Install Python 3.10+ from:
    echo            https://www.python.org/downloads/
    echo.
    echo          During installation, make sure to tick:
    echo            "Add Python to PATH"
    echo.
    goto :error
)

for /f "delims=" %%v in ('python --version 2^>^&1') do (
    echo  [OK]    %%v found.
)

REM Enforce minimum version 3.10
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PY_VER=%%v
for /f "tokens=1,2 delims=." %%a in ("!PY_VER!") do (
    set PY_MAJOR=%%a
    set PY_MINOR=%%b
)
if !PY_MAJOR! LSS 3 (
    echo  [ERROR] Python 3.10 or newer is required. Found: !PY_VER!
    goto :error
)
if !PY_MAJOR! EQU 3 if !PY_MINOR! LSS 10 (
    echo  [ERROR] Python 3.10 or newer is required. Found: !PY_VER!
    echo          Download: https://www.python.org/downloads/
    goto :error
)

REM =============================================================================
REM  STEP 2 — Create or reuse virtual environment
REM =============================================================================
echo.
echo  [2/4] Setting up virtual environment...

REM Honour RECREATE_VENV=1 to force a clean rebuild
if "%RECREATE_VENV%"=="1" (
    if exist ".venv\" (
        echo  [WARN]  RECREATE_VENV=1 — removing existing .venv\ ...
        rmdir /s /q .venv
        echo  [OK]    Old environment removed.
    )
)

set FIRST_RUN=0
if not exist ".venv\Scripts\activate.bat" (
    echo  [SETUP] Creating virtual environment at .venv\ ...
    python -m venv --upgrade-deps .venv
    if !errorlevel! neq 0 (
        echo  [ERROR] Could not create the virtual environment.
        goto :error
    )
    echo  [OK]    Virtual environment created.
    set FIRST_RUN=1
) else (
    echo  [OK]    Existing virtual environment found at .venv\
)

REM Activate
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo  [ERROR] Could not activate the virtual environment.
    echo          Try deleting .venv\ and running 1Click-Kllama.bat again.
    goto :error
)
echo  [OK]    Virtual environment activated.

REM =============================================================================
REM  STEP 3 — Install / verify Python packages
REM =============================================================================
echo.
echo  [3/4] Installing / verifying packages...

if "!FIRST_RUN!"=="1" (
    REM First run: full verbose output so the user can see download progress
    echo  [SETUP] Upgrading pip...
    python -m pip install --quiet --upgrade pip --disable-pip-version-check
    echo.
    echo  [SETUP] Installing packages from requirements.txt
    echo          This may take 1-2 minutes on first run.
    echo.
    pip install --no-cache-dir -r requirements.txt --disable-pip-version-check
    if !errorlevel! neq 0 (
        echo.
        echo  [ERROR] Package installation failed.
        echo          Check your internet connection and try again.
        echo          To retry from scratch: set RECREATE_VENV=1 and run again.
        goto :error
    )
    echo.
    echo  [OK]    All packages installed successfully.
) else (
    REM Subsequent runs: upgrade pip silently, then verify packages
    python -m pip install --quiet --upgrade pip --disable-pip-version-check
    pip install --quiet --no-cache-dir -r requirements.txt --disable-pip-version-check
    if !errorlevel! neq 0 (
        echo  [ERROR] Package verification failed.
        echo          To repair your environment, run:
        echo              set RECREATE_VENV=1
        echo              1Click-Kllama.bat
        goto :error
    )
    echo  [OK]    Packages verified.
)

REM =============================================================================
REM  STEP 4 — Launch Streamlit
REM =============================================================================
echo.
echo  [4/4] Starting Kllama...

echo.
echo  +----------------------------------------------------------+
echo  ^|  App is starting at http://localhost:!STREAMLIT_PORT!
echo  ^|
echo  ^|  Your browser will open automatically in a few seconds.
echo  ^|  Press Ctrl+C here to stop the server.
echo  +----------------------------------------------------------+
echo.

call streamlit run kllama.py ^
    "--server.port=!STREAMLIT_PORT!" ^
    "--server.headless=false" ^
    "--browser.gatherUsageStats=false"

REM ── Server stopped (user pressed Ctrl+C or an error occurred) ────────────────
set STREAMLIT_EXIT=!errorlevel!
echo.
if !STREAMLIT_EXIT! neq 0 (
    echo  [WARN]  Streamlit stopped with an error - exit code: !STREAMLIT_EXIT!
    echo          Scroll up to see the error details.
    echo.
    echo  Common fixes:
    echo    - Port in use      :  set STREAMLIT_PORT=8502  and run again
    echo    - Broken packages  :  set RECREATE_VENV=1  and run again to rebuild
    echo    - Corrupted env    :  set RECREATE_VENV=1  and run again
    echo.
    pause
    exit /b !STREAMLIT_EXIT!
)
echo  Server stopped normally.
goto :done

REM =============================================================================
REM  Error handler — keeps the window open so the user can read the message
REM =============================================================================
:error
echo.
echo  ---------------------------------------------------------------
echo  Setup did not complete. See the error message above.
echo  ---------------------------------------------------------------
echo.
pause
exit /b 1

:done
echo  Press any key to close this window...
pause >nul
endlocal
