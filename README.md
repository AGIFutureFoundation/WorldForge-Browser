# WorldForge-Browser

**The SmartCiti.X world builder, in the browser.** WorldForge turns the 41 AGI Corp "coming soon" worlds into
walkable 3-D scenes: GLEWME Master Cards, card-tagged glTF worlds, agent avatars, civic landmarks, lessons and
Omega Steward personas. You can open all of it from a static site, with no build step and no backend.

*Agents operate; people govern. Powered by AGI Corp. Owned by AGI Future Foundation PBC.*

## Open it

```bash
python3 -m http.server 8094 --directory site
# then open http://127.0.0.1:8094/
```

| Page | What it is |
|---|---|
| [`site/index.html`](site/index.html) | Landing page |
| [`site/worldforge/viewer.html`](site/worldforge/viewer.html) | **World builder viewer.** Walk any world (`?world=locator-x`), with Master Cards, buildings, avatars and landmarks in three.js |
| [`site/consoles/worldforge/`](site/consoles/worldforge/) | WorldForge console: every world's cards, rights, avatars and voice lines on one page |
| [`site/worldforge/out/overview/`](site/worldforge/out/overview/) | One overview per world |
| [`site/worldforge/whitepaper/out/index.html`](site/worldforge/whitepaper/out/index.html) | WorldForge whitepaper: features, roadmap, stack |
| [`site/worldforge/review/out/whitepaper.html`](site/worldforge/review/out/whitepaper.html) | Review round whitepaper, with film and captions |
| [`site/agents/teams.html`](site/agents/teams.html) | Agent teams per world |

The viewer loads `three@0.160.0` from cdn.jsdelivr.net, so it needs internet access.

## What each world contains (`site/worldforge/out/<slug>/`)

| File | What it is |
|---|---|
| `cards.json` | GLEWME Master Cards: world → plaza, Alignment Evaluation Gate, Steward Council (3 human seats, all empty), zones → agent avatars. Each card has an owner, a **Volum** (its bounded 3-D region) and a permission matrix (`view, enter, build, operate, delegate, transfer, govern`). |
| `<slug>.glb` | glTF 2.0. Every node carries `cardId`/`parentCardId` in its extras. |
| `blockout.generated.json` | The deterministic, synthetic generated core: zones, primitives and roads in metres. |
| `sneeze-mount-plan.json` | Ordered RP1/Sneeze Scene Object Model node specs, parents first. Names are ASCII, ≤ 47 units. |
| `manifest.json` | File hashes, counts, eval results and gate status. |

Shared folders: `out/avatars/` (447 agent avatars bound to their cards), `out/assets/landmarks/` (41 civic
landmarks, served as LOD1), `out/training/` (draft lessons per world), `out/onchain/` (draft ERC-721 metadata and
Merkle proofs).

**Governance rules:** agents may view, enter and operate only their own zone. `delegate` belongs to stewards.
`transfer` and `govern`, plus the PBC's reserved actions, need a 2-of-3 human steward quorum.

## SmartCiti.X Holodeck in RP1 (`rp1/`)

[`rp1/`](rp1/) contains the RP1 / Metaversal spatial-fabric installers for the SmartCiti.X Holodeck:
- the whole scene, `smartciti-holodeck` (227 objects, 170 models), or
- its two parts, `holodeck-simulator-yard` and `holodeck-robotics-wing`.

Install one or the other, never both. Each folder has an `install_scene.js` with a `DRY=1` dry run. See
[`rp1/README.md`](rp1/README.md) for the steps.

## Honest status

- Every world is **coming soon**. Omega Stewards are *defined, not seated*. Lessons are drafts, and none are certified.
- The onchain Master Cards are **draft metadata: not deployed, not minted.**
- Voice lines are synthetic (local Kokoro). Lines not yet rendered fall back to a labelled browser voice.
- Native RP1/Sneeze load is still open. The mount plans are prepared, not mounted.
- Known links that leave this site (they point to pages in the source monorepo): `agents/teams.html` →
  `my-fabric/viewer.html`, and the console's Hive links.

## Check it

```bash
node tools/check_site.mjs    # every manifest file present with its recorded size, every relative link resolves,
                             # no credential-shaped string or local path ships. Exit 1 on any failure.
```

CI runs the same check on every push and pull request (`.github/workflows/ci.yml`).

## Deploy

- **GitHub Pages:** in Settings → Pages → Source, choose **GitHub Actions** (an admin has to do this once). Then run
  the *pages* workflow from the Actions tab. It publishes `site/` as is.
- **Cloudflare Pages:** `npx wrangler pages deploy` (see `wrangler.toml` and [`tools/DEPLOY.md`](tools/DEPLOY.md),
  including how to put the site behind Cloudflare Access if it shouldn't be public yet).

## Where it comes from

`site/` is the output of `tools/build_site.py`, run in the SmartCiti.X worlds monorepo. It copies files
byte-for-byte and rewrites nothing. The script expects that repository layout and is kept here for provenance.
The Trade Craft Academy itself lives in [AGIFutureFoundation/SmartCiti.X](https://github.com/AGIFutureFoundation/SmartCiti.X),
and the onchain agent layer in [AGIFutureFoundation/Metropolis-SmartCiti](https://github.com/AGIFutureFoundation/Metropolis-SmartCiti).

## License

MIT, see [LICENSE](LICENSE).
