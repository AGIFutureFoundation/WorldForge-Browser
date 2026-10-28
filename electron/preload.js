// Preload: bridge safe APIs from main to renderer
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getPlatform: () => process.platform,
  getVersion: () => process.versions,
  onWorldChange: (callback) => ipcRenderer.on('world-change', (_, world) => callback(world)),
});
