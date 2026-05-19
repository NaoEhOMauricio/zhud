@echo off
title ZHud - Build Instalador
color 0A

echo ============================================================
echo   ZHud - Criando instalador para Windows
echo ============================================================
echo.

:: ── Verifica dependencias ─────────────────────────────────────────────────────
python --version >nul 2>&1 || (echo [ERRO] Python nao encontrado & pause & exit /b 1)
node   --version >nul 2>&1 || (echo [ERRO] Node.js nao encontrado & pause & exit /b 1)

:: ── Diretorio raiz do projeto ─────────────────────────────────────────────────
set ROOT=%~dp0
set ROOT=%ROOT:~0,-1%

echo ROOT: %ROOT%
echo.

:: ── [1/5] Build Vite (frontend React) ────────────────────────────────────────
echo [1/5] Compilando frontend (React + Tailwind)...
cd /d "%ROOT%\frontend"
call npm install --silent
call npm run build
if %ERRORLEVEL% neq 0 (
    echo [ERRO] Falha no build do frontend.
    pause & exit /b 1
)
echo      Frontend OK.
echo.

:: ── [2/5] Instalar PyInstaller ────────────────────────────────────────────────
echo [2/5] Instalando PyInstaller...
pip install pyinstaller --quiet --upgrade
if %ERRORLEVEL% neq 0 (
    echo [ERRO] Falha ao instalar PyInstaller.
    pause & exit /b 1
)
echo      PyInstaller OK.
echo.

:: ── [3/5] Compilar backend Python → exe ──────────────────────────────────────
echo [3/5] Compilando backend Python ^> ZHud-backend.exe...
cd /d "%ROOT%\backend"
pyinstaller backend.spec --noconfirm --clean --distpath dist
if %ERRORLEVEL% neq 0 (
    echo [ERRO] Falha ao compilar backend.
    echo Tentando modo alternativo (--onefile)...
    pyinstaller --onefile --name ZHud-backend ^
        --hidden-import uvicorn.logging ^
        --hidden-import uvicorn.loops ^
        --hidden-import uvicorn.loops.auto ^
        --hidden-import uvicorn.protocols ^
        --hidden-import uvicorn.protocols.http ^
        --hidden-import uvicorn.protocols.http.auto ^
        --hidden-import uvicorn.protocols.websockets ^
        --hidden-import uvicorn.protocols.websockets.auto ^
        --hidden-import uvicorn.lifespan ^
        --hidden-import uvicorn.lifespan.on ^
        --hidden-import aiosqlite ^
        --hidden-import sqlalchemy.dialects.sqlite ^
        --hidden-import greenlet ^
        --hidden-import watchdog.observers ^
        --hidden-import watchdog.observers.polling ^
        --hidden-import winreg ^
        --collect-all sqlalchemy ^
        --noconfirm ^
        main.py
    if %ERRORLEVEL% neq 0 (
        echo [ERRO] Falha no build do backend.
        pause & exit /b 1
    )
)
echo      Backend OK: backend\dist\ZHud-backend.exe
echo.

:: ── [4/5] Instalar electron-builder e electron-updater ───────────────────────
echo [4/5] Instalando dependencias do instalador...
cd /d "%ROOT%\frontend"
call npm install --save-exact electron-builder electron-updater --save-dev --silent
echo      Dependencias OK.
echo.

:: ── [5/5] Criar instalador Windows ───────────────────────────────────────────
echo [5/5] Criando instalador Windows (.exe)...
cd /d "%ROOT%\frontend"
call npx electron-builder --win --x64 --publish never
if %ERRORLEVEL% neq 0 (
    echo [AVISO] electron-builder falhou. Verifique o log acima.
    echo Verifique se o arquivo backend\dist\ZHud-backend.exe existe.
    pause & exit /b 1
)
echo.
echo ============================================================
echo   BUILD CONCLUIDO!
echo.
echo   Arquivos gerados em:
echo     %ROOT%\frontend\dist-electron\
echo.
echo   Envie para o amigo:
echo     ZHud Setup 1.0.0.exe   (instalador completo)
echo     ZHud 1.0.0.exe         (versao portatil sem instalacao)
echo.
echo   Auto-update: configure publish.owner no package.json
echo   com seu usuario do GitHub para habilitar atualizacoes
echo   automaticas via GitHub Releases.
echo ============================================================
echo.
pause
