@echo off
REM Double-click this file to start the local server and open the site.
cd /d "%~dp0"
python serve.py %*
pause
