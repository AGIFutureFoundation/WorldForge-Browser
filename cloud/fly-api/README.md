# worldforge-api (Fly.io)

Long-running Node/Hono service on Fly.io. It mounts the **same** `marketplace-v2.ts` route
file the Cloudflare Worker uses (single source of truth, Node 24 type-stripping) and serves:

## Routes

| Route | What |
|---|---|
| `GET /health` | liveness (Fly http_check) |
| `GET /v2/rp1/worlds` | RP1 worlds registry: 41 mounted worlds, `bound` (4 with live `enter.rp1.com` anchors) + `unbound` (37 awaiting steward-set locations) |
| `GET /v2/rp1/worlds/:slug` | world record + world card + RP1 entry URL + Sneeze summary |
| `GET /v2/sneeze/plans` | index of the 41 Sneeze SOM mount plans |
| `GET /v2/sneeze/plans/:slug` | full mount plan; asset URLs rewritten from the dev `127.0.0.1:8789` origin to this deployment |
| `GET /v2/sneeze/assets/*` | shared Sneeze assets (`unit-cube.glb`, avatars, LODs, landmarks) — Range-streamed |
| `GET /v2/worlds/:slug/preview.glb` | per-world preview GLB — Range-streamed |
| `GET /v2/marketplace/projects` | marketplace v2 (shared route file) |
| `GET /v2/motion/model` · `/samples` · `/corpus-stats` | wf-motion-lm-1 artifacts |

Data is loaded from disk at boot — no drift possible from `worldforge/out/` and
`site/earth/worlds.json`.

## Deploy

```bash
# token: flyctl auth login, then `flyctl tokens deploy -a worldforge-api`
#        put it in .env at repo root (gitignored) OR the GitHub secret FLY_API_TOKEN
bash cloud/fly-api/deploy.sh          # or push to main (workflow deploys when the secret exists)
curl https://worldforge-api.fly.dev/health
```

The repo-root `.dockerignore` keeps the build context ~155MB (repo is multi-GB on disk);
only the files the Dockerfile COPYs are shipped to the remote builder.

## Custom domain (optional)

```bash
flyctl certs add worlds.example.com   # then add the A/AAAA records Fly prints
```
