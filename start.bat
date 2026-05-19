@echo off
title ZHud

echo ========================================
echo  ZHud - Iniciando...
echo ========================================
echo.
echo Backend: http://127.0.0.1:8765
echo.

:: Inicia o backend Python (auto-detecta a pasta do PokerStars)
start "ZHud Backend" cmd /k "cd /d "%~dp0backend" && python main.py"

:: Aguarda o backend inicializar
timeout /t 3 /nobreak >nul

:: Inicia o frontend (Electron + Vite)
cd /d "%~dp0frontend"
npm run start

exit /b 0
