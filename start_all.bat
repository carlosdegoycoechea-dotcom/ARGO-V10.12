@echo off
REM ============================================================================
REM ARGO V10.12 - Iniciar Backend + Frontend
REM ============================================================================

echo.
echo ========================================================================
echo ARGO V10.12 - INICIO COMPLETO
echo ========================================================================
echo.
echo Iniciando Backend y Frontend en ventanas separadas...
echo.

REM Iniciar Backend en nueva ventana
start "ARGO Backend" cmd /k start_backend.bat

REM Esperar 3 segundos para que backend inicie
timeout /t 3 /nobreak >nul

REM Iniciar Frontend en nueva ventana
start "ARGO Frontend" cmd /k start_frontend.bat

echo.
echo ========================================================================
echo ARGO iniciado correctamente
echo ========================================================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo Docs:     http://localhost:8000/docs
echo.
echo Para detener, cierre las ventanas del Backend y Frontend
echo ========================================================================
echo.

pause
