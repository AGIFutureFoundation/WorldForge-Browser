#!/usr/bin/env node
// Batch capture all worlds with progress reporting.
// Spawns its own static server (earth/serve.mjs) so it survives independent of any external server.
// Usage: node earth/batch_capture.mjs [--seconds 3] [--batch 10] [--port 8094]
import { execSync, spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(__dirname, '../site/earth/data');
const videoDir = path.join(__dirname, '../site/earth/videos');

const arg = (n, d) => { const i = process.argv.indexOf('--' + n); return i > 0 ? process.argv[i + 1] : d; };
const SECS = Number(arg('seconds', 3));
const BATCH = Number(arg('batch', 10)); // worlds per Chrome instance
const PORT = Number(arg('port', 8094));

// --- Built-in static server (child process; killed on exit) ---
const server = spawn(process.execPath, [path.join(__dirname, 'serve.mjs'), String(PORT)],
  { stdio: ['ignore', 'inherit', 'inherit'], detached: false, env: { ...process.env, PORT: String(PORT) } });
const killServer = () => { try { server.kill('SIGTERM'); } catch {} };
process.on('exit', killServer);
process.on('SIGINT', () => { killServer(); process.exit(130); });
process.on('SIGTERM', () => { killServer(); process.exit(143); });

// Wait until the server answers before proceeding
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const waitForServer = async () => {
  for (let i = 0; i < 60; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/earth/world.html?world=ping`, { method: 'GET' });
      if (r.status < 500) return true;
    } catch {}
    await sleep(500);
  }
  throw new Error('built-in server failed to start on port ' + PORT);
};

// Get all world slugs
const allWorlds = fs.readdirSync(dataDir)
  .filter(f => f.endsWith('.geo.json'))
  .map(f => f.replace('.geo.json', ''));

// Filter out already captured
const captured = new Set(
  fs.readdirSync(videoDir)
    .filter(f => f.endsWith('.mp4'))
    .map(f => f.replace('.mp4', ''))
);

const remaining = allWorlds.filter(w => !captured.has(w));
console.log(`Total: ${allWorlds.length} | Captured: ${captured.size} | Remaining: ${remaining.length}`);

if (remaining.length === 0) {
  console.log('All worlds already captured!');
  killServer();
  process.exit(0);
}

await waitForServer();

// Process in batches
for (let i = 0; i < remaining.length; i += BATCH) {
  const batch = remaining.slice(i, i + BATCH);
  console.log(`\n--- Batch ${Math.floor(i / BATCH) + 1}: ${batch.join(', ')} ---`);

  try {
    const env = { ...process.env, WF_BASE: `http://127.0.0.1:${PORT}` };
    const result = execSync(
      `node earth/capture_videos.mjs --worlds ${batch.join(',')} --seconds ${SECS}`,
      { cwd: path.join(__dirname, '..'), stdio: 'inherit', timeout: 1800000, env } // 30 min timeout per batch (worst case 10 x ~110s)
    );
  } catch (e) {
    console.error(`Batch failed: ${e.message}`);
  }

  // Progress summary
  const currentCaptured = fs.readdirSync(videoDir).filter(f => f.endsWith('.mp4')).length;
  console.log(`Progress: ${currentCaptured}/${allWorlds.length} (${((currentCaptured / allWorlds.length) * 100).toFixed(1)}%)`);
}

console.log('\nBatch capture complete!');
killServer();
