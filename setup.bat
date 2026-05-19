@echo off
title ZHud - Setup
echo ========================================
echo  ZHud Setup
echo ========================================
echo.

echo [1/2] Instalando dependencias Python...
cd /d "%~dp0backend"
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ERRO: Falha ao instalar dependencias Python.
    echo Certifique-se que Python 3.10+ esta instalado.
    pause & exit /b 1
)

echo.
echo [2/2] Instalando dependencias Node.js...
cd /d "%~dp0frontend"
npm install
if %ERRORLEVEL% neq 0 (
    echo ERRO: Falha ao instalar dependencias Node.js.
    echo Certifique-se que Node.js 18+ esta instalado.
    pause & exit /b 1
)

echo.
echo ========================================
echo  Setup concluido! Execute start.bat
echo ========================================
pause
