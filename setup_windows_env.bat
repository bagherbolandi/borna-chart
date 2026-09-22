@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "BORNA_SKIP_PAUSE=0"
if /I "%~1"=="--no-pause" set "BORNA_SKIP_PAUSE=1"

echo [Borna] Preparing Windows environment...

if not exist ".venv\Scripts\python.exe" (
  echo [Borna] Creating virtual environment...
  where py >nul 2>nul
  if not errorlevel 1 (
    py -3.11 -m venv .venv
  ) else (
    python -m venv .venv
  )
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

:fail
echo [Borna] Environment setup failed.
if "%BORNA_SKIP_PAUSE%"=="1" exit /b 1
pause
exit /b 1

:end
endlocal
