// server.mjs -- WorldForge API on Fly.io. A long-running Node service that mounts the SAME
// marketplace-v2 route file the Cloudflare Worker uses (cloud/datasets-api/src/routes/
// marketplace-v2.ts, via Node native type-stripping) and serves the Movement LM artifacts.
// Token handling: FLY_API_TOKEN is read from the environment or the gitignored .env at repo
// root -- never from this file (deploy.sh wires it; the GitHub workflow uses a repo secret).
import http from 'node:http';
import fs from 'node:fs';
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

app.notFound((c) => c.json({ error: 'not_found', hint: 'GET /health, /v2/marketplace/projects, /v2/motion/model' }, 404));

http.createServer(async (req, res) => {
  const url = `http://${req.headers.host || 'localhost'}${req.url}`;
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
}).listen(PORT, () => console.log(`worldforge-api listening on :${PORT} (marketplace v2 + movement LM artifacts)`));
