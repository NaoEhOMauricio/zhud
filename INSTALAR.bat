@echo off
title ZHud - Instalacao
color 0A
echo ============================================================
echo   ZHud - Instalacao
echo ============================================================
echo.

:: Verifica Python
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERRO] Python nao encontrado!
    echo.
    echo Instale o Python 3.10 ou superior em:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANTE: marque "Add Python to PATH" durante a instalacao.
    echo.
    pause
    start https://www.python.org/downloads/
    exit /b 1
)
echo [OK] Python encontrado.

:: Verifica Node.js
node --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERRO] Node.js nao encontrado!
    echo.
    echo Instale o Node.js 18 LTS ou superior em:
    echo https://nodejs.org/
    echo.
    pause
    start https://nodejs.org/
    exit /b 1
)
echo [OK] Node.js encontrado.

echo.
echo [1/2] Instalando dependencias Python...
cd /d "%~dp0backend"
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERRO] Falha ao instalar dependencias Python.
    pause
    exit /b 1
)
echo [OK] Backend instalado.

echo.
echo [2/2] Instalando dependencias Node.js...
cd /d "%~dp0frontend"
npm install
if %ERRORLEVEL% neq 0 (
    echo [ERRO] Falha ao instalar dependencias Node.js.
    pause
    exit /b 1
)
echo [OK] Frontend instalado.

echo.
echo ============================================================
echo   Instalacao concluida!
echo.
echo   Para usar o ZHud:
echo   - Abra o PokerStars e entre em uma mesa
echo   - Clique duas vezes em  start.bat
echo   - Na primeira vez, selecione seu nick
echo ============================================================
echo.
pause
