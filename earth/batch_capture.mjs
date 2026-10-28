#!/usr/bin/env node
// Batch capture all worlds with progress reporting.
// Usage: node earth/batch_capture.mjs [--seconds 3] [--concurrency 1]
import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(__dirname, '../site/earth/data');
const videoDir = path.join(__dirname, '../site/earth/videos');

const arg = (n, d) => { const i = process.argv.indexOf('--' + n); return i > 0 ? process.argv[i + 1] : d; };
const SECS = Number(arg('seconds', 3));
const BATCH = Number(arg('batch', 10)); // worlds per Chrome instance

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
  process.exit(0);
}

// Process in batches
for (let i = 0; i < remaining.length; i += BATCH) {
  const batch = remaining.slice(i, i + BATCH);
  console.log(`\n--- Batch ${Math.floor(i / BATCH) + 1}: ${batch.join(', ')} ---`);
  
  try {
    const result = execSync(
      `node earth/capture_videos.mjs --worlds ${batch.join(',')} --seconds ${SECS}`,
      { cwd: path.join(__dirname, '..'), stdio: 'inherit', timeout: 1800000 } // 30 min timeout per batch (worst case 10 x ~110s)
    );
  } catch (e) {
    console.error(`Batch failed: ${e.message}`);
  }
  
  // Progress summary
  const currentCaptured = fs.readdirSync(videoDir).filter(f => f.endsWith('.mp4')).length;
  console.log(`Progress: ${currentCaptured}/${allWorlds.length} (${((currentCaptured / allWorlds.length) * 100).toFixed(1)}%)`);
}

console.log('\nBatch capture complete!');
