@echo off
setlocal
cd /d "%~dp0"
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
  echo ERROR: No se encontro Python. Instala Python 3 desde https://www.python.org/downloads/windows/ y vuelve a ejecutar este archivo.
  pause
  exit /b 1
)
set "NODE_CMD=node"
where node >nul 2>nul
if errorlevel 1 set "NODE_CMD="
if defined NODE_CMD node -e "const [M,m,p]=process.versions.node.split('.').map(Number);if((M===22&&(m>22||(m===22&&p>=3)))||(M===24&&m>=15)||M>=26)process.exit(0);process.exit(1)"
if errorlevel 1 (
  set "NODE_CMD="
)
if not defined NODE_CMD (
  if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe" set "NODE_CMD=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
)
if not defined NODE_CMD (
  echo ERROR: No se encontro Node.js compatible. Angular requiere Node 22.22.3+, 24.15+ o 26+. Instala Node LTS desde https://nodejs.org/.
  pause
  exit /b 1
)
"%NODE_CMD%" -e "const [M,m,p]=process.versions.node.split('.').map(Number);if((M===22&&(m>22||(m===22&&p>=3)))||(M===24&&m>=15)||M>=26)process.exit(0);process.exit(1)"
if errorlevel 1 (
  echo ERROR: Node.js encontrado no es compatible con Angular. Instala Node 22.22.3+, 24.15+ o 26+.
  pause
  exit /b 1
)
echo Requisitos encontrados:
"%PYTHON_CMD%" --version
"%NODE_CMD%" --version
set "NODE_DIR="
for %%I in ("%NODE_CMD%") do set "NODE_DIR=%%~dpI"
set "PATH=%NODE_DIR%;%PATH%"
if not exist "frontend\node_modules\@angular\cli\bin\ng.js" (
  where npm >nul 2>nul
  if errorlevel 1 (
    echo ERROR: Faltan las dependencias de Angular y no se encontro npm. Instala Node LTS con npm y vuelve a ejecutar este archivo.
    pause
    exit /b 1
  )
  echo Instalando dependencias de Angular por primera vez...
  pushd frontend
  call npm ci
  if errorlevel 1 (
    echo ERROR: No se pudieron instalar las dependencias. Comprueba la conexion a Internet y vuelve a ejecutar este archivo.
    popd
    pause
    exit /b 1
  )
  popd
)
set "NG_CLI_ANALYTICS=false"
start "Laboratorio - API Python" /D "%~dp0backend" cmd /k ""%PYTHON_CMD%" server.py"
start "Laboratorio - Angular" /D "%~dp0frontend" cmd /k ""%NODE_CMD%" node_modules\@angular\cli\bin\ng.js serve --host 0.0.0.0 --port 4200 --proxy-config proxy.conf.json"
echo.
echo API:              http://localhost:8000/api/state
echo Pantalla cliente: http://localhost:4200/cliente
echo Pantalla atencion: http://localhost:4200/atencion
echo Deje abiertas ambas ventanas y espere a que Angular indique que compilo correctamente.
endlocal
