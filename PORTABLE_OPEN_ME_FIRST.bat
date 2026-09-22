@echo off
setlocal EnableExtensions
if /I "%BORNA_PORTABLE_LOCAL%"=="1" goto local_run
set "BORNA_PORTABLE_LOCAL=1"
set "BORNA_PORTABLE_DEST=%LOCALAPPDATA%\BornaP24"
set "BORNA_COPY_LOG=%TEMP%\borna_portable_copy.log"
echo [Borna Portable] Source package: %CD%
echo [Borna Portable] Local runtime folder: %BORNA_PORTABLE_DEST%
echo [Borna Portable] Copying package to local runtime folder...
robocopy "%~dp0" "%BORNA_PORTABLE_DEST%" /E /R:1 /W:1 /NFL /NDL /NP /XD .portable_runtime .git deliverables __pycache__ .pytest_cache .mypy_cache .ruff_cache /XF borna_chart.db *.pyc *.pyo > "%BORNA_COPY_LOG%"
set "BORNA_COPY_RC=%ERRORLEVEL%"
if %BORNA_COPY_RC% GEQ 8 goto :fail
cd /d "%BORNA_PORTABLE_DEST%"
call "%BORNA_PORTABLE_DEST%\PORTABLE_OPEN_ME_FIRST.bat"
exit /b %errorlevel%

:local_run
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0portable\bootstrap_portable_runtime.ps1"
exit /b %errorlevel%

:fail
echo [Borna Portable] Copy to local runtime folder failed with robocopy exit code %BORNA_COPY_RC%.
echo [Borna Portable] Copy log: %BORNA_COPY_LOG%
if exist "%BORNA_COPY_LOG%" type "%BORNA_COPY_LOG%"
echo [Borna Portable] Workaround: open CMD in this folder and run:
echo   set BORNA_PORTABLE_LOCAL=1
echo   powershell -NoProfile -ExecutionPolicy Bypass -File portable\bootstrap_portable_runtime.ps1
pause
exit /b 1
