@echo off
setlocal EnableExtensions
if /I "%BORNA_PORTABLE_LOCAL%"=="1" goto local_run
set "BORNA_PORTABLE_LOCAL=1"
set "BORNA_PORTABLE_DEST=%LOCALAPPDATA%\BornaPortable\borna-chart-windows-truly-portable-20260922"
echo [Borna Portable] Copying package to local runtime folder...
robocopy "%~dp0" "%BORNA_PORTABLE_DEST%" /MIR /XD .portable_runtime .git deliverables __pycache__ .pytest_cache .mypy_cache .ruff_cache /XF borna_chart.db *.pyc *.pyo >nul
if errorlevel 8 goto :fail
cd /d "%BORNA_PORTABLE_DEST%"
call "%BORNA_PORTABLE_DEST%\PORTABLE_RESET_AND_RUN_DEMO.bat"
exit /b %errorlevel%

:local_run
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0portable\bootstrap_portable_runtime.ps1" -ResetDb
exit /b %errorlevel%

:fail
echo [Borna Portable] Copy to local runtime folder failed.
pause
exit /b 1
