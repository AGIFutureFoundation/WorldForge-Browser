# SMARTCITI-STYLE.md — the PS2-era look for SmartCiti environments

Canonical spec. Any SmartCiti environment (new world, VR yard, holodeck export, training page)
inherits this look by default. Reference implementation: `site/earth/js/ps2.js` (material pass)
+ `site/earth/js/core.js` `makeStage()` (renderer settings). Validation:
`earth/ps2_check.mjs` (state + screenshots), `earth/ps2_probe.mjs` (stats + fps),
`earth/ps2_hist.mjs` (luminance histogram). Copies of this spec travel into SmartCiti.X and
VR-BAC-Yard when those trees are touched.

The goal is **era-authentic but polished** — a deliberate 2000s console aesthetic, never a
degraded modern render. Every rule below has an escape hatch: `?modern=1` restores the
full-fidelity renderer on the earth viewer.

## Renderer

| Setting | Value | Why |
|---|---|---|
| Internal resolution | `devicePixelRatio × 0.42` (floor 0.35) | ~PS2-class framebuffer, upscaled |
| Upscale | `canvas.style.imageRendering = 'pixelated'` | chunky texels, never blurry |
| Antialiasing | OFF in era mode | jagged edges are the look |
| Tone mapping | ACES, exposure **0.88** (era) vs 0.55 (modern) | Lambert is flat; lift to keep mid-tones |
| Shadows | `BasicShadowMap`, 1024² | hard-edged blob shadows, era signature |
| Draw distance | camera far **4800** (vs 9000) | the console had to cheat |
| Fog | `Fog(0xb4d0ea, 420, 2300)` (vs 900–3200) | close pop-in fog hides the horizon cutoff |
| Grading | CSS filter `saturate(1.14) contrast(1.07) sepia(0.05)` | composite-video color push |
| CRT overlay | fixed div: 1px scanlines + radial vignette, `pointer-events:none` | sits over the viewport, never input |

## Materials & textures

- **Lighting model: per-vertex (Gouraud).** `MeshStandardMaterial`/`MeshPhysicalMaterial` →
  `MeshLambertMaterial` at load (`ps2ify()`). No metalness/roughness sheen, no envmaps.
- **Texture page ceiling: 512px.** Nothing larger ships to the GPU: oversized maps are
  downscaled to 512 max-dimension at load (the 2048² satellite drape becomes 512², 4.3MP→0.36MP).
  256px is the typical page; 512 is for hero surfaces only.
- **Filtering: `NearestFilter` mag**, anisotropy **1** (PS2s had none). Bilinear min is fine.
- **Polygons:** low-poly meshes, merged draw calls. OSM footprints extruded as boxes with
  procedural facade textures (256×128 canvas pages) are the reference building treatment.
- Hemisphere ambient **1.35** + directional sun ~2.6 (era mode): bright enough that facades and
  roofs read; guard with `ps2_hist.mjs` — dark-bin (0–31) share should stay **below the modern
  mode's**, never above.

## 2D pages (menus, HUDs, map UIs — the "console chrome")

- Palette: deep indigo panels `#0d1030`/`#1a1f4a`, border `#2c3670`, cyan titles `#4dd8ff`,
  amber XP `#ffd23f`, green confirm `#3ddc84`. Difficulty colors stay semantic
  (green/amber/red).
- Typography: bold Arial/Helvetica stack for UI, **`Courier New` mono for telemetry/data**,
  uppercase + letter-spacing on buttons and labels.
- Era signatures: hard 1px offset text-shadows (`1px 1px 0`, no blur), 3px bottom-border
  bevels on buttons, boxy radii (2–6px, not 16px). Functionality first: never skin over
  usability — contrast and hit targets stay as-is.

## GLB / holodeck exports (rp1 pipeline)

- Textures ≤512px, nearest-friendly (no subpixel detail that dies at 512), materials flattened
  to unlit/Lambert equivalents with baked vertex color, single material per mesh where possible.
- Validate the exported scene with the same checks; `?modern=1` does not exist for exported
  GLBs, so err on the light side of texture budgets.

## Do / don't

**Do:** keep world functionality untouched (agents, training logic, certifications, quests);
ship one commit per world; validate each converted world with the three earth/ scripts before
committing; report buffer size, swap count, texture MP before→after, and fps.

**Don't:** blur the upscale (linear filtering is the #1 era-killer); use PBR sheen, soft
shadows, or anisotropy; blow the 512 page ceiling; delete or dim UI to look "retro";
touch the `?modern=1` path; chase 60fps under SwiftShader — headless fps is a *regression
signal relative to modern mode* (era mode should be ≥1.5× faster), real GPUs are the target.

## Validation snapshot (2026-11-04, s12-parking-smart-x / nola-french-quarter)

| World | buffer | Lambert swaps | tex MP | era fps vs modern (SwiftShader) |
|---|---|---|---|---|
| s12-parking-smart-x | 430×268 | 188 | 4.29→0.36 | 1.4 vs 0.6 (2.3×) |
| nola-french-quarter | 430×268 | 121 | 4.19→0.26 | 2.5 vs 0.9 (2.8×) |
| ar-training (2D) | — | — | — | 60.1 fps, p95 16.8ms |
