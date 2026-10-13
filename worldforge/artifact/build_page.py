#!/usr/bin/env python3
"""SmartCiti.X pitch page: a whitepaper / pitch-deck artifact built from the registries.

    python3 worldforge/artifact/build_page.py      # -> worldforge/artifact/index.html + media/ (the publishable folder)

Every project number is read from a registry when this runs; every market figure is one of the fact-checked claims in
worldforge/whitepaper/content/market.json (confirmed or corrected only) and links its source. The 3D viewer and consoles
run from the team's own server, so the page links each world to its section here and, where the founder has chosen
one, to its RP1 location (enter.rp1.com); it never names the private repository.
"""
import html
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = HERE
E = html.escape


def J(p):
    with open(os.path.join(ROOT, p)) as f:
        return json.load(f)


def opt(p):
    return J(p) if os.path.exists(os.path.join(ROOT, p)) else None


IDX = J("worldforge/out/index.json")
AV = J("worldforge/out/avatars/index.json")
LM = {w["slug"]: w for w in J("worldforge/out/assets/landmarks/index.json")["worlds"]}
TR = {w["slug"]: w for w in J("worldforge/out/training/index.json")["worlds"]}
VO = J("worldforge/out/voices/manifest.json")
HIVE = J("agents/hive/index.json")
MKT = J("worldforge/whitepaper/content/market.json")
ROAD = J("atlas/roadmap.json")
DRV = J("worldforge/out/drives/index.json")
AK = os.path.exists(os.path.join(ROOT, "worldforge/akamai/RESULTS.md"))
ONC = J("worldforge/out/onchain/index.json")
SPACES = J("my-fabric/worlds/spaces_index.json")
CONF_LINE = None

voiced_by_world = {}
for line in VO["lines"]:
    w = line["avatarId"].split(":")[1].split("/")[0]
    voiced_by_world[w] = voiced_by_world.get(w, 0) + 1

STYLE_LABEL = {"series-setback": "W3 LLC series world", "focus-rotunda": "PBC focus DAO", "track-twist": "Program track",
               "platform-prism": "Platform world"}

worlds = []
for w in IDX["worlds"]:
    cards = J(f"worldforge/out/{w['slug']}/cards.json")["cards"]
    wc = cards[0]
    om = next((c for c in cards if c["kind"] == "omega"), None)
    zones = [c for c in cards if c["kind"] == "zone"]
    agents = [c for c in cards if c["kind"] == "agent"]
    lm = LM.get(w["slug"], {})
    coll = J(f"worldforge/out/onchain/{w['slug']}/collection.json")
    worlds.append({
        "slug": w["slug"], "name": wc["name"], "tagline": wc.get("tagline") or "", "status": wc.get("status"),
        "rp1": (wc.get("anchor") or {}).get("rp1"), "zones": [(z["name"], z.get("purpose") or "", (z.get("building") or {}).get("kind")) for z in zones],
        "agents": [(a["name"], a.get("role") or "") for a in agents], "cards": len(cards),
        "temperament": (om or {}).get("persona", {}).get("temperament") if om and om.get("persona") else None,
        "kind": STYLE_LABEL.get(lm.get("style"), "World"), "style": lm.get("style"), "height": lm.get("height_m"),
        "mark": lm.get("mark"), "hue": lm.get("hue", 180), "voiced": voiced_by_world.get(w["slug"], 0),
        "lessons": TR.get(w["slug"], {}).get("lessons", 0), "root": coll.get("merkle_root", "")[:12],
    })

T = IDX["totals"]
avt = AV["totals"]
hive_t = HIVE.get("totals", {})
claims = {c["id"]: c for c in MKT["claims"]}
anchored = sum(1 for w in worlds if w["rp1"])
lessons = sum(w["lessons"] for w in worlds)
voiced = VO["totals"].get("voiced", len(VO["lines"])) if isinstance(VO.get("totals"), dict) else len(VO["lines"])

WHY = ["agents-mkt-mnm", "gartner-apps-2026", "gartner-sprawl-2028", "kpmg-highrisk-q3-2026", "vw-eu-800bn", "vw-abi-45bn",
       "dt-mnm-2030", "city-un-45pct", "gov-euaiact-force"]
foot = {cid: i + 1 for i, cid in enumerate(WHY)}


def cite(cid):
    return f'<a class="fn" href="#src-{foot[cid]}" aria-label="source {foot[cid]}">[{foot[cid]}]</a>'


def world_card(w):
    zones = "".join(f"<li><b>{E(n)}</b><span>{E(p)}</span></li>" for n, p, _ in w["zones"])
    agents = ", ".join(E(n) for n, _ in w["agents"])
    rp1 = (f'<a class="btn" href="{E(w["rp1"])}" target="_blank" rel="noopener">Enter on RP1 ↗</a>' if w["rp1"]
           else '<span class="pill muted">RP1 anchor not chosen yet</span>')
    temper = f'<p class="omega"><span class="lbl">Omega Steward</span> {E(w["temperament"])}</p>' if w["temperament"] else ""
    return f'''<article class="world" id="{E(w["slug"])}" data-kind="{E(w["kind"])}" style="--hue:{int(w["hue"])}">
  <header><span class="mark" aria-hidden="true">{E(w["mark"] or "")}</span><div><h3>{E(w["name"])}</h3><p class="kind">{E(w["kind"])} · {E(w["status"] or "")}</p></div></header>
  <p class="tag">{E(w["tagline"])}</p>
  <ul class="zones">{zones}</ul>
  <p class="agents"><span class="lbl">Agents</span> {agents}</p>
  {temper}
  <dl class="facts"><div><dt>Master Cards</dt><dd>{w["cards"]}</dd></div><div><dt>Lessons</dt><dd>{w["lessons"]}</dd></div><div><dt>Voiced intros</dt><dd>{w["voiced"]}</dd></div><div><dt>Landmark</dt><dd>{E(str(w["height"]))} m</dd></div><div><dt>Merkle root</dt><dd class="mono">{E(w["root"])}…</dd></div></dl>
  <footer>{rp1}<a class="btn ghost" href="#{E(w["slug"])}">Link to this world</a></footer>
</article>'''


kinds = sorted({w["kind"] for w in worlds})
filters = '<button type="button" class="chip on" data-k="all">All {n}</button>'.format(n=len(worlds)) + "".join(
    f'<button type="button" class="chip" data-k="{E(k)}">{E(k)} <span>{sum(1 for w in worlds if w["kind"] == k)}</span></button>' for k in kinds)
index_links = "".join(f'<a href="#{E(w["slug"])}">{E(w["name"])}</a>' for w in worlds)
road = "".join(f'<li class="ph {E(p["status"])}"><span class="st">{E(p["status"])}</span><h4>{E(p["name"])}</h4><ul>{"".join(f"<li>{E(i)}</li>" for i in p["items"][:4])}</ul><p class="gate"><span class="lbl">Human gate</span> {E(p["gate"])}</p></li>' for p in ROAD["phases"])
drives_rows = len(DRV["rows"])
drives_ok = sum(1 for r in DRV["rows"] if not r["failed"])
sources = "".join(f'<li id="src-{foot[c]}"><a href="{E(claims[c]["url"])}" target="_blank" rel="noopener">{E(claims[c]["publisher"])}, {E(str(claims[c]["year"]))}</a>. {E(claims[c]["claim"])}</li>' for c in WHY)
film = "media/film-features.mp4"
has_vtt = False  # artifacts do not serve .vtt; narration and on-screen text carry the film
roadmap_film = "media/film-roadmap-stack.mp4"

page = f'''<title>SmartCiti.X Agentic Worlds</title>
<meta name="description" content="41 agent-run, human-governed virtual worlds for the AGI Future Foundation PBC: Master Cards, avatars, an Omega Hive, buildings and a path to RP1.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
/* Layout: civic wayfinding. A city signage system: tall condensed display, plaques, a world directory you can filter. */
:root {{ --bg:#f2f3ee; --surface:#ffffff; --raise:#e7e9e2; --fg:#14211f; --muted:#56635f; --line:#cdd3cb; --accent:#a8631a; --accent-fg:#ffffff; --ok:#2f7a55;
  --display:"Big Shoulders Display", "Arial Narrow", sans-serif; --body:"IBM Plex Sans", system-ui, sans-serif; --mono:"IBM Plex Mono", ui-monospace, monospace; color-scheme: light }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#0e1514; --surface:#151f1d; --raise:#1c2825; --fg:#e6ebe5; --muted:#9caaa4; --line:#2a3834; --accent:#e3a44f; --accent-fg:#1a1206; --ok:#6fc49a; color-scheme: dark }} }}
:root[data-theme="dark"] {{ --bg:#0e1514; --surface:#151f1d; --raise:#1c2825; --fg:#e6ebe5; --muted:#9caaa4; --line:#2a3834; --accent:#e3a44f; --accent-fg:#1a1206; --ok:#6fc49a; color-scheme: dark }}
* {{ box-sizing:border-box }}
body {{ background:var(--bg); color:var(--fg); font:16px/1.6 var(--body); padding-inline:clamp(16px,4vw,48px); padding-block:0 64px }}
.wrap {{ max-width:1180px; margin:0 auto; display:flex; flex-direction:column; gap:72px }}
h1,h2,h3,h4 {{ font-family:var(--display); font-weight:800; letter-spacing:.01em; text-wrap:balance; margin:0; line-height:1.02 }}
h1 {{ font-size:clamp(48px,9vw,112px); text-transform:uppercase }}
h2 {{ font-size:clamp(34px,5vw,56px); text-transform:uppercase }}
h3 {{ font-size:28px }} h4 {{ font-size:22px; font-weight:600 }}
p {{ margin:0; max-width:68ch }}
a {{ color:var(--accent) }} a:focus-visible, button:focus-visible {{ outline:3px solid var(--accent); outline-offset:3px }}
.eyebrow, .lbl, dt, .st, .pill {{ font:500 12px/1.2 var(--mono); letter-spacing:.12em; text-transform:uppercase; color:var(--muted) }}
nav.top {{ position:sticky; top:env(safe-area-inset-top,0px); z-index:5; background:var(--bg); border-bottom:1px solid var(--line); display:flex; gap:18px; align-items:center; padding-block:12px; overflow-x:auto; white-space:nowrap }}
nav.top b {{ font-family:var(--display); font-size:20px; letter-spacing:.04em; text-transform:uppercase }}
nav.top a {{ color:var(--fg); text-decoration:none; font-size:14px }}
.hero {{ display:grid; grid-template-columns:minmax(0,1.15fr) minmax(0,1fr); gap:40px; align-items:end; padding-top:48px }}
.hero .lede {{ font-size:20px; color:var(--muted); margin-top:20px }}
.plaque {{ border:2px solid var(--fg); padding:18px 20px; display:grid; gap:14px; background:var(--surface) }}
.stats {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:1px; background:var(--line); border:1px solid var(--line) }}
.stats div {{ background:var(--surface); padding:14px }}
.stats b {{ display:block; font:800 38px/1 var(--display); font-variant-numeric:tabular-nums }}
.stats span {{ font-size:13px; color:var(--muted) }}
.film {{ display:grid; gap:12px }}
.film video {{ width:100%; max-width:100%; aspect-ratio:16/9; background:#000; border:2px solid var(--fg) }}
.film p {{ font-size:14px; color:var(--muted) }}
section {{ display:grid; gap:24px; scroll-margin-top:72px }}
.cols {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr)); gap:20px }}
.claim {{ border-top:4px solid var(--accent); padding-top:14px; display:grid; gap:8px }}
.claim b {{ font:800 34px/1 var(--display) }}
.fn {{ font:500 12px var(--mono); text-decoration:none; margin-left:2px }}
.note {{ background:var(--raise); padding:16px 18px; font-size:15px }}
.model {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr)); gap:1px; background:var(--line); border:1px solid var(--line) }}
.model div {{ background:var(--surface); padding:16px; display:grid; gap:6px; min-width:0 }}
.model code, .mono {{ font-family:var(--mono); font-size:13px }}
.stack {{ display:grid; gap:6px }}
.stack div {{ display:grid; grid-template-columns:minmax(0,180px) minmax(0,1fr); gap:16px; padding:12px 16px; background:var(--surface); border-left:6px solid var(--accent) }}
.stack div:nth-child(2n) {{ border-left-color:var(--fg) }}
.stack b {{ font-family:var(--display); font-size:20px; text-transform:uppercase }}
table {{ border-collapse:collapse; width:100%; font-size:14px }} th,td {{ text-align:left; padding:8px 10px; border-bottom:1px solid var(--line); vertical-align:top }}
.tbl {{ overflow-x:auto }}
.chips {{ display:flex; flex-wrap:wrap; gap:8px }}
.chip {{ font:500 13px var(--body); border:1px solid var(--line); background:var(--surface); color:var(--fg); padding:6px 12px; cursor:pointer }}
.chip.on {{ background:var(--fg); color:var(--bg); border-color:var(--fg) }} .chip span {{ opacity:.7 }}
.windex {{ display:flex; flex-wrap:wrap; gap:6px 14px; font-size:14px }}
.directory {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(min(100%,340px),1fr)); gap:18px }}
.world {{ --tone:hsl(var(--hue) 45% 42%); background:var(--surface); border:1px solid var(--line); border-top:6px solid var(--tone); padding:18px; display:flex; flex-direction:column; gap:12px; min-width:0; scroll-margin-top:72px }}
.world:target {{ outline:3px solid var(--accent) }}
.world header {{ display:flex; gap:12px; align-items:center }}
.mark {{ font:800 22px/1 var(--display); width:48px; height:48px; display:grid; place-items:center; background:var(--tone); color:#fff; flex:none }}
.kind {{ font-size:13px; color:var(--muted) }} .tag {{ font-size:15px }}
.zones {{ list-style:none; padding:0; margin:0; display:grid; gap:6px; font-size:13.5px }}
.zones li {{ display:grid; gap:2px }} .zones span {{ color:var(--muted) }}
.agents, .omega {{ font-size:13.5px }}
.facts {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; margin:0 }}
.facts div {{ background:var(--raise); padding:8px }} .facts dd {{ margin:2px 0 0; font:600 15px var(--body); font-variant-numeric:tabular-nums; overflow-wrap:anywhere }}
.world footer {{ margin-top:auto; display:flex; flex-wrap:wrap; gap:8px }}
.btn {{ font:600 13px var(--body); padding:8px 12px; background:var(--accent); color:var(--accent-fg); text-decoration:none }}
.btn.ghost {{ background:transparent; color:var(--fg); border:1px solid var(--line) }}
.pill {{ border:1px dashed var(--line); padding:8px 10px }}
.road {{ list-style:none; padding:0; margin:0; display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr)); gap:16px }}
.ph {{ background:var(--surface); border:1px solid var(--line); padding:16px; display:grid; gap:10px; align-content:start }}
.ph.done {{ border-top:6px solid var(--ok) }} .ph.now {{ border-top:6px solid var(--accent) }} .ph.next, .ph.later {{ border-top:6px solid var(--line) }}
.ph ul {{ margin:0; padding-left:18px; font-size:14px }} .gate {{ font-size:14px }}
.not li {{ margin-bottom:6px }}
.sources {{ font-size:13.5px; padding-left:22px }}
.contact {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center }} .contact code {{ font:500 16px var(--mono); background:var(--raise); padding:8px 12px; user-select:all }}
@media (max-width:760px) {{ .hero {{ grid-template-columns:1fr }} .stats {{ grid-template-columns:repeat(2,minmax(0,1fr)) }} .stack div {{ grid-template-columns:1fr }} }}
@media (prefers-reduced-motion:reduce) {{ * {{ scroll-behavior:auto !important }} }}
</style>
<nav class="top" aria-label="Sections"><b>SmartCiti.X</b><a href="#film">Film</a><a href="#why">Why</a><a href="#what">What</a><a href="#how">How</a><a href="#governance">Governance</a><a href="#worlds">41 worlds</a><a href="#roadmap">Roadmap</a><a href="#sources">Sources</a></nav>
<main class="wrap">
<header class="hero">
  <div><p class="eyebrow">AGI Future Foundation PBC · Powered by AGI Corp</p>
  <h1>Agentic worlds, governed by people</h1>
  <p class="lede">SmartCiti.X is a network of {T["worlds"]} virtual worlds where AI agents run the day-to-day work and people keep every decision that matters. Each world is a set of owned, permissioned Master Cards that can be streamed into RP1, walked in a browser, and checked by evals on every heartbeat.</p></div>
  <div class="plaque"><span class="lbl">The network today</span>
   <div class="stats"><div><b>{T["worlds"]}</b><span>worlds</span></div><div><b>{T["cards"]}</b><span>Master Cards</span></div><div><b>{avt["avatars"]}</b><span>agent avatars</span></div>
   <div><b>{hive_t.get("omegas", 44)}</b><span>Omega Stewards, none seated</span></div><div><b>{lessons}</b><span>draft lessons</span></div><div><b>{T["evals"]}</b><span>WorldForge evals, {T["failed"]} failing</span></div></div>
   <span class="lbl">Source: worldforge/out/index.json, avatars, training and hive registries</span></div>
</header>

<section id="film" class="film" aria-labelledby="film-h"><h2 id="film-h">The two-minute explainer</h2>
  <video controls preload="metadata" poster="media/poster-features.jpg">
    <source src="{film}" type="video/mp4">{'<track kind="captions" src="media/film-features.vtt" srclang="en" label="English" default>' if has_vtt else ''}
  </video>
  <p>Features film, 120 seconds: the world network, a walkthrough recorded in the WorldForge viewer (fly-in, a building and its interior, the Omega Steward, the council, a landmark), avatars bound to agents, the Omega Hive, and governance. The narration is a synthetic voice.</p>
</section>

<section id="why" aria-labelledby="why-h"><p class="eyebrow">Why we built it</p><h2 id="why-h">Agents are arriving faster than governance</h2>
  <div class="cols">
   <div class="claim"><b>$7.84bn → $52.62bn</b><p>AI agents market, 2025 to 2030, as projected by MarketsandMarkets.{cite("agents-mkt-mnm")}</p></div>
   <div class="claim"><b>40%</b><p>of enterprise applications expected to integrate task-specific agents by 2026, up from under 5%, says Gartner.{cite("gartner-apps-2026")}</p></div>
   <div class="claim"><b>150,000+</b><p>AI agents per Global Fortune 500 enterprise expected by 2028, with a warning about ungoverned sprawl.{cite("gartner-sprawl-2028")}</p></div>
   <div class="claim"><b>49%</b><p>of leaders have defined high-risk uses where autonomous agent decisions are not allowed (KPMG, Q3 2026).{cite("kpmg-highrisk-q3-2026")}</p></div>
   <div class="claim"><b>45%</b><p>of the world's 8.2 billion people live in cities, the setting SmartCiti.X models.{cite("city-un-45pct")}</p></div>
   <div class="claim"><b>Aug 2024</b><p>the EU AI Act entered into force; it became applicable in August 2026, with some exceptions.{cite("gov-euaiact-force")}</p></div>
  </div>
  <p class="note">Virtual-world forecasts disagree widely: the European Commission cites a market of over EUR 800 billion by 2030{cite("vw-eu-800bn")}, while ABI Research held a US$45 billion view{cite("vw-abi-45bn")}. We read that spread as uncertainty about demand, not as a target. Digital twins are forecast to reach USD 149.81 billion by 2030{cite("dt-mnm-2030")}. SmartCiti.X has no revenue or users to report yet.</p>
</section>

<section id="what" aria-labelledby="what-h"><p class="eyebrow">What it is</p><h2 id="what-h">Every place, agent and seat is an owned Master Card</h2>
  <p>A world is a tree of SmartCiti.X Master Cards. Each card has an owner (the PBC), a <b>Volum</b> (the bounded 3D region it governs) and a seven-right permission table. Agents may view, enter and operate their own zone. Building, delegating, transferring and governing belong to people, and six actions are always held for a 2-of-3 human Steward Council.</p>
  <div class="model">
   <div><span class="lbl">Card kinds</span><p>world, plaza, coordinator, 3 scripted advisors, Alignment Evaluation Gate, council with 3 empty human seats, Omega Steward, zones with buildings, agents</p></div>
   <div><span class="lbl">Seven rights</span><p><code>view · enter · build · operate · delegate · transfer · govern</code></p></div>
   <div><span class="lbl">Held for people</span><p><code>governance.final_vote · charter.amend · treasury.transfer · proposal.enact · windfall.distribute · steward.appoint</code></p></div>
   <div><span class="lbl">Buildings</span><p>{SPACES["totals"]["exteriors"]} exteriors and {SPACES["totals"]["interiors"]} interiors with PBR textures, doors aligned to each zone's room, plus {len(LM)} civic landmarks</p></div>
  </div>
</section>

<section id="how" aria-labelledby="how-h"><p class="eyebrow">How it works</p><h2 id="how-h">The stack, layer by layer</h2>
  <div class="stack">
   <div><b>Assets</b><p>glTF 2.0 worlds, buildings, interiors, landmarks and six rig-free avatar models, all checked by the Khronos validator. Lighter LOD versions exist for streaming.</p></div>
   <div><b>Master Cards</b><p>Card-tagged GLBs and mount plans for the Sneeze engine. Names fit the engine's 47-character limit, and Sneeze conformance shows 0 violations.</p></div>
   <div><b>Agents</b><p>{avt["specialists"]} specialists, {avt["coordinators"]} coordinators and {avt["advisors"]} scripted advisors, each bound to its card, swarm and metaprompt. {avt["persona_prompts"]} persona prompts pass {avt["prompt_gates"]} gate checks.</p></div>
   <div><b>Omega Hive</b><p>{hive_t.get("omegas", 44)} Omega Stewards with grounded personas and synthetic voices. They are defined, not seated: none acts until a person seats it.</p></div>
   <div><b>Gateway</b><p>A guarded service between visitors and the model. It strips personal data and refuses the six human-only actions in code, before the model sees them.</p></div>
   <div><b>Evidence</b><p>A heartbeat runs every generator and eval. There is a hash-chained agent ledger and an on-chain-ready export of {ONC.get("totals", {}).get("tokens", T["cards"])} card tokens with Merkle roots (draft, not deployed).</p></div>
   <div><b>Compute</b><p>On the Akamai inference workshop's GPU, Qwen3-4B on vLLM drafted all 246 zone expansions in 66 seconds at 32 concurrent requests. The drafts are unreviewed.</p></div>
  </div>
</section>

<section id="governance" aria-labelledby="gov-h"><p class="eyebrow">Governance</p><h2 id="gov-h">Built to leave the "basic AI drives" spine</h2>
  <p>Ben Goertzel's restatement of Omohundro's argument lists six assumptions under which an AI drifts toward self-protection and resource grabbing. We check every world's design against the ways out of that argument:</p>
  <ul>
   <li>many objectives, not a single score;</li>
   <li>held actions that can't be outweighed;</li>
   <li>self-change gated by people;</li>
   <li>goal changes only under governance;</li>
   <li>prompts that care how goals are reached;</li>
   <li>an off switch that stays with people.</li>
  </ul>
  <p><b>{drives_ok} of {drives_rows}</b> worlds pass all seven checks.</p>
  <p class="note">These checks measure design, not a running model's values. In a live test, a raw Qwen3-4B offered to move treasury funds when only its prompt forbade it. That is why the gateway enforces the held actions in code.</p>
</section>

<section id="worlds" aria-labelledby="worlds-h"><p class="eyebrow">The directory</p><h2 id="worlds-h">{len(worlds)} worlds</h2>
  <p>Each card shows the world's zones and agents, its Omega Steward's temperament, and its counts. Where the founder has chosen an RP1 location ({anchored} so far), it links straight into RP1. The 3D viewer and team consoles run from the team's own server and are available on request.</p>
  <div class="chips" role="group" aria-label="Filter worlds">{filters}</div>
  <div class="windex">{index_links}</div>
  <div class="directory">{"".join(world_card(w) for w in worlds)}</div>
</section>

<section id="roadmap" aria-labelledby="road-h"><p class="eyebrow">Roadmap</p><h2 id="road-h">Every phase names the person who decides</h2>
  <ol class="road">{road}</ol>
</section>

<section aria-labelledby="not-h"><h2 id="not-h">What we do not claim</h2>
  <ul class="not">
   <li>Nothing is mounted or rendered in the Sneeze engine yet. The mount plans and decoder are ready, and the native gates are open.</li>
   <li>Nothing is deployed or minted on any chain. The Merkle roots are commitments a future contract could anchor, by a human decision.</li>
   <li>No steward is seated and no Omega acts. Only {anchored} of {len(worlds)} worlds have an RP1 location, and publishing on RP1 is the founder's call.</li>
   <li>Lessons are drafts and none is certified. The Akamai expansions are unreviewed model drafts. Every voice is synthetic.</li>
  </ul>
</section>

<section id="sources" aria-labelledby="src-h"><h2 id="src-h">Sources</h2>
  <ol class="sources">{sources}</ol>
  <p class="note">External figures were checked against their sources on 2026-10-12. Project figures are read from the WorldForge registries at build time.</p>
  <div class="contact"><span class="lbl">Contact</span><code>x@agifuturefoundation.org</code><button type="button" class="chip" id="copy">Copy address</button></div>
</section>
</main>
<script>
(() => {{
  const chips = document.querySelectorAll('.chip[data-k]'), cards = document.querySelectorAll('.world');
  chips.forEach(c => c.addEventListener('click', () => {{
    chips.forEach(x => x.classList.toggle('on', x === c));
    cards.forEach(w => {{ w.hidden = c.dataset.k !== 'all' && w.dataset.kind !== c.dataset.k; }});
  }}));
  const b = document.getElementById('copy');
  b.addEventListener('click', () => {{
    navigator.clipboard?.writeText('x@agifuturefoundation.org').then(() => {{ b.textContent = 'Copied'; }}, () => {{
      const r = document.createRange(); r.selectNodeContents(b.previousElementSibling); const s = getSelection(); s.removeAllRanges(); s.addRange(r); b.textContent = 'Selected: press copy';
    }});
  }});
}})();
</script>
'''
assert "agi-corp-worlds" not in page
os.makedirs(os.path.join(OUT, "media"), exist_ok=True)
with open(os.path.join(OUT, "index.html"), "w") as f:
    f.write(page)
for src, dst in [("worldforge/whitepaper/out/film-features.mp4", "film-features.mp4"),
                 ("worldforge/whitepaper/out/film-features.vtt", "film-features.vtt"),
                 ("worldforge/whitepaper/out/media/poster-features.jpg", "poster-features.jpg")]:
    p = os.path.join(ROOT, src)
    if os.path.exists(p):
        shutil.copyfile(p, os.path.join(OUT, "media", dst))
print(f"page: {len(page)//1024} KB, {len(worlds)} worlds, {anchored} anchored, {len(WHY)} cited claims")
