const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    getPlatform: () => ipcRenderer.invoke('get-platform'),
    checkServer: () => ipcRenderer.invoke('check-server'),
    executeScript: (script, type) => ipcRenderer.invoke('execute-script', { script, type }),
    openExternal: (url) => ipcRenderer.invoke('open-external', url),
    onScriptOutput: (callback) => ipcRenderer.on('script-output', (event, data) => callback(data))
});
