@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if "%BORNA_HOST%"=="" set "BORNA_HOST=0.0.0.0"
if "%BORNA_PORT%"=="" set "BORNA_PORT=8000"
set "BORNA_RESET_DB=0"
set "BORNA_OPEN_BROWSER=1"
set "BORNA_LAN_MODE=0"

:parse_args
if "%~1"=="" goto args_done
if /I "%~1"=="--reset-db" (
  set "BORNA_RESET_DB=1"
  shift
  goto parse_args
)
if /I "%~1"=="--no-browser" (
  set "BORNA_OPEN_BROWSER=0"
  shift
  goto parse_args
)
if /I "%~1"=="--lan" (
  set "BORNA_LAN_MODE=1"
  set "BORNA_HOST=0.0.0.0"
  shift
  goto parse_args
)
shift
goto parse_args

:args_done
echo [Borna] Repository root: %CD%
call "%~dp0setup_windows_env.bat" --no-pause
if errorlevel 1 goto :fail

if "%BORNA_RESET_DB%"=="1" (
  if exist "borna_chart.db" del /Q "borna_chart.db"
  echo [Borna] Existing demo database removed.
)

echo [Borna] Local Console: http://localhost:%BORNA_PORT%/console
echo [Borna] Local Swagger: http://localhost:%BORNA_PORT%/docs
if "%BORNA_LAN_MODE%"=="1" call :show_lan_hints

if "%BORNA_OPEN_BROWSER%"=="1" start "" "http://localhost:%BORNA_PORT%/console"
call ".venv\Scripts\python.exe" -m uvicorn app.main:app --host %BORNA_HOST% --port %BORNA_PORT%
if errorlevel 1 goto :fail
goto :end

:show_lan_hints
set "BORNA_IP="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 ^| Where-Object { $_.IPAddress -notmatch '^127\.' -and $_.PrefixOrigin -ne 'WellKnown' } ^| Select-Object -ExpandProperty IPAddress -First 1)"`) do set "BORNA_IP=%%I"
if defined BORNA_IP (
  echo [Borna] LAN Console: http://%BORNA_IP%:%BORNA_PORT%/console
  echo [Borna] LAN Swagger: http://%BORNA_IP%:%BORNA_PORT%/docs
) else (
  echo [Borna] LAN mode enabled. If server IP is known, use http://SERVER-IP:%BORNA_PORT%/console
)
echo [Borna] If remote users cannot connect, open Windows Firewall for TCP port %BORNA_PORT%.
exit /b 0

:fail
echo [Borna] Startup failed.
pause
exit /b 1

:end
endlocal
