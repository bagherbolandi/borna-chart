@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "BORNA_LOCAL_ROOT=%LOCALAPPDATA%\BornaRuntime\borna-chart-windows-selfcontained-iis-kit-20260922"
echo [Borna] Source package: %CD%
echo [Borna] Local runtime folder: %BORNA_LOCAL_ROOT%
echo [Borna] Copying package to local disk...
robocopy "%CD%" "%BORNA_LOCAL_ROOT%" /MIR /XD .venv .git deliverables __pycache__ .pytest_cache .mypy_cache .ruff_cache /XF borna_chart.db *.pyc *.pyo >nul
if errorlevel 8 goto :fail
cd /d "%BORNA_LOCAL_ROOT%"
echo [Borna] Starting from local disk copy...
call "%BORNA_LOCAL_ROOT%\OPEN_ME_FIRST.bat"
exit /b %errorlevel%

:fail
echo [Borna] Copy to local disk failed.
echo [Borna] Try copying the extracted folder manually to C:\Borna or another local drive, then run OPEN_ME_FIRST.bat there.
pause
exit /b 1
