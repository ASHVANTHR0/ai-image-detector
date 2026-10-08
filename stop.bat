@echo off
rem Stops the AI Image Detector: whatever is listening on the backend (8765) and frontend (5173) ports.
setlocal enabledelayedexpansion
set FOUND=0
for %%P in (8765 5173) do (
  for /f "tokens=5" %%I in ('netstat -ano ^| findstr /r /c:":%%P .*LISTENING"') do (
    if not "%%I"=="0" (
      echo Stopping process %%I on port %%P
      taskkill /PID %%I /T /F >nul 2>&1
      set FOUND=1
    )
  )
)
rem Close the windows opened by run.bat
taskkill /FI "WINDOWTITLE eq AI Detector - backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq AI Detector - frontend*" /T /F >nul 2>&1
if "!FOUND!"=="0" (echo The app was not running.) else (echo AI Image Detector stopped.)
"%SystemRoot%\System32\timeout.exe" /t 3 >nul
