# Deploying the WorldForge site to Cloudflare Pages (founder steps)

`worldforge/site/build_site.py` assembles a static site in `worldforge/site/dist/` (gitignored): the WorldForge
viewer, the data and GLBs it loads, the WorldForge console, the review whitepaper and the WorldForge whitepaper.
Nothing has been deployed. No Cloudflare account, token or project is configured on this machine, and nothing in this
folder holds a credential.

## 1. Build and check locally

```bash
python3 worldforge/site/build_site.py --dry-run   # files, sizes, the 25 MiB / 20,000-file Pages limits, path mapping
python3 worldforge/site/build_site.py             # writes worldforge/site/dist/ (byte-identical copies, verified)
python3 worldforge/site/build_site.py --smoke     # serves dist/ on 127.0.0.1:8094 with _headers applied, tests it, stops
```

The site mirrors repository paths (`/worldforge/viewer.html`, `/worldforge/out/...`, `/my-fabric/worlds/models/...`,
`/worlds/generated/teams/...`, `/agents/hive/voices/...`) because the viewer resolves its data against its own folder
and the repository root. No page or data file is rewritten. The one substitution is reported on every build: when
`worldforge/out/assets/lod/index.json` exists, each landmark's LOD1 GLB is served at the LOD0 path the viewer requests.
To look at it in a browser, serve `dist/` (`python3 -m http.server 8094 --directory worldforge/site/dist`) and open
`http://127.0.0.1:8094/`. The viewer loads three.js from cdn.jsdelivr.net, so it needs internet access.

## 2. Decide who may see it first

**`wrangler pages deploy` publishes the site at a public `*.pages.dev` URL.** Anyone with the link can open it
unless Cloudflare Access protects it. Deciding to publish publicly is yours. To keep it private:

1. In the Cloudflare dashboard, open **Zero Trust > Access > Applications > Add an application > Self-hosted**.
2. Application domain: `<project>.pages.dev`, and add a second one for `*.<project>.pages.dev` so preview deployments
   are covered too. (Pages project > Settings > General > **Enable access policy** sets up the preview half for you.)
3. Add a policy: Action **Allow**, Include **Emails** with the addresses that may view it (or an email domain), and
   pick a login method (one-time PIN works with no identity provider).
4. Save, then open the URL in a private window: you should get the Access login page, not the site.

Set this up before the first deploy, or deploy and protect it at once, if the site must never be public.

## 3. Deploy

Run these yourself; the login opens your browser and keeps the session outside the repository:

```bash
npx wrangler login
python3 worldforge/site/build_site.py
npx wrangler pages deploy worldforge/site/dist --project-name <name>
```

Or from `worldforge/site/` with its `wrangler.toml` (`name` is the placeholder `smartciti-worldforge`;
`pages_build_output_dir = "dist"`): `cd worldforge/site && npx wrangler pages deploy`. The first deploy offers to create
the project. Never put an API token or account id in `wrangler.toml` or any file here. If CI ever deploys, keep the
token in the CI secret store.

## 4. Check the deployment

```bash
curl -sI https://<project>.pages.dev/worldforge/viewer.html | head -5
curl -sI https://<project>.pages.dev/worldforge/out/locator-x/locator-x.glb | grep -iE 'content-type|access-control|cache-control'
```

Expect `model/gltf-binary` with `Access-Control-Allow-Origin: *` for the GLB. `_headers` sets MIME types for
`.glb/.gltf/.wasm/.vtt/.mp4`, CORS for GLB/glTF/JSON, and cache-control (HTML and JSON revalidate; models and video cache a
day). The local smoke test applies these rules, but Cloudflare's own header merging should be confirmed with the curl
lines above. `_redirects` adds `/viewer`, `/console` and `/whitepaper`. With Access on, add `-H "cf-access-token: ..."`
or check in a logged-in browser instead.

## Known gaps on the deployed site

- The console's links to `../hive/` and `../../agents/teams.html` and its citation links (registry files such as
  `worlds/PBC.json`) point outside WorldForge and are not shipped, so they 404.
- Avatar voice lines that have not been rendered yet are absent. The viewer HEAD-checks each one and falls back to a
  labelled browser voice.
- With LOD1 substitution, the landmark panel shows the LOD0 byte, hash and triangle figures from
  `worldforge/out/assets/landmarks/index.json`.
