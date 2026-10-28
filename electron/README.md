# WorldForge Desktop (Electron)

Wrap WorldForge Browser as a native desktop app with bundled static server.

## Quick Start

```bash
cd electron
npm install
npm start
```

## CLI Options

```bash
npm start                              # Default: climate-dao
npm start -- --world=locator-x         # Specific world
npm start -- --port=3000               # Custom port
```

## Building Distributables

```bash
npm run build:mac    # .dmg + .zip
npm run build:win    # .exe (NSIS + portable)
npm run build:linux  # .AppImage + .deb
```

Output goes to `../dist/`.

## Architecture

- **main.js** — Chromium process with embedded HTTP server
- **preload.js** — Safe bridge for `window.electronAPI`
- **../site/earth/** — Static assets served at runtime (bundled into app)
