const { app, BrowserWindow, screen, ipcMain, dialog } = require('electron')
const path  = require('path')
const { spawn, exec } = require('child_process')

let mainWindow
let backendProcess = null
let _lastReportedTable = null

// ── PokerStars window detection ───────────────────────────────────────────────
// Reads the FOREGROUND window title every 2s.
// If it's a PokerStars game window, extracts the table name and tells the backend.
// Title format: "... - Torneio 4001866684 Mesa 1 - Logado como NaoEOMauricio - Mão #3/3"
// Cash format:  "... - Mesa 12345678 - Logado como NaoEOMauricio"
const PS_CMD = String.raw`
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices; using System.Text;
public class U32 {
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
}
'@
$h = [U32]::GetForegroundWindow(); $s = New-Object System.Text.StringBuilder(512)
[U32]::GetWindowText($h, $s, 512); $s.ToString()
`.trim()

function _parsePokerTable(title) {
  if (!title || !title.includes('PokerStars') && !title.includes('Torneio') && !title.includes('Hold')) return null
  // Tournament: "Torneio 4001866684 Mesa 1"
  const mt = title.match(/Torneio\s+(\d+)\s+Mesa\s+(\d+)/i)
  if (mt) return `${mt[1]} ${mt[2]}`
  // Cash: "Mesa 12345678"
  const mc = title.match(/Mesa\s+(\d+)/i)
  if (mc) return mc[1]
  return null
}

function pollForegroundTable() {
  exec(`powershell -NoProfile -NonInteractive -Command "${PS_CMD.replace(/"/g, '\\"').replace(/\n/g, ' ')}"`,
    { timeout: 1500 },
    (err, stdout) => {
      if (err || !stdout) return
      const table = _parsePokerTable(stdout.trim())
      if (table && table !== _lastReportedTable) {
        _lastReportedTable = table
        fetch('http://127.0.0.1:8765/active-tables/set-current', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ table }),
        }).catch(() => {})
      }
    }
  )
}

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

  // Poll PokerStars foreground window every 2s to track current table
  setInterval(pollForegroundTable, 2000)
})

let _shuttingDown = false

async function shutdownBackend() {
  if (!backendProcess || _shuttingDown) return
  _shuttingDown = true
  const pid = backendProcess.pid

  // 1. Ask the backend to shut down gracefully
  try {
    await fetch('http://127.0.0.1:8765/shutdown', { method: 'POST' })
  } catch {}

  // 2. Wait for process to exit on its own (up to 2.5s)
  await new Promise(res => {
    const t = setTimeout(res, 2500)
    backendProcess?.once('exit', () => { clearTimeout(t); res() })
  })

  // 3. Force-kill the entire process tree (Windows: PyInstaller spawns children)
  if (pid) {
    try {
      const { execSync } = require('child_process')
      execSync(`taskkill /F /T /PID ${pid}`, { stdio: 'ignore' })
    } catch {}
  }
  try { backendProcess?.kill('SIGKILL') } catch {}
  backendProcess = null
}

// will-quit fires for all exit paths (close button, update, OS shutdown)
app.on('will-quit', (event) => {
  if (!backendProcess) return
  event.preventDefault()
  shutdownBackend().then(() => app.exit(0))
})

// ── IPC ───────────────────────────────────────────────────────────────────────
ipcMain.on('set-always-on-top', (_, value) => mainWindow?.setAlwaysOnTop(value))
ipcMain.on('minimize-window',   () => mainWindow?.minimize())
ipcMain.on('close-window',      () => mainWindow?.close())
ipcMain.on('restart-to-update', async () => {
  if (!app.isPackaged) return
  // Backend must be fully stopped before the installer can replace the .exe
  await shutdownBackend()
  try { require('electron-updater').autoUpdater.quitAndInstall(false, true) } catch {}
})
