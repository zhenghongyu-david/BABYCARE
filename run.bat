@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import kivy, PIL, plyer" >nul 2>nul
    if not errorlevel 1 goto run
    echo Local environment is broken. Rebuilding...
    rmdir /s /q ".venv" >nul 2>nul
)

if not exist ".python313\python.exe" goto try_py

echo [1/2] Creating local Python environment...
".python313\python.exe" -m venv .venv
if errorlevel 1 goto failed
goto install

:try_py
py -3.13 -c "import sys" >nul 2>nul
if errorlevel 1 goto nopython
echo [1/2] Creating local Python environment...
py -3.13 -m venv .venv
if errorlevel 1 goto failed

:install
echo [2/2] Installing dependencies (first run may take a few minutes)...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto failed

:run
".venv\Scripts\python.exe" main.py
if errorlevel 1 goto failed
goto end

:nopython
echo.
echo Python 3.13 was not found.
echo Install Python 3.13 from https://www.python.org/downloads/
echo.
pause
goto end

:failed
echo.
echo Startup failed. Please send the error above to the developer.
echo.
pause

:end
endlocal
