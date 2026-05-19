const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('zhud', {
  setAlwaysOnTop: (val) => ipcRenderer.send('set-always-on-top', val),
  minimize:       ()    => ipcRenderer.send('minimize-window'),
  close:          ()    => ipcRenderer.send('close-window'),
  onUpdateAvailable:  (cb) => ipcRenderer.on('update-available',  cb),
  onUpdateDownloaded: (cb) => ipcRenderer.on('update-downloaded', cb),
})
