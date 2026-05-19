const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('zhud', {
  setAlwaysOnTop:     (val) => ipcRenderer.send('set-always-on-top', val),
  minimize:           ()    => ipcRenderer.send('minimize-window'),
  close:              ()    => ipcRenderer.send('close-window'),
  restartToUpdate:    ()    => ipcRenderer.send('restart-to-update'),
  onUpdateAvailable:  (cb)  => ipcRenderer.on('update-available',  (_, ...a) => cb(...a)),
  onUpdateDownloaded: (cb)  => ipcRenderer.on('update-downloaded', (_, ...a) => cb(...a)),
})
