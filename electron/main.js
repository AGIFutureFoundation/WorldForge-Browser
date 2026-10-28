// WorldForge Electron Wrapper
// npx electron . [--world climate-dao] [--port 8094]
const { app, BrowserWindow, screen } = require('electron');
const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

// Handle both development and packaged app
const isPackaged = app.isPackaged;
const SITE_ROOT = isPackaged
  ? path.join(process.resourcesPath, 'site', 'earth')
  : path.join(__dirname, '..', 'site', 'earth');
const PORT = parseInt(process.argv.find(a => a.startsWith('--port='))?.split('=')[1] || '8094');
const DEFAULT_WORLD = process.argv.find(a => a.startsWith('--world='))?.split('=')[1] || 'climate-dao';

// MIME types for static server
const MIME = {
  '.html': 'text/html', '.js': 'application/javascript', '.mjs': 'application/javascript',
  '.css': 'text/css', '.json': 'application/json', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif',
  '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.webp': 'image/webp',
  '.glb': 'model/gltf-binary', '.gltf': 'model/gltf+json',
  '.mp4': 'video/mp4', '.webm': 'video/webm',
  '.wasm': 'application/wasm', '.ttf': 'font/ttf', '.woff': 'font/woff', '.woff2': 'font/woff2',
};

function startServer(root, port) {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      let filePath = path.join(root, req.url === '/' ? 'index.html' : req.url.split('?')[0]);
      // Security: prevent directory traversal
      if (!filePath.startsWith(root)) { res.writeHead(403); res.end(); return; }
      const ext = path.extname(filePath).toLowerCase();
      const mime = MIME[ext] || 'application/octet-stream';

      fs.readFile(filePath, (err, data) => {
        if (err) {
          if (err.code === 'ENOENT') { res.writeHead(404); res.end('Not Found'); }
          else { res.writeHead(500); res.end('Server Error'); }
          return;
        }
        // CORS headers for module imports
        res.writeHead(200, {
          'Content-Type': mime,
          'Access-Control-Allow-Origin': '*',
          'Cache-Control': 'no-cache',
        });
        res.end(data);
      });
    });
    server.listen(port, '127.0.0.1', () => {
      console.log(`Static server: http://127.0.0.1:${PORT}`);
      resolve(server);
    });
  });
}

let mainWindow;
let httpServer;

async function createWindow(worldSlug) {
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.workAreaSize;

  mainWindow = new BrowserWindow({
    width: Math.min(1280, width),
    height: Math.min(720, height),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: false, // Allow local module imports
    },
    backgroundColor: '#000000',
  });

  const pageUrl = `http://127.0.0.1:${PORT}/world.html?world=${worldSlug}`;
  console.log(`Loading: ${pageUrl}`);
  await mainWindow.loadURL(pageUrl);

  mainWindow.on('closed', () => { mainWindow = null; });
}

app.whenReady().then(async () => {
  httpServer = await startServer(SITE_ROOT, PORT);
  await createWindow(DEFAULT_WORLD);
});

app.on('window-all-closed', () => {
  if (httpServer) httpServer.close();
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', async () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    await createWindow(DEFAULT_WORLD);
  }
});
