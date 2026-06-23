@echo off
REM =========================================================================
REM  run_tests.bat -- One-click test runner for Kllama (Windows)
REM
REM  Usage:
REM    Double-click this file  -- runs all tests
REM    run_tests.bat --network -- kept for compatibility
REM    run_tests.bat --cov     -- adds coverage report
REM  =========================================================================
setlocal
cd /d "%~dp0.."

echo.
echo ========================================
echo  Kllama ^| Test Suite
echo ========================================
echo.

REM -- Resolve Python binary from virtual environment if present
set "PYTHON_BIN=python"
if exist ".venv\Scripts\python.exe" (
    echo [*] Using virtual environment .venv ...
    set "PYTHON_BIN=.venv\Scripts\python.exe"
) else if exist "venv\Scripts\python.exe" (
    echo [*] Using virtual environment venv ...
    set "PYTHON_BIN=venv\Scripts\python.exe"
) else (
    echo [!] No virtual environment found -- running with system Python.
    echo     For isolation: python -m venv .venv ^&^& .venv\Scripts\activate
    echo.
)

REM -- Install dev dependencies
echo [*] Installing developer dependencies (editable mode with dev extras) ...
%PYTHON_BIN% -m pip install -e .[dev] -q
if errorlevel 1 (
    echo.
    echo [ERROR] Dependency installation failed.
    pause
    exit /b 1
)
echo.

REM -- Resolve pytest arguments
set PYTEST_ARGS=--tb=short -v
set "COV_ARGS="

for %%A in (%*) do (
    if /I "%%A"=="--network" (
        echo [*] Network flag detected -- Kllama tests are offline-only, running normal suite.
        echo.
    )
    if /I "%%A"=="--cov" (
        echo [*] Installing pytest-cov for coverage reporting ...
        %PYTHON_BIN% -m pip install pytest-cov -q
        set "COV_ARGS=--cov=kllama --cov=kllama_core --cov-report=term-missing"
        echo [*] Coverage mode: terminal report enabled for kllama modules.
        echo.
    )
)

REM -- Run pytest
echo [*] Running tests ...
echo.
%PYTHON_BIN% -m pytest %PYTEST_ARGS% %COV_ARGS%
set EXIT_CODE=%ERRORLEVEL%

REM -- Summary
echo.
echo ========================================
if %EXIT_CODE% EQU 0 (
    echo  RESULT: ALL TESTS PASSED
) else (
    echo  RESULT: SOME TESTS FAILED
    echo  Review the output above for details.
)
echo ========================================
echo.

pause
exit /b %EXIT_CODE%
