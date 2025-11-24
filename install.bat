@echo off
REM ============================================================================
REM ARGO V10.12 - Script de Instalación
REM ============================================================================
REM Este script instala todas las dependencias necesarias para ARGO
REM ============================================================================

echo.
echo ========================================================================
echo ARGO V10.12 - INSTALACION
echo ========================================================================
echo.

REM Verificar Python
echo [1/4] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en el PATH
    echo Por favor instale Python 3.10 o superior desde https://www.python.org/
    pause
    exit /b 1
)
python --version
echo.

REM Verificar Node.js
echo [2/4] Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js no está instalado o no está en el PATH
    echo Por favor instale Node.js 18 o superior desde https://nodejs.org/
    pause
    exit /b 1
)
node --version
echo.

REM Instalar dependencias Python (Backend)
echo [3/4] Instalando dependencias Python (Backend)...
cd ARGO
pip install -r backend/requirements.txt
if errorlevel 1 (
    echo ERROR: Falló la instalación de dependencias Python
    pause
    exit /b 1
)
cd ..
echo ✓ Dependencias Python instaladas correctamente
echo.

REM Instalar dependencias Node.js (Frontend)
echo [4/4] Instalando dependencias Node.js (Frontend)...
cd ARGO\frontend\client
call npm install
if errorlevel 1 (
    echo ERROR: Falló la instalación de dependencias Node.js
    pause
    exit /b 1
)
cd ..\..\..
echo ✓ Dependencias Node.js instaladas correctamente
echo.

REM Crear archivo .env si no existe
if not exist "ARGO\backend\.env" (
    echo Creando archivo .env desde .env.example...
    copy "ARGO\backend\.env.example" "ARGO\backend\.env"
    echo.
    echo ⚠️  IMPORTANTE: Edite ARGO\backend\.env con sus API keys
    echo    - OPENAI_API_KEY
    echo    - ANTHROPIC_API_KEY
    echo.
)

echo ========================================================================
echo INSTALACION COMPLETADA
echo ========================================================================
echo.
echo Próximos pasos:
echo 1. Edite ARGO\backend\.env con sus API keys (OpenAI, Anthropic)
echo 2. Ejecute start_all.bat para iniciar ARGO
echo.
echo ========================================================================
pause
