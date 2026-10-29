// server.mjs -- WorldForge API on Fly.io. A long-running Node service that mounts the SAME
// marketplace-v2 route file the Cloudflare Worker uses (cloud/datasets-api/src/routes/
// marketplace-v2.ts, via Node native type-stripping) and serves:
//   - the Movement LM artifacts (wf-motion-lm-1)
//   - the RP1 worlds registry (worlds anchored into rp1.com via enter.rp1.com URLs)
//   - the Sneeze / WorldForge engine: SOM mount plans, shared assets, preview GLBs
// Token handling: FLY_API_TOKEN is read from the environment or the gitignored .env at repo
// root -- never from this file (deploy.sh wires it; the GitHub workflow uses a repo secret).

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { Readable } from 'node:stream';
import { fileURLToPath } from 'node:url';
import { Hono } from 'hono';


const PORT = Number(process.env.PORT || 8080);
const ROOT = new URL('../../', import.meta.url);            // repo root (mirrored in the Docker image)
const app = new Hono();

app.get('/health', (c) => c.json({ status: 'ok', host: 'fly.io', service: 'worldforge-api', ts: Date.now() }));

// marketplace v2: the SAME route file the Cloudflare Worker registers (single source of truth).
// Dynamic import: the file sits in a "commonjs" package, so resolve the export defensively.
const routes = await import('../datasets-api/src/routes/marketplace-v2.ts');
const registerMarketplaceV2Routes = routes.registerMarketplaceV2Routes
  ?? routes.default?.registerMarketplaceV2Routes;
if (!registerMarketplaceV2Routes) throw new Error('marketplace-v2.ts: no registerMarketplaceV2Routes export');
registerMarketplaceV2Routes(app);

// movement LM artifacts (wf-motion-lm-1): the exact files the dashboard and capture tools use
const motionFile = (name) => {
  const p = new URL(name, ROOT);
  if (!fs.existsSync(fileURLToPath(p))) return null;
  return fs.readFileSync(fileURLToPath(p));
};
for (const [route, path, type] of [
  ['/v2/motion/model', 'site/earth/data/motion/model.json', 'application/json'],
  ['/v2/motion/samples', 'site/earth/data/motion/samples.json', 'application/json'],
  ['/v2/motion/corpus-stats', 'earth/motion/corpus/corpus-stats.json', 'application/json'],
]) {
  app.get(route, (c) => {
    const data = motionFile(path);
    return data ? new Response(data, { headers: { 'content-type': type, 'cache-control': 'public, max-age=300' } })
      : c.json({ error: 'artifact_missing', path }, 503);
  });
}

// --- RP1 worlds registry + Sneeze / WorldForge engine ----------------------
// Source of truth is on disk, parsed once at boot:
//   site/earth/worlds.json                        -> 544 world records (slug, place, lat/lon)
//   worldforge/out/<slug>/cards.json             -> world cards (anchor.rp1 = enter.rp1.com URL)
//   worldforge/out/<slug>/sneeze-mount-plan.json -> Sneeze SOM mount plans (the mounted set)
//   worldforge/out/assets/                       -> shared Sneeze assets (unit-cube.glb, ...)
//   worldforge/out/<slug>/<slug>.glb             -> per-world preview GLB
const readJson = (rel) => JSON.parse(fs.readFileSync(fileURLToPath(new URL(rel, ROOT)), 'utf8'));

let WORLDS = [];
try { WORLDS = readJson('site/earth/worlds.json'); } catch { /* registry absent: RP1 detail falls back to the card */ }
const worldsBySlug = new Map(WORLDS.map((w) => [w.slug, w]));

const OUT_DIR = fileURLToPath(new URL('worldforge/out/', ROOT));
const rp1Worlds = new Map(); // slug -> { world, card, plan, previewGlbPath }
if (fs.existsSync(OUT_DIR)) {
  for (const entry of fs.readdirSync(OUT_DIR, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const slug = entry.name;
    const cardFile = path.join(OUT_DIR, slug, 'cards.json');
    const planFile = path.join(OUT_DIR, slug, 'sneeze-mount-plan.json');
    if (!fs.existsSync(cardFile) || !fs.existsSync(planFile)) continue;
    try {
      const cardDoc = JSON.parse(fs.readFileSync(cardFile, 'utf8'));
      const plan = JSON.parse(fs.readFileSync(planFile, 'utf8'));
      const cards = Array.isArray(cardDoc) ? cardDoc : (cardDoc.cards || [cardDoc]);
      const card = (Array.isArray(cards) ? cards : [cards]).find((x) => String(x?.cardId || '').startsWith('world:')) || cards[0];
      let previewAbs = null;
      if (plan.previewGlb?.path) {
        const cand = fileURLToPath(new URL(plan.previewGlb.path, ROOT));
        if (fs.existsSync(cand)) previewAbs = cand;
      }
      rp1Worlds.set(slug, { world: worldsBySlug.get(slug) || null, card, plan, previewGlbPath: previewAbs });
    } catch { /* malformed card/plan pair: skip this world rather than fail the boot */ }
  }
}

// RP1 anchoring: a world is "bound" once a steward writes its location (anchor.lat/lon)
// and rp1.com issues the entry URL (enter.rp1.com?start_cid=553&lat=..&lon=..&rad=..).
const rp1Entry = (card) => {
  const a = card?.anchor;
  if (!a) return { status: 'unbound', url: null, lat: null, lon: null, rad: null };
  if (a.rp1) return { status: 'bound', url: a.rp1, lat: a.lat, lon: a.lon, rad: a.rad };
  if (a.lat !== null && a.lat !== undefined) {
    return {
      status: 'bound-latlon',
      url: `https://enter.rp1.com?start_cid=553&lat=${a.lat}&lon=${a.lon}&rad=${a.rad ?? 6371000}`,
      lat: a.lat, lon: a.lon, rad: a.rad,
    };
  }
  return { status: 'unbound', url: null, lat: null, lon: null, rad: null };
};

const rp1Summary = (slug, origin) => {
  const e = rp1Worlds.get(slug) || null;                 // mounted set: cards + Sneeze mount plan
  const w = (e && e.world) || worldsBySlug.get(slug) || {};
  const base = {
    slug,
    mounted: !!e,
    name: w.name || (e && e.card?.displayName) || slug,
    place: w.place || null,
    biome: w.biome || null,
  };
  if (!e) {
    // registered from the world record's real-Earth place; the Sneeze mount plan is not built yet
    return {
      ...base,
      lat: w.lat ?? null,
      lon: w.lon ?? null,
      rp1: (w.lat != null && w.lon != null)
        ? { status: 'registered', url: `https://enter.rp1.com?start_cid=553&lat=${w.lat}&lon=${w.lon}&rad=6371000` }
        : { status: 'unbound', url: null },
      sneeze: { engine: 'Sneeze', mounted: false, status: 'mount-plan-pending', planUrl: null },
    };
  }
  const rp1 = rp1Entry(e.card);
  const extent = e.plan.coordinateFrame?.extentXZ || [0, 0];
  return {
    ...base,
    lat: rp1.lat ?? w.lat ?? null,
    lon: rp1.lon ?? w.lon ?? null,
    rp1: {
      status: rp1.status,
      url: rp1.url,
      ...(rp1.url ? {} : { enterTemplate: 'https://enter.rp1.com?start_cid=553&lat=<LAT>&lon=<LON>&rad=6371000 (written by a steward via the card anchor)' }),
    },
    sneeze: {
      engine: e.plan.engine,
      schemaVersion: e.plan.schemaVersion,
      bindingStatus: e.plan.bindingStatus,
      nodes: Array.isArray(e.plan.nodes) ? e.plan.nodes.length : 0,
      d3Max: Math.max(0, ...extent.map((x) => Math.abs(x))),
      planUrl: `${origin}/v2/sneeze/plans/${slug}`,
      ...(e.previewGlbPath ? { previewGlbUrl: `${origin}/v2/worlds/${slug}/preview.glb` } : {}),
    },
  };
};

// Range-aware file serving (GLBs are streamed, not buffered).
const MIME = { '.glb': 'model/gltf-binary', '.json': 'application/json', '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.ktx2': 'image/ktx2' };
const serveFile = (c, absPath) => {
  let stat;
  try { stat = fs.statSync(absPath); } catch { return c.json({ error: 'not_found', path: path.basename(absPath) }, 404); }
  if (!stat.isFile()) return c.json({ error: 'not_found' }, 404);
  const type = MIME[path.extname(absPath).toLowerCase()] || 'application/octet-stream';
  const base = { 'content-type': type, 'accept-ranges': 'bytes', 'cache-control': 'public, max-age=300' };
  const range = c.req.header('range');
  const m = range && /^bytes=(\d*)-(\d*)$/.exec(range.trim());
  if (m) {
    const start = m[1] ? Number(m[1]) : 0;
    const end = m[2] ? Math.min(Number(m[2]), stat.size - 1) : stat.size - 1;
    if (start >= stat.size || start > end) return new Response(null, { status: 416, headers: { 'content-range': `bytes */${stat.size}`, ...base } });
    return new Response(Readable.toWeb(fs.createReadStream(absPath, { start, end })), {
      status: 206,
      headers: { ...base, 'content-range': `bytes ${start}-${end}/${stat.size}`, 'content-length': String(end - start + 1) },
    });
  }
  return new Response(Readable.toWeb(fs.createReadStream(absPath)), { headers: { ...base, 'content-length': String(stat.size) } });
};

app.get('/', (c) => c.json({
  service: 'worldforge-api',
  host: 'fly.io',
  routes: ['/', '/health', '/v2/rp1/worlds', '/v2/rp1/worlds/:slug', '/v2/sneeze/plans', '/v2/sneeze/plans/:slug', '/v2/sneeze/assets/*', '/v2/worlds/:slug/preview.glb', '/v2/marketplace/projects', '/v2/motion/model'],
}));

app.get('/v2/rp1/worlds', (c) => {
  const origin = new URL(c.req.url).origin;
  const mounted = [...rp1Worlds.keys()].sort().map((slug) => rp1Summary(slug, origin));
  const mountedSlugs = new Set(rp1Worlds.keys());
  const pending = WORLDS.filter((w) => !mountedSlugs.has(w.slug))
    .map((w) => rp1Summary(w.slug, origin))
    .sort((a, b) => (a.slug < b.slug ? -1 : 1));
  const worlds = [...mounted, ...pending];
  const registered = worlds.filter((x) => x.rp1.url).length;
  return c.json({
    engine: 'worldforge-sneeze',
    total: worlds.length,
    mounted: mounted.length,
    mountPlanPending: pending.length,
    registered,
    unbound: worlds.length - registered,
    note: 'registered = an enter.rp1.com link exists; mounted = Sneeze SOM mount plan built (worldforge/out/<slug>); mount-plan-pending = registered from the world record, plan not built yet',
    worlds,
  }, 200, { 'cache-control': 'public, max-age=300' });
});

app.get('/v2/rp1/worlds/:slug', (c) => {
  const slug = c.req.param('slug');
  const e = rp1Worlds.get(slug);
  const w = worldsBySlug.get(slug);
  if (!e && !w) return c.json({ error: 'unknown_world', slug, hint: 'GET /v2/rp1/worlds for the full registry' }, 404);
  const origin = new URL(c.req.url).origin;
  if (e) return c.json({ ...rp1Summary(slug, origin), world: e.world, card: e.card }, 200, { 'cache-control': 'public, max-age=300' });
  return c.json({
    ...rp1Summary(slug, origin),
    world: w,
    card: null,
    note: 'registered from the world record (site/earth/worlds.json); the Sneeze mount plan is pending the worldforge build',
  }, 200, { 'cache-control': 'public, max-age=300' });
});

app.get('/v2/sneeze/plans', (c) => {
  const origin = new URL(c.req.url).origin;
  const plans = [...rp1Worlds.keys()].sort().map((slug) => {
    const p = rp1Worlds.get(slug).plan;
    return {
      slug,
      rootCardId: p.rootCardId,
      mountParent: p.mountParent,
      bindingStatus: p.bindingStatus,
      schemaVersion: p.schemaVersion,
      nodes: Array.isArray(p.nodes) ? p.nodes.length : 0,
      url: `${origin}/v2/sneeze/plans/${slug}`,
    };
  });
  return c.json({ engine: 'Sneeze', total: plans.length, plans }, 200, { 'cache-control': 'public, max-age=300' });
});

app.get('/v2/sneeze/plans/:slug', (c) => {
  const e = rp1Worlds.get(c.req.param('slug'));
  if (!e) return c.json({ error: 'unknown_plan', slug: c.req.param('slug'), hint: 'GET /v2/sneeze/plans' }, 404);
  const origin = new URL(c.req.url).origin;
  const plan = JSON.parse(JSON.stringify(e.plan));
  if (Array.isArray(plan.assets)) {
    for (const a of plan.assets) {
      // dev plans point at a local 8789 server; rewrite to this deployment so plans are fetchable in production
      if (typeof a.url === 'string' && /127\.0\.0\.1|localhost/.test(a.url)) {
        a.url = `${origin}/v2/sneeze/assets/${path.basename(a.localPath || a.url)}`;
        a.servedFrom = 'worldforge-api';
      }
    }
  }
  return c.json(plan, 200, { 'cache-control': 'public, max-age=300' });
});

app.get('/v2/sneeze/assets/*', (c) => {
  const rest = c.req.path.replace(/^\/v2\/sneeze\/assets\//, '');
  const baseDir = path.resolve(OUT_DIR, 'assets');
  const abs = path.resolve(baseDir, rest || '');
  if (!abs.startsWith(baseDir + path.sep)) return c.json({ error: 'forbidden' }, 403);
  return serveFile(c, abs);
});

app.get('/v2/worlds/:slug/preview.glb', (c) => {
  const e = rp1Worlds.get(c.req.param('slug'));
  if (!e || !e.previewGlbPath) return c.json({ error: 'preview_missing', slug: c.req.param('slug') }, 404);
  return serveFile(c, e.previewGlbPath);
});

app.notFound((c) => c.json({ error: 'not_found', hint: 'GET /, /v2/rp1/worlds, /v2/sneeze/plans, /v2/marketplace/projects, /v2/motion/model' }, 404));



http.createServer(async (req, res) => {
  // Fly terminates TLS: honor x-forwarded-proto so route-generated URLs (plan asset rewrites,
  // registry links) come out as https://worldforge-api.fly.dev, not http://
  const proto = req.headers['x-forwarded-proto'] || 'http';
  const url = `${proto}://${req.headers.host || 'localhost'}${req.url}`;
  const init = { method: req.method, headers: req.headers };
  if (!['GET', 'HEAD'].includes(req.method)) init.body = req;        // stream request body through
  try {
    const resp = await app.fetch(new Request(url, init));
    res.writeHead(resp.status, Object.fromEntries(resp.headers));
    if (resp.body) for await (const chunk of resp.body) res.write(chunk);
    res.end();
  } catch (e) {
    res.writeHead(500, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ error: 'internal', message: String(e.message || e) }));
  }
}).listen(PORT, () => console.log(`worldforge-api listening on :${PORT} (marketplace v2 + movement LM + ${rp1Worlds.size} mounted RP1/Sneeze worlds of ${WORLDS.length} registered)`));
