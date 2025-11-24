@echo off
REM ============================================================================
REM ARGO V10.12 - Iniciar Frontend
REM ============================================================================

echo.
echo ========================================================================
echo ARGO V10.12 - FRONTEND
echo ========================================================================
echo.

REM Cambiar al directorio del frontend
cd ARGO\frontend\client

echo Iniciando servidor de desarrollo Vite...
echo.
echo Frontend estará disponible en:
echo   - http://localhost:5173
echo.
echo Presione Ctrl+C para detener el servidor
echo ========================================================================
echo.

REM Iniciar npm dev
call npm run dev

pause
