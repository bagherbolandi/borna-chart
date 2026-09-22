@echo off
setlocal
set "BORNA_PORT=8000"
if not "%~1"=="" set "BORNA_PORT=%~1"
echo [Borna] Adding inbound firewall rule for TCP port %BORNA_PORT% ...
netsh advfirewall firewall add rule name="Borna API %BORNA_PORT%" dir=in action=allow protocol=TCP localport=%BORNA_PORT%
if errorlevel 1 (
  echo [Borna] Firewall rule creation failed. Run this file as Administrator.
  pause
  exit /b 1
)
echo [Borna] Firewall rule added.
pause
endlocal
