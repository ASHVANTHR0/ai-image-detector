@echo off
rem Starts the FastAPI backend (port 8765) and the Vue frontend (port 5173) in two windows.
rem Stop everything with stop.bat.
set ROOT=%~dp0
if not exist "%ROOT%venv\Scripts\python.exe" (
  echo Python environment not found. See README.md ^> Setup.
  pause
  exit /b 1
)
netstat -ano | findstr /r /c:":8765 .*LISTENING" >nul && (
  echo The app is already running. Opening it in the browser.
  echo Use stop.bat to stop it.
  start "" http://localhost:5173
  "%SystemRoot%\System32\timeout.exe" /t 4 >nul
  exit /b 0
)
if not exist "%ROOT%frontend\node_modules" (
  echo Installing frontend packages...
  pushd "%ROOT%frontend" && call npm install && popd
)
start "AI Detector - backend" cmd /k "cd /d %ROOT%backend && set HF_HUB_OFFLINE=1 && ..\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8765"
start "AI Detector - frontend" cmd /k "cd /d %ROOT%frontend && npm run dev"
echo Starting... the models take 10-20 seconds to load.
"%SystemRoot%\System32\timeout.exe" /t 8 /nobreak >nul
start "" http://localhost:5173
