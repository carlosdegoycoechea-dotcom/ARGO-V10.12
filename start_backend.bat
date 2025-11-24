@echo off
REM ============================================================================
REM ARGO V10.12 - Iniciar Backend
REM ============================================================================

echo.
echo ========================================================================
echo ARGO V10.12 - BACKEND
echo ========================================================================
echo.

REM Verificar que existe .env
if not exist "ARGO\backend\.env" (
    echo ERROR: No se encontró el archivo .env
    echo Por favor ejecute install.bat primero
    pause
    exit /b 1
)

REM Cambiar al directorio del backend
cd ARGO\backend

echo Iniciando servidor FastAPI...
echo.
echo Backend estará disponible en:
echo   - API REST:     http://localhost:8000
echo   - Documentación: http://localhost:8000/docs
echo   - WebSocket:    ws://localhost:8000/ws/chat
echo.
echo Presione Ctrl+C para detener el servidor
echo ========================================================================
echo.

REM Iniciar uvicorn
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
