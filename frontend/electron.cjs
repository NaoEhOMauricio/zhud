const { app, BrowserWindow, screen, ipcMain, dialog } = require('electron')
const path  = require('path')
const { spawn } = require('child_process')

let mainWindow
let backendProcess = null

// ── Backend startup (only in packaged mode) ───────────────────────────────────
function startBackend() {
  if (!app.isPackaged) return   // dev mode: backend started manually

  const backendExe  = path.join(process.resourcesPath, 'backend', 'ZHud-backend.exe')
  const userDataDir = app.getPath('userData')   // e.g. %APPDATA%\ZHud

  console.log('[electron] Starting backend:', backendExe)
  console.log('[electron] User data dir:',  userDataDir)

  try {
    backendProcess = spawn(backendExe, [], {
      cwd: path.dirname(backendExe),
      env: { ...process.env, ZHUD_DATA_DIR: userDataDir },
      detached: false,
      windowsHide: true,
    })

    backendProcess.stdout?.on('data', d => process.stdout.write('[backend] ' + d))
    backendProcess.stderr?.on('data', d => process.stderr.write('[backend] ' + d))
    backendProcess.on('error',  e  => console.error('[backend] Error:', e.message))
    backendProcess.on('exit',   code => console.log('[backend] Exited with code', code))
  } catch (e) {
    console.error('[backend] Failed to start:', e.message)
    dialog.showErrorBox(
      'ZHud — Erro ao iniciar backend',
      `Não foi possível iniciar o backend.\n\nArquivo: ${backendExe}\nErro: ${e.message}`
    )
  }
}

// ── Wait until backend is accepting connections ───────────────────────────────
async function waitForBackend(url = 'http://127.0.0.1:8765/setup/status', maxWait = 15000) {
  const start = Date.now()
  while (Date.now() - start < maxWait) {
    try {
      const r = await fetch(url)
      if (r.ok) return true
    } catch { /* not ready yet */ }
    await new Promise(res => setTimeout(res, 300))
  }
  return false
}

// ── Main window ───────────────────────────────────────────────────────────────
function createWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize

  mainWindow = new BrowserWindow({
    width: 320,
    height: height,
    x: width - 322,
    y: 0,
    frame: false,
    resizable: true,
    minWidth: 280,
    maxWidth: 480,
    alwaysOnTop: false,
    skipTaskbar: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.cjs'),
    },
  })

  if (!app.isPackaged) {
    mainWindow.loadURL('http://localhost:5173')
  } else {
    mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'))
  }
}

// ── App lifecycle ─────────────────────────────────────────────────────────────
app.whenReady().then(async () => {
  startBackend()

  if (app.isPackaged) {
    console.log('[electron] Waiting for backend...')
    const ok = await waitForBackend()
    if (!ok) console.warn('[electron] Backend did not respond in time — continuing anyway')
  }

  createWindow()
})

async function shutdownBackend() {
  if (!backendProcess) return
  // 1. Ask backend to save state and shut down gracefully
  try {
    await fetch('http://127.0.0.1:8765/shutdown', { method: 'POST' })
    await new Promise(res => setTimeout(res, 1200))   // wait for clean exit
  } catch { /* backend already dead */ }
  // 2. Force kill if still running
  try { backendProcess.kill() } catch {}
  backendProcess = null
}

app.on('window-all-closed', async () => {
  await shutdownBackend()
  app.quit()
})

// ── IPC ───────────────────────────────────────────────────────────────────────
ipcMain.on('set-always-on-top', (_, value) => mainWindow?.setAlwaysOnTop(value))
ipcMain.on('minimize-window',   () => mainWindow?.minimize())
ipcMain.on('close-window',      () => mainWindow?.close())

// ── Auto-updater (GitHub Releases) ───────────────────────────────────────────
if (app.isPackaged) {
  try {
    const { autoUpdater } = require('electron-updater')
    autoUpdater.logger = console
    autoUpdater.checkForUpdatesAndNotify()

    autoUpdater.on('update-available', () => {
      mainWindow?.webContents.send('update-available')
    })
    autoUpdater.on('update-downloaded', () => {
      mainWindow?.webContents.send('update-downloaded')
    })
  } catch (e) {
    // electron-updater not available or no publish config — skip silently
    console.log('[updater] Not configured:', e.message)
  }
}
