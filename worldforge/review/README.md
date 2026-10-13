# WorldForge review: a film and a whitepaper every 45 minutes

This is the review pipeline for the WorldForge lane. It is separate from the atlas review film in `atlas/` and `pitch/`.
In each 45-minute round the lead updates one file and runs two commands. The output is a 120-second review film and a
pitch-deck-style whitepaper. Both are built from the registries, so every number on them can be traced to a file.

```bash
# 0. the lead overwrites worldforge/review/round.json (schema: round.template.json)
node worldforge/review/record.mjs                    # 1. 3D clips through worldforge/viewer.html (headless Chrome)
python3 worldforge/review/build_review.py            # 2. film + captions + whitepaper + media + build.json
python3 worldforge/review/build_review.py --check    # heartbeat check: one line, exit 1 when stale
```

Prerequisites:

- The static server must be running on `http://127.0.0.1:8080` and serving the repo root.
- Google Chrome.
- The working ffmpeg at `.cache/bin/ffmpeg`. You can override it with `FFMPEG=`.
- For narration, macOS `say`. Inside the Claude Code sandbox `say -o` writes a header-only file, so the build
  detects this and produces a silent film with burned-in captions. Run the build outside the sandbox to get narration.

## What a round does

1. **`round.json`** (the lead writes it): `{n, date, window, headline, landed[], doing[], next[], gates[], worlds?[], modes?[]}`.
   - `worlds` defaults to `locator-x, cancer-dao, s29-metaverse-dao`.
   - `modes` defaults to `flyin, building, omega, orbit`.
   - `gates[]` items can be strings or `{name, status}`.
   - A file that still contains `TODO by lead`, or that sets `"placeholder": true`, is shown as a placeholder on the film and on the page.
2. **`record.mjs`**:
   - Opens `worldforge/viewer.html?world=<slug>&hud=0&tour=1` for each world and waits for `window.__wfReady`.
   - Calls `window.__wfShot(mode, k/(N-1))` for each frame and captures it with `Page.captureScreenshot`. It captures 12 fps for 5 s, so each clip is 60 frames.
   - Encodes each clip at 24 fps (libx264, yuv420p, 960x540) to `out/clips/<slug>-<mode>.mp4`.
   - Writes `out/clips/index.json` with the round number the clips belong to.
   - If the viewer has no `__wfShot`, or any shot fails to return `true`, it exits 1 with one line. It never fakes frames.
   - A missing contract fails fast and is not retried. Before Chrome starts, it fetches `viewer.html` from the server. It exits 1 at once if the server is unreachable, if the page is not served, or if the source names neither `__wfReady` nor `__wfShot`. It also exits 1, once, if the page is still without `window.__wfReady` `READY_GRACE_S` seconds (default 60) after it loads. The grace allows for the viewer warming three.js from the CDN before its module runs. A world that defines `__wfReady` but never sets it to true gets `READY_S` seconds (default 120) and `ATTEMPTS` tries.
   - Clips are tagged limited-range BT.709 (`yuv420p(tv, bt709)`). The build warns when a clip on disk is not, for example one recorded by an older `record.mjs`.
   - It deletes the previous clips only after the contract has been confirmed.
   - Flags: `--worlds a,b --modes orbit,flyin --seconds 5`. Env: `CDP_PORT` (default 9347), `WF_BASE`, `FPS`, `ATTEMPTS` (default 3).
   - If Chrome crashes mid-run (software WebGL under heavy load), it relaunches Chrome and retries that world up to `ATTEMPTS` times.
   - `--resume`: use it after an interrupted run in the same round. It keeps the finished clips on disk and records only the missing ones.
3. **`build_review.py`**:
   - **Film** `out/review-film.mp4`: 960x540, 24 fps, exactly 2880 frames. The duration is probed and must be 118-122 s, or the build fails. Sections:

     | Section | Length | Content |
     |---|---|---|
     | Title | 8 s | `WorldForge Review <n> · <window>`, Powered by AGI Corp |
     | Landed | 18 s | `landed[:6]` |
     | 3D | 60 s | This round's clips, with lower thirds naming the world and what is shown |
     | By the numbers | 14 s | Registry counts |
     | Next + gates | 14 s | `next[:4]` and the gates |
     | End card | 6 s | What is not claimed |

     If this round has no clips, the 3D section uses `worldforge/out/stills/*.jpg` with a slow Ken Burns pan. If there are fewer than 3 stills, plan views drawn from each world's `blockout.generated.json` are added. Either way the screen says that 3D clips were not recorded this round.
   - **Narration**: one line per section, read by the macOS system voice (Samantha) and mixed in with ffmpeg. The title line says the voice is synthetic, and the end card labels it as synthetic. If `say` produces no audio (the sandbox, or not macOS), the film is silent: the narration lines are burned in as captions, and the title line and end card say the film is silent.
   - **Captions** `out/review.vtt`: a cue for each section line and a cue for each 3D item. Every 3D cue starts with the world's name.
     - The captions belong to the film. When the film is cut, its cues are stored in `build.json` (`film.captions`).
     - `--no-film` and `--check` render the VTT from those stored cues, never from the current registries. So the caption track always matches the film's picture and narration.
   - **Stills fallback**: each still is labelled by its file name only.
     - A world is named only when the file name starts with that world's slug (`<slug>-<mode>.jpg`).
     - `viewer-<mode>.jpg` is labelled as a viewer still with no world named.
     - Any other still, for example `console.jpg`, is labelled by its path.
     - The narration names worlds only for stills whose file name names them.
   - **Whitepaper** `out/whitepaper.html`: 12 full-width 16:9 slides:
     1. Cover
     2. Problem
     3. Cards, Volum and permissions
     4. Worlds (41 plan thumbnails)
     5. Buildings
     6. Avatars: avatars and bindings counted on every card kind that carries them (agent, coordinator, advisor, omega and any later kind), avatar-registry totals, and the avatar GLBs' Khronos validator results (`worldforge/out/assets/avatars/validation.json`, counted only where the sha256 still matches)
     7. Omega Hive
     8. Governance
     9. Evidence (including the heartbeat beat)
     10. Roadmap gates
     11. Review `<n>`, with the embedded film and captions
     12. The ask, with contact `x@agifuturefoundation.org` and the disclaimer

     The card-kind breakdown on slide 3 lists every kind in the cards. The build fails if the kinds do not add up to `totals.cards` in `worldforge/out/index.json` (for example, while `worldforge/out` is mid-rebuild). If the film was cut from an earlier registry state than the page (after a `--no-film` rebuild, its `plan_sha` differs), the Review slide says that the film's numbers can trail the page.

     The theme is dark by default with a light toggle. The toggle sits outside the scrolling nav, so it stays on screen at phone width. The page is safe at phone width, and all links are relative, so `out/` can be published as an Artifact with its files: `review-film.mp4`, `review.vtt`, `media/*`.
   - **`out/build.json`**: the round, film facts (seconds, narration, which 3D source was used, plan hash) and the pinned values described below. It contains no timestamps.
4. **`--check`**:
   - Rebuilds the whitepaper, the captions, the poster and the plan PNGs in memory and compares them byte for byte with the files on disk.
   - Confirms that the film exists, runs 118-122 s and was built for the current round. The film is a build artifact, so registry counts that move between rounds do not make it stale. `build.json` keeps a `plan_sha` for anyone who wants a stricter comparison.
   - Prints `worldforge review current (round <n>, film <s>s)` or `worldforge review STALE (round <n>): <reasons>`.

**Pinned values.** Two of the cited values change between rounds without the review itself changing: the heartbeat
log gains a line every beat, and the hive voices more lines while a round runs. The build pins the beat line and the
voiced-line count in `build.json`, and the page says the count is "when this page was built". `--check` rebuilds with
the pinned values. It reports STALE only if the pinned beat line has gone from `evidence/heartbeat.log` or the voiced
count has fallen. Every other registry change (cards, spaces, avatars, evals, gates) makes the check report STALE
until the build is run again. `--no-film` refreshes the page and media in a few seconds without re-rendering the film.
It leaves the film's captions as they were cut.

## Honesty rules the build enforces

- Every number is read at build time. Each slide names its sources:
  - `worldforge/out/index.json` and `worldforge/out/*/cards.json`
  - `worldforge/out/avatars/index.json` (when present)
  - `worldforge/out/assets/avatars/index.json` and `validation.json` (when present)
  - `my-fabric/worlds/spaces_index.json`
  - `agents/hive/index.json`
  - `evidence/heartbeat.log`
  - `atlas/roadmap.json` (founder gates)
  - `worlds/generated/teams/*.json` (brand hue and mark)
- The build fails (`worldforge review FAILED: ...`) if the page or captions would contain the private repository
  name, an email address other than the contact address, a wallet-like address or a key-like string.
- Omega Stewards are shown as *defined, not seated*, and human seats as empty. The six reserved actions are listed
  verbatim as held for the 2-of-3 Steward Council.
- What is not done is stated on the end card and on the Evidence slide: Sneeze gates not done, voices voiced N of
  176, avatar models present or not, and which 3D source was used.

## Files and git

| Path | Committed? |
|---|---|
| `build_review.py`, `record.mjs`, `round.json`, `round.template.json`, `README.md`, `.gitignore` | yes |
| `out/whitepaper.html`, `out/review.vtt`, `out/build.json`, `out/media/*` (poster, plan PNGs, copied stills, clip frames) | yes (small) |
| `out/review-film.mp4` | **no** (gitignored: `out/*.mp4`) |
| `out/clips/` (recorded clips and their index) | **no** (gitignored) |
| `out/tmp/` | **no** (gitignored; the build itself works in `$TMPDIR`) |

Because the film is not committed, a fresh checkout reports `--check` STALE ("review-film.mp4 missing") until the
build runs.
