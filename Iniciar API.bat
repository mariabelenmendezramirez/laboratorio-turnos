@echo off
setlocal
cd /d "%~dp0backend"

rem Avoid starting a second copy when the API is already responding.
powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8000/api/state' -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"
if not errorlevel 1 (
  echo La API ya esta activa en http://localhost:8000/api/state
  pause
  exit /b 0
)

set "PYTHON_CMD="
where py >nul 2>nul && set "PYTHON_CMD=py"
if not defined PYTHON_CMD (
  where python >nul 2>nul && set "PYTHON_CMD=python"
)
if defined PYTHON_CMD (
  "%PYTHON_CMD%" --version >nul 2>nul
  if errorlevel 1 set "PYTHON_CMD="
)
if not defined PYTHON_CMD (
  if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON_CMD=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
)
if not defined PYTHON_CMD (
  echo ERROR: No se encontro Python. Instala Python 3 para Windows y vuelve a intentarlo.
  pause
  exit /b 1
)

echo Iniciando API Python. Deja esta ventana abierta.
"%PYTHON_CMD%" server.py
if errorlevel 1 (
  echo ERROR: La API se detuvo. Revisa el mensaje anterior.
  pause
)
endlocal

