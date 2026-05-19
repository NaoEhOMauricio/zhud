const { app, BrowserWindow, screen, ipcMain, dialog } = require('electron')
const path  = require('path')
const { spawn } = require('child_process')

let mainWindow
let backendProcess = null

// ── Backend startup (only in packaged mode) ───────────────────────────────────
function startBackend() {
  if (!app.isPackaged) return

  const backendExe  = path.join(process.resourcesPath, 'backend', 'ZHud-backend.exe')
  const userDataDir = app.getPath('userData')

  console.log('[electron] Starting backend:', backendExe)

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
    dialog.showErrorBox('ZHud — Erro ao iniciar backend', `Erro: ${e.message}`)
  }
}

async function waitForBackend(url = 'http://127.0.0.1:8765/setup/status', maxWait = 15000) {
  const start = Date.now()
  while (Date.now() - start < maxWait) {
    try {
      const r = await fetch(url)
      if (r.ok) return true
    } catch {}
    await new Promise(res => setTimeout(res, 300))
  }
  return false
}

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

// ── Auto-updater — called AFTER window is ready ───────────────────────────────
function setupAutoUpdater() {
  if (!app.isPackaged) return
  try {
    const { autoUpdater } = require('electron-updater')
    autoUpdater.logger = console
    autoUpdater.autoDownload = true

    autoUpdater.on('checking-for-update',  ()    => console.log('[updater] Checking...'))
    autoUpdater.on('update-not-available', ()    => console.log('[updater] Up to date'))
    autoUpdater.on('error',                (err) => console.error('[updater] Error:', err.message))

    autoUpdater.on('update-available', (info) => {
      console.log('[updater] Update available:', info.version)
      mainWindow?.webContents.send('update-available')
    })

    autoUpdater.on('update-downloaded', (info) => {
      console.log('[updater] Downloaded:', info.version)
      mainWindow?.webContents.send('update-downloaded')
    })

    autoUpdater.checkForUpdates()
      .catch(e => console.error('[updater] checkForUpdates failed:', e.message))

  } catch (e) {
    console.error('[updater] Setup failed:', e.message)
  }
}

// ── App lifecycle ─────────────────────────────────────────────────────────────
app.whenReady().then(async () => {
  startBackend()

  if (app.isPackaged) {
    const ok = await waitForBackend()
    if (!ok) console.warn('[electron] Backend timeout — continuing anyway')
  }

  createWindow()

  // Start auto-updater 5s after window is created (ensures renderer is ready)
  mainWindow.webContents.once('did-finish-load', () => {
    setTimeout(setupAutoUpdater, 5000)
  })
})

async function shutdownBackend() {
  if (!backendProcess) return
  try {
    await fetch('http://127.0.0.1:8765/shutdown', { method: 'POST' })
    await new Promise(res => setTimeout(res, 1200))
  } catch {}
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
ipcMain.on('restart-to-update', () => {
  if (app.isPackaged) {
    try { require('electron-updater').autoUpdater.quitAndInstall() } catch {}
  }
})
