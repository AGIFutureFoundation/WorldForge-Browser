# SmartCiti.X Agentic Worlds: whitepaper and two films

This folder builds a standalone whitepaper page and two 120-second films for SmartCiti.X, by AGI Future Foundation PBC
(Powered by AGI Corp). The page works both as a pitch deck and as an article. Every project number on it, and in the
films, is read from a registry file at build time, and the page names that file.

```bash
python3 worldforge/whitepaper/build_whitepaper.py            # page + both films + captions + posters + build.json
python3 worldforge/whitepaper/build_whitepaper.py --no-film  # page, media and build.json only (keeps the films already cut)
python3 worldforge/whitepaper/build_whitepaper.py --silent   # films without narration
python3 worldforge/whitepaper/build_whitepaper.py --check    # one line; exit 1 when stale

# options for a build (each is pinned in build.json, so --check rebuilds the same page)
#   --base-url https://<host>/<folder>/   absolute og:image, twitter:image, og:url, canonical and JSON-LD URLs (or WHITEPAPER_BASE_URL)
#   --contact-email ADDRESS               print a contact address on the page and the film end cards (or WHITEPAPER_CONTACT_EMAIL)
```

No contact address is printed unless one is passed: the founder decides whether an address is public. Without
`--base-url` the share kit says plainly that the social tags hold relative URLs and are not ready to share.

`--check` prints `whitepaper current: <sections> sections, <claims> cited market claims, films <a>s + <b>s`, or
`whitepaper STALE: <reasons>`. Besides rebuilding the page and comparing it, it checks that each film is 118-122 s, that
each `.vtt` matches the captions stored in `build.json`, and that every caption cue covers the measured span of its
spoken line.

## What you need

- Python 3 with Pillow.
- The working ffmpeg at `.cache/bin/ffmpeg`. You can override it with `FFMPEG=`.
- The recorded 3D clips in `worldforge/review/out/clips/` (`node worldforge/review/record.mjs`, plus the landmark
  clips from `worldforge/viewer/record_extra.mjs`).
- macOS `say` for narration. Inside the Claude Code sandbox, `say -o` writes a file with a header and no audio. The
  build detects this and cuts silent films with burned-in captions. To get narration, run the build outside the sandbox.
- Do not start film renders between 09:50 and 10:05 local time. The other team renders its films then.

## Inputs (read only)

| Input | What it gives |
|---|---|
| `content/market.json` | The fact-checked external claims (verdict `confirmed` or `corrected` only), the why/what/how narrative that cites them by id, and the caveats. The build fails if the narrative cites an id that is not kept. |
| `content/explainers-*.json` | The deep explainers written by the explainer agents: sections, facts with sources, visual hints, what is not done, glossary and FAQ. |
| `content/market.raw.json` | The research before fact-checking. Not read by the build. |
| Registries | `worldforge/out/**` (index, cards, manifests, avatars, assets, onchain, voices), `agents/swarms`, `agents/prompts`, `agents/hive`, `agents/ledger`, `my-fabric/worlds/{spaces,scenes}_index.json`, `worlds/PBC.json`, `atlas/roadmap.json`, `rp1/publish/manifest.json`, `worldforge/native/conformance-report.json`, `evidence/heartbeat.log` |
| `worldforge/review/build_review.py` | Drawing, ffmpeg and `say` helpers. Imported read-only, never edited. |

## Explainer facts are re-checked

Each explainer fact names its source. When that source is a JSON file followed by a plain pointer (for example
`worldforge/out/index.json#totals.evals`), the build re-reads it. The fact is then marked in one of three ways:

- **re-read**: the registry still holds that value.
- **now N**: the registry value has moved since the explainer was written. The section opens with a note that gives
  both values. A FAQ answer that quotes a moved number has the current value appended to it.
- **as read**: the build does not parse this source, so the value stands as the agent's reading of it.
- **from registry**: the value is written from the registry at build time (the voicing counts and where the avatars
  are mounted), because these move while voicing runs.

Where an explainer's source is not a plain pointer, `FACT_CHECK` in the builder supplies one (the beats logged, the GLB
sweep of the cited beat, the world GLB bytes, a plan's native name-limit flags), so a moved value shows as **now N**.

Sentences whose counts move as voicing proceeds (voiced intros, what is not voiced, dialogue lines spoken, the
"How much is actually voiced?" answer) are rebuilt from `worldforge/out/voices/manifest.json`,
`worldforge/out/avatars/index.json`, `agents/hive/index.json` and `agents/hive/dialogues.json` (`TEXT_FIXES`). The
section says so, and the explainer's earlier wording is kept in `build.json` under `rebuilt`. Otherwise the prose keeps
the explainer's wording, and the registry value is shown beside it, never silently swapped in.

## Lines qualified on this page

`atlas/roadmap.json` belongs to another team. Where its wording overstates what is done, the page and Film 2 show a
qualified line and the page quotes the roadmap's own wording under the table (`build.json` `page_qualifiers`): the
"management teams seated by each company's own agents" item (no agent is seated), the "2-of-3 signed steward votes"
item (signed with throwaway test keys; no steward is seated), and the Artemis row (only the fabrics with a log in
`evidence/artemis-*.log` have been load-tested). When the roadmap owner fixes the source, the qualifier stops applying.

## Outputs (`out/`)

| File | Committed? |
|---|---|
| `index.html` | yes |
| `film-features.vtt`, `film-roadmap-stack.vtt` | yes |
| `media/*`: posters, stills, previews and clip frames | yes |
| `build.json`: the numbers used and their sources, the claim ids with footnote numbers, film facts (seconds, narration lines, captions, clips), the pinned heartbeat beat and date, and the explainer-fact check summary | yes |
| `film-features.mp4`, `film-roadmap-stack.mp4` | **no** (gitignored) |

The page links everything relatively, so `out/` can be served or published as a folder. The host must serve `.vtt`
files as `text/vtt` (Firefox ignores caption tracks sent as `application/octet-stream`) and must answer byte-range
requests for the `.mp4` files with `206 Partial Content` (Safari will not play MP4 without them). The local static
server on port 8080 does neither, so check captions and playback on the real host before announcing the page.

## The page

- **SEO**: `<title>` of 60 characters or fewer, a meta description of 155 or fewer, keywords, robots, Open Graph,
  a Twitter card, and a JSON-LD `@graph` (Organization, TechArticle, two VideoObjects, and an FAQPage built from the
  visible FAQ). The canonical link, `og:url` and absolute image and video URLs are written only when `--base-url` is
  given; otherwise a comment in `<head>` and the share kit say so. No domain is assumed.
- **Accessibility**: the light theme's accent, gold and green meet WCAG AA (4.5:1) on every surface they sit on,
  including the tinted slides. Below 640 px the inline SVG diagrams keep their full width in a box that scrolls
  sideways, so labels stay at least 12 px. Images carry width and height. The section nav fades at its edge while more
  links are off screen.
- **Order**: Hero and key numbers, Film 1, Why, What, How, the deep explainers (each with facts, a visual and what is
  not done), Film 2, the stack diagram (inline SVG that follows the theme), the roadmap with its human gates, the
  market table, what we do not claim, the FAQ, the glossary, sources (market sources numbered as cited, then the
  registries), the search and share kit, and contact.
- **Design**: dark by default, with a light theme and a toggle. Safe at phone width. No external scripts.

## The films (960×540, 24 fps, 120 s ±2, probed)

- **Features**: title 6 s, world network 14 s, recorded walkthrough 54 s (nine clips: Cancer DAO fly-in, building,
  Omega, council, landmark and orbit, then Locator.X and Metaverse DAO, each with a lower third), avatars 12 s, Omega
  Hive 12 s, governance 12 s, end card 10 s.
- **Roadmap and stack**: title 6 s, the six stack layers 40 s, evidence 14 s, the roadmap phases with their human gates
  plus the WorldForge gates 40 s, next steps 10 s, end card 10 s.
- Each section has a narration line, and each walkthrough clip, stack layer and roadmap step has its own short line,
  read by the macOS voice Samantha. The title and the end card both label it as synthetic. Every line is synthesised
  before the cut, so its caption cue is timed to the measured speech (a section that would overrun is read slightly
  faster, up to 1.35×, or the build fails). Silent cuts use an estimated speaking time. The captions and each line's
  start, end and tempo are stored in `build.json`, so the `.vtt` files always match the film that was cut.
- The Omega Steward clip shows its defined Kokoro voice as a label; that voice is not played in the film.

## Honesty rules the build enforces

- The build fails if the page or captions would contain the private repository's name, any email address other than
  one passed with `--contact-email`, a wallet-like address, a key-like string, or a local file path.
- Market figures are labelled as third-party forecasts about adjacent markets, never as traction. The page states
  plainly that the project has no revenue, users, customers or partnerships.
- The six reserved actions are shown verbatim, held for the 2-of-3 Steward Council. Omega Stewards are shown as
  "defined, not seated".
- What is not done is listed: not mounted in Sneeze, nothing deployed or minted on any chain, most worlds have no
  anchor, and RP1 publication is the founder's call.
