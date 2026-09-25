@echo off
setlocal
cd /d "%~dp0"
if not defined PORT set "PORT=5000"
set "STRUCTRA_BUNDLED_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if not exist ".venv\Scripts\python.exe" (
    where py >nul 2>&1
    if not errorlevel 1 (
        py -3 -m venv .venv
    ) else (
        where python >nul 2>&1
        if not errorlevel 1 (
            python -m venv .venv
        ) else (
            if exist "%STRUCTRA_BUNDLED_PYTHON%" (
                "%STRUCTRA_BUNDLED_PYTHON%" -m venv .venv
            ) else (
                goto setup_error
            )
        )
    )
    if errorlevel 1 goto setup_error
)

".venv\Scripts\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
    echo Structra needs Python 3.10 or newer. Install Python, then recreate .venv.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -c "import flask" >nul 2>&1
if errorlevel 1 (
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto setup_error
)

echo.
echo Structra is starting. Open http://127.0.0.1:%PORT% in your browser.
echo Keep this window open during your demo. Press Ctrl+C to stop.
echo.
".venv\Scripts\python.exe" app.py
if errorlevel 1 pause
exit /b

:setup_error
echo.
echo Setup could not finish. Check that Python 3.10 or newer is installed.
echo Internet access is needed once to install Flask. See README.md for manual steps.
pause
exit /b 1
