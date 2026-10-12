@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_CMD="
where py >nul 2>nul && set "PYTHON_CMD=py"
if not defined PYTHON_CMD (
  where python >nul 2>nul && set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
  echo ERROR: No se encontro Python ni el lanzador py. Instala Python 3 desde https://www.python.org/downloads/windows/ y marca Add python.exe to PATH. El lanzador py tambien es compatible.
  echo Angular no se iniciara hasta que Python este disponible.
  pause
  exit /b 1
)
"%PYTHON_CMD%" --version >nul 2>nul
if errorlevel 1 (
  echo ERROR: Se encontro un comando Python, pero no se pudo ejecutar. Revisa la instalacion de Python o desactiva los alias de Microsoft Store en Configuracion.
  pause
  exit /b 1
)
where node >nul 2>nul
if errorlevel 1 (
  echo ERROR: No se encontro Node.js. Instala la version LTS desde https://nodejs.org/.
  pause
  exit /b 1
)
node -e "const [M,m,p]=process.versions.node.split('.').map(Number);if((M===22&&(m>22||(m===22&&p>=3)))||(M===24&&m>=15)||M>=26)process.exit(0);process.exit(1)"
if errorlevel 1 (
  echo ERROR: Angular requiere Node.js 22.22.3 o posterior compatible, 24.15 o posterior, o 26+. Instala Node.js LTS desde https://nodejs.org/.
  pause
  exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
  echo ERROR: No se encontro npm. Reinstala Node.js LTS con npm incluido y abre una terminal nueva.
  pause
  exit /b 1
)
echo Requisitos encontrados:
"%PYTHON_CMD%" --version
node --version
npm --version
if not exist "frontend\node_modules\@angular\cli\bin\ng.js" (
  echo Instalando dependencias de Angular por primera vez...
  pushd frontend
  call npm install
  if errorlevel 1 (
    echo ERROR: No se pudieron instalar las dependencias. Comprueba la conexion a Internet y vuelve a ejecutar este archivo.
    popd
    pause
    exit /b 1
  )
  popd
)
start "Laboratorio - API Python" /D "%~dp0backend" cmd /k "%PYTHON_CMD% server.py"
start "Laboratorio - Angular" /D "%~dp0frontend" cmd /k "npm start"
echo.
echo API:              http://localhost:8000/api/state
echo Pantalla cliente: http://localhost:4200/cliente
echo Pantalla atencion: http://localhost:4200/atencion
echo Espere a que Angular indique que compilo correctamente.
endlocal



