@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "BORNA_SKIP_PAUSE=0"
if /I "%~1"=="--no-pause" set "BORNA_SKIP_PAUSE=1"
set "BORNA_BOOTSTRAP_CMD="

echo [Borna] Preparing Windows environment...
call :resolve_python
if errorlevel 1 goto :fail

if not exist ".venv\Scripts\python.exe" (
  echo [Borna] Creating virtual environment...
  call !BORNA_BOOTSTRAP_CMD! -m venv .venv
  if errorlevel 1 goto :fail
)

echo [Borna] Upgrading pip...
call ".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :fail

echo [Borna] Installing requirements...
call ".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :fail

if not exist ".env" (
  copy /Y ".env.example" ".env" >nul
  echo [Borna] Created .env from .env.example
)

echo [Borna] Environment is ready.
if "%BORNA_SKIP_PAUSE%"=="1" goto :end
pause
goto :end

:resolve_python
where py >nul 2>nul
if not errorlevel 1 (
  call :try_python_cmd "py -3.13"
  if not errorlevel 1 exit /b 0
  call :try_python_cmd "py -3.12"
  if not errorlevel 1 exit /b 0
  call :try_python_cmd "py -3.11"
  if not errorlevel 1 exit /b 0
  call :try_python_cmd "py -3"
  if not errorlevel 1 exit /b 0
)

where python >nul 2>nul
if not errorlevel 1 (
  call :try_python_cmd "python"
  if not errorlevel 1 exit /b 0
)

echo [Borna] Python 3.11+ was not found.
echo [Borna] Install Python 3.11 or 3.12 and then run this file again.
echo [Borna] Recommended options during install:
echo [Borna]   - Add python.exe to PATH
echo [Borna]   - Install launcher for all users
echo [Borna] Download page: https://www.python.org/downloads/windows/
echo [Borna] If winget is available, you can try:
echo [Borna]   winget install Python.Python.3.12
exit /b 1

:try_python_cmd
call %~1 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
if errorlevel 1 exit /b 1
set "BORNA_BOOTSTRAP_CMD=%~1"
echo [Borna] Using Python runtime: %~1
exit /b 0

:fail
echo [Borna] Environment setup failed.
if "%BORNA_SKIP_PAUSE%"=="1" exit /b 1
pause
exit /b 1

:end
endlocal
