@echo off
setlocal
set "BORNA_PORT=8000"
if not "%~1"=="" set "BORNA_PORT=%~1"
echo [Borna] Removing inbound firewall rule for TCP port %BORNA_PORT% ...
netsh advfirewall firewall delete rule name="Borna API %BORNA_PORT%"
echo [Borna] If the rule existed, it has been removed.
pause
endlocal
