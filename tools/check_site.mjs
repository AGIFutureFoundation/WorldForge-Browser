#!/usr/bin/env node
// Checks the committed site/ against its own manifest, with no network and no dependencies:
//   1. every file in site/site-manifest.json exists, with the recorded size and sha256
//   2. every relative href/src in the HTML pages resolves to a file inside site/
//   3. no credential-shaped string and no local filesystem path ships
//   node tools/check_site.mjs        exit 1 on any failure
import { readFileSync, existsSync, statSync, readdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join, dirname, relative, extname } from 'node:path';
import { fileURLToPath } from 'node:url';

const SITE = join(dirname(fileURLToPath(import.meta.url)), '..', 'site');
let failed = 0;
let passed = 0;
const ok = (name, cond, detail = '') => {
  if (cond) passed++;
  else { failed++; console.log(`FAIL ${name}${detail ? `: ${detail}` : ''}`); }
};

function* walk(dir) {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, e.name);
    if (e.isDirectory()) yield* walk(p);
    else yield p;
  }
}

// 1. manifest
const manifest = JSON.parse(readFileSync(join(SITE, 'site-manifest.json'), 'utf8'));
// contents is { "<site path>": { bytes, sha256?, why } } (build_site.py); accept a list of { path } too
const entries = Array.isArray(manifest.contents)
  ? manifest.contents
  : Object.entries(manifest.contents || {}).map(([path, v]) => ({ path, ...v }));
let checked = 0;
for (const e of entries) {
  const rel = e.path || e.site || e.dest;
  if (!rel) continue;
  const p = join(SITE, rel.replace(/^\//, ''));
  if (!existsSync(p)) { ok(`manifest file present ${rel}`, false); continue; }
  if (e.bytes !== undefined) ok(`size ${rel}`, statSync(p).size === e.bytes, `${statSync(p).size} != ${e.bytes}`);
  if (e.sha256) ok(`sha256 ${rel}`, createHash('sha256').update(readFileSync(p)).digest('hex') === e.sha256);
  checked++;
}
ok('manifest lists files', checked > 0, 'no entries with a path were found in site-manifest.json');

// 2. relative links in HTML
// Pages that live in the source monorepo and are deliberately not part of this site
// (build_site.py reports the same links as known 404s). Keep this list short and explicit.
const KNOWN_OUTSIDE = new Set(['my-fabric/viewer.html', 'consoles/hive/index.html']);
let links = 0;
for (const f of walk(SITE)) {
  if (extname(f) !== '.html') continue;
  const html = readFileSync(f, 'utf8');
  for (const m of html.matchAll(/\b(?:href|src)\s*=\s*"([^"#?]+)[^"]*"/g)) {
    const ref = m[1];
    // skip absolute/external URLs and links the page assembles in JS ('...' + esc(x) + '...', ${x})
    if (/^(?:[a-z]+:|\/\/|data:|mailto:|javascript:)/i.test(ref) || ref.startsWith('/') || /\$\{|' \+ |" \+ /.test(ref)) continue;
    let target = join(dirname(f), ref);
    if (ref.endsWith('/')) target = join(target, 'index.html');
    if (!target.startsWith(SITE)) continue; // links outside the site are reported by the build as known 404s
    if (KNOWN_OUTSIDE.has(relative(SITE, target))) continue;
    links++;
    ok(`link ${relative(SITE, f)} -> ${ref}`, existsSync(target));
  }
}

// 3. nothing secret or local ships
const TEXT = new Set(['.html', '.js', '.mjs', '.json', '.md', '.txt', '.vtt', '.css', '.sql']);
const SECRET = /(?:\bsk-[A-Za-z0-9]{32,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|PRIVATE_KEY=0x[0-9a-fA-F]{64}|\bghp_[A-Za-z0-9]{30,}|\bAKIA[0-9A-Z]{16}\b|\/Users\/[a-z0-9._-]+\/)/;
for (const f of walk(SITE)) {
  if (!TEXT.has(extname(f))) continue;
  const hit = readFileSync(f, 'utf8').match(SECRET);
  ok(`no secret or local path in ${relative(SITE, f)}`, !hit, hit && hit[0].slice(0, 12) + '...');
}

console.log(`site: ${checked} manifest files, ${links} relative links, ${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
