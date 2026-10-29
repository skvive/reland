@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".env" (
 copy /Y ".env.example" ".env" >nul
 echo Initial demo settings created: .env
 echo To enable Google login, edit GOOGLE_CLIENT_ID in .env and restart.
)
where py >nul 2>&1
if %ERRORLEVEL%==0 (set PY=py) else (set PY=python)
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
 echo [ERROR] Failed to install Python dependencies.
 pause
 exit /b 1
)
echo.
echo RE:LAND  http://127.0.0.1:8000
start "" http://127.0.0.1:8000
%PY% app.py
pause
