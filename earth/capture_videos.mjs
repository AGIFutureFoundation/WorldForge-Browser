// Capture 3-second videos for every world with geo data.
// node earth/capture_videos.mjs [--worlds a,b] [--seconds 3]
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { session, open, shot, wf, sleep, tmp } from './cdp.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, '../site/earth/videos');
const arg = (n, d) => { const i = process.argv.indexOf('--' + n); return i > 0 ? process.argv[i + 1] : d; };
const SECS = Number(arg('seconds', 3));
const FPS = 8;
let SLUGS = arg('worlds', '');
if (!SLUGS) {
  const dataDir = path.join(__dirname, '../site/earth/data');
  SLUGS = fs.readdirSync(dataDir).filter(f => f.endsWith('.geo.json')).map(f => f.replace('.geo.json', '')).join(',');
}
const worlds = SLUGS.split(',').filter(Boolean);
console.log('Capturing ' + worlds.length + ' worlds, ' + SECS + 's each at ' + FPS + 'fps...');

fs.mkdirSync(OUT, { recursive: true });

let S;
const results = [];
try {
  S = await session(960, 540);
  for (let wi = 0; wi < worlds.length; wi++) {
    const slug = worlds[wi];
    try {
      console.log('[' + (wi + 1) + '/' + worlds.length + '] ' + slug + '...');
      const w = await open(S, slug, '&tour=1', { timeoutMs: 90000, fallback: true });
      await sleep(4000);
      // Add clean overlay
      await S.ev('(function(){var d=document.createElement("div");d.id="vid-overlay";d.innerHTML="<div style=\'position:fixed;left:20px;top:20px;font:700 20px system-ui;color:#fff;text-shadow:0 2px 12px #000;z-index:10\'>WorldForge Earth - SLUG</div>";document.body.appendChild(d)})()'.replace('SLUG', slug));
      // Capture frames
      const frames = SECS * FPS;
      for (let i = 0; i < frames; i++) {
        const jpg = await shot(S, 82);
        fs.writeFileSync(path.join(OUT, slug + '-f' + String(i).padStart(4, '0') + '.jpg'), jpg);
        await sleep(1000 / FPS);
      }
      // Encode to MP4
      execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-framerate', String(FPS), '-i', path.join(OUT, slug + '-f%04d.jpg'), '-vf', 'fps=24,format=yuv420p', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22', '-movflags', '+faststart', path.join(OUT, slug + '.mp4')]);
      const size = fs.statSync(path.join(OUT, slug + '.mp4')).size;
      results.push({ slug, ok: true, fallback: !!w.fallback, size, frames });
      console.log('  OK ' + slug + ' (' + (size / 1024).toFixed(0) + ' KB)' + (w.fallback ? ' [fallback: world not fully ready]' : ''));
      // Clean up frames
      for (let i = 0; i < frames; i++) { fs.unlinkSync(path.join(OUT, slug + '-f' + String(i).padStart(4, '0') + '.jpg')); }
    } catch (e) {
      results.push({ slug, ok: false, error: e.message });
      console.log('  FAIL ' + slug + ': ' + e.message);
    }
  }
} finally { S?.close(); }
// Merge results into the existing manifest (so batch runs accumulate instead of overwrite)
const MANIFEST = path.join(OUT, 'manifest.json');
let merged = {};
try { merged = JSON.parse(fs.readFileSync(MANIFEST, 'utf8')); } catch {}
if (!merged.results) { merged = { total: 0, captured: 0, failed: 0, results: [] }; }
const bySlug = new Map(merged.results.map(r => [r.slug, r]));
for (const r of results) bySlug.set(r.slug, r); // current run wins
merged.results = [...bySlug.values()];
const allSlugs = fs.readdirSync(path.join(__dirname, '../site/earth/data')).filter(f => f.endsWith('.geo.json')).map(f => f.replace('.geo.json', ''));
merged.total = allSlugs.length;
merged.captured = merged.results.filter(r => r.ok).length;
merged.failed = merged.results.filter(r => !r.ok).length;
fs.writeFileSync(MANIFEST, JSON.stringify(merged, null, 2));
const runOk = results.filter(r => r.ok).length;
console.log('Done: ' + runOk + '/' + worlds.length + ' captured (this run); manifest total: ' + merged.captured + '/' + merged.total);