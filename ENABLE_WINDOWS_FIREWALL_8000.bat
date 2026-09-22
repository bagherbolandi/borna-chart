@echo off
cd /d "%~dp0"
call "%~dp0deploy\windows\install_firewall_rule_8000.bat" 8000
