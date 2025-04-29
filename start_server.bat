@echo off
REM Resume Customizer Server Launcher (Windows Batch Script)

REM Change to the script's directory
cd /d "%~dp0"

REM Run the Python script
python start_server.py %*
