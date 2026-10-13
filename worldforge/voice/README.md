# WorldForge avatar voices

`voice_intros.py` speaks the avatar intro lines from `worldforge/out/avatars/index.json` with **Kokoro v1.0**
(kokoro-onnx 0.6.1, Apache-2.0), a free open-source text-to-speech model that runs locally from `.cache/voice/`.
Nothing is sent anywhere. No account, key or credits are involved. Every line is a **synthetic voice** reading a
scripted intro, and the intro text itself says so ("You are hearing a synthetic voice."). Rows whose intro does not
say it are skipped and reported. No line is spoken live by a model.

```sh
.cache/voice/venv/bin/python worldforge/voice/voice_intros.py           # render: resumable, time-boxed (35 min)
.cache/voice/venv/bin/python worldforge/voice/voice_intros.py --plan    # list what would be rendered; render nothing
python3 worldforge/voice/voice_intros.py --check                        # verify; plain python3, no Kokoro needed
```

Options: `--budget-min N` sets the wall-clock time box (default 35; sleeps count toward it), `--limit N` renders at
most N lines, and `--batch N` sets how many lines run between registry re-reads (default 10).

## Contract

- **Audio path:** `worldforge/out/voices/<world>/<last path segment of avatarId>.mp4`, for example
  `avatar:locator-x/specialist/forecast-agent` → `worldforge/out/voices/locator-x/forecast-agent.mp4`.
  The avatar registry stores only this expected path, never a voiced or exists flag (that would go stale). Viewers
  HEAD-check the path at runtime and use the browser speech fallback (`voice.browser_fallback`) when it is missing.
- **Format:** the hive's format. Mono AAC at 48 kbps and 24 kHz in an `.mp4` container (artifacts serve `.mp4`, not
  `.m4a`), with `+faststart`. Loudness is normalised by ffmpeg `loudnorm` in two passes: measure, then apply with
  `linear=true`, targeting -16 LUFS integrated and -1.5 dBTP. The script uses ffmpeg from `.cache/bin/ffmpeg`.
- **Voice:** the row's `voice.id` (a Kokoro voice such as `af_kore` or `bm_lewis`; en-gb for `bf_`/`bm_`, en-us
  otherwise), speed 1.0, with nothing prepended. The registry's `voice.speed` (0.92 to 1.08) is used only by the
  browser fallback.
- **Manifest:** `worldforge/out/voices/manifest.json` has the shape
  `{lines: [{avatarId, role, path, voice, seconds, text_sha256}], totals, engine: "Kokoro v1.0 (kokoro-onnx), local"}`.
  It lists only lines that were actually rendered, so a missing entry means not voiced. `seconds` is the duration in
  the mp4 movie header. `text_sha256` is the SHA-256 of the UTF-8 intro text. The file is deterministic: lines are
  sorted by path, there are no timestamps, and it is saved after every line.

## Scope and order

Order: the coordinators (41), then the first specialist of each world (41), then the advisors (host, liaison and
alignment rows, once worldforge/avatars.mjs writes them), then the remaining specialists. The registry is re-read
before every batch because another builder may be adding rows. Only rows whose intro text is present are voiced.

Omega rows are **not** voiced here. Their intro is the hive greet line, and the hive voices it
(`agents/hive_voice.py` → the row's `voice.audio.greet`).

## Resuming, stale lines, etiquette

- A line is skipped when its mp4 exists and its manifest entry has the same text hash, voice and path.
- An entry goes stale when its intro text or voice changes, or its row disappears. The entry is dropped and its mp4
  removed before re-rendering, so a viewer never plays an outdated line at the contract path.
- CPU: at most 2 threads. That is one Kokoro ONNX session with `intra_op_num_threads=2` and
  `inter_op_num_threads=1`, plus `ffmpeg -threads 1`.
- Before each line the script reads local time (as `date +%H:%M` would show it). Inside the other team's film render
  windows, 07:25–07:35 and 08:10–08:20, it sleeps until the window ends. If the time box would end inside a window,
  it stops cleanly instead.

## --check

`--check` verifies every manifest entry against the disk and the registry:

- its file exists;
- its mp4 duration matches `seconds` within 0.05 s;
- its text hash and voice still match the registry row;
- its path follows the contract;
- its intro still says the voice is synthetic.

It also rebuilds the manifest in memory from its own lines and compares the bytes (order, totals and format), and
flags any mp4 under `worldforge/out/voices/` that is not in the manifest (in-progress `.part.mp4` files are
ignored). It prints one final line,
`voices current: <n> of <m> intro lines voiced, <k> failing`, and exits 1 when k > 0. Here m counts the in-scope
intro lines in the registry right now.

## Not done

- No lip sync or visemes.
- No live or AI speech: the intro lines are scripted text.
- No omega audio (that is the hive's job).
- The time box may stop before every line is voiced. `--check` reports how many are.
- `worldforge/out/voices/` is not git-ignored, unlike `agents/hive/voices/`. Whether to commit the roughly 57 KB per
  line of audio is the lead's decision.
