#!/usr/bin/env node
// worldforge/overview.mjs: deep GLEWME overviews, one Markdown file per world plus a network README.
//
//   node worldforge/overview.mjs           writes worldforge/out/overview/*.md and runs the evals (exit 1 on any failure)
//   node worldforge/overview.mjs --check   exit 1 if worldforge/out/overview/ is behind its registries
//
// Every number is read from a registry at build time and the section that shows it names the source path.
// Nothing is invented: when a registry has no value, the overview says so. No timestamps, so output is deterministic.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT_REL = 'worldforge/out/overview';
const OUT = path.join(ROOT, OUT_REL);
const CHECK = process.argv.includes('--check');
const FORBIDDEN = ['agi', 'corp', 'worlds'].join('-'); // never written into any overview

const abs = (rel) => path.join(ROOT, rel);
const exists = (rel) => !!rel && fs.existsSync(abs(rel));
const readJSON = (rel) => JSON.parse(fs.readFileSync(abs(rel), 'utf8'));
const readOpt = (rel) => (exists(rel) ? readJSON(rel) : null);

// ---------- formatting helpers (locale-free, deterministic) ----------
const fmt = (n) => {
  if (n === null || n === undefined) return 'none';
  if (typeof n !== 'number') return String(n);
  if (!Number.isInteger(n)) return String(n);
  const s = String(Math.abs(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  return n < 0 ? '-' + s : s;
};
const vec = (v) => (Array.isArray(v) ? '(' + v.map((x) => String(x)).join(', ') + ')' : 'none');
const cell = (s) => String(s ?? '').replace(/\|/g, '\\|').replace(/\n/g, ' ');
const code = (s) => '`' + String(s).replace(/`/g, "'") + '`';
const plural = (n, one, many) => `${fmt(n)} ${n === 1 ? one : many || one + 's'}`;
const relFromOverview = (repoRel) => path.posix.relative(OUT_REL, repoRel);

// ---------- registries ----------
const SRC = {
  index: 'worldforge/out/index.json',
  avatars: 'worldforge/out/avatars/index.json',
  voices: 'worldforge/out/voices/manifest.json',
  hive: 'agents/hive/index.json',
  landmarks: 'worldforge/out/assets/landmarks/index.json',
  onchain: 'worldforge/out/onchain/index.json',
  conformance: 'worldforge/native/conformance-report.json',
  roadmap: 'atlas/roadmap.json',
  pbc: 'worlds/PBC.json',
  wfReadme: 'worldforge/README.md',
  viewer: 'worldforge/viewer.html',
  console: 'consoles/worldforge/index.html',
};
const P = {
  cards: (s) => `worldforge/out/${s}/cards.json`,
  manifest: (s) => `worldforge/out/${s}/manifest.json`,
  plan: (s) => `worldforge/out/${s}/sneeze-mount-plan.json`,
  glb: (s) => `worldforge/out/${s}/${s}.glb`,
  collection: (s) => `worldforge/out/onchain/${s}/collection.json`,
  proofs: (s) => `worldforge/out/onchain/${s}/proofs.json`,
  team: (s) => `worlds/generated/teams/${s}.json`,
  training: (s) => `worldforge/out/training/${s}.json`,
  overview: (s) => `${OUT_REL}/${s}.md`,
};

function loadAll() {
  const R = {};
  for (const [k, rel] of Object.entries(SRC)) if (rel.endsWith('.json')) R[k] = readJSON(rel);
  R.worlds = R.index.worlds.map((w) => {
    const s = w.slug;
    return {
      entry: w,
      slug: s,
      cards: readJSON(P.cards(s)),
      manifest: readJSON(P.manifest(s)),
      plan: readJSON(P.plan(s)),
      collection: readOpt(P.collection(s)),
      team: readOpt(P.team(s)),
      training: readOpt(P.training(s)),
    };
  });
  return R;
}

// ---------- a Markdown document that records what it mentions ----------
class Doc {
  constructor(rel) {
    this.rel = rel;
    this.lines = [];
    this.cardIds = new Set();
    this.links = [];
  }
  p(...ls) { this.lines.push(...ls); return this; }
  blank() { this.lines.push(''); return this; }
  cid(id) { this.cardIds.add(id); return code(id); }
  link(text, repoRelTarget, query = '') {
    this.links.push(repoRelTarget);
    return `[${text}](${relFromOverview(repoRelTarget)}${query})`;
  }
  linkIf(text, repoRelTarget) { return exists(repoRelTarget) ? this.link(text, repoRelTarget) : `${code(repoRelTarget)} (file not present)`; }
  src(...rels) { this.p('', `_Source: ${rels.map(code).join(', ')}_`); return this; }
  table(head, rows) {
    this.p('| ' + head.map(cell).join(' | ') + ' |', '|' + head.map(() => '---').join('|') + '|');
    for (const r of rows) this.p('| ' + r.map((c) => cell(c)).join(' | ') + ' |');
    return this;
  }
  text() { return this.lines.join('\n').replace(/\n{3,}/g, '\n\n').trim() + '\n'; }
}

const SECTIONS = [
  'Ownership and permissions', 'Volums', 'Buildings and interiors', 'Avatars and agents', 'Omega Steward',
  'Landmark', 'Onchain-ready', 'Sneeze/RP1 readiness', 'Training', 'Evals', 'Gaps',
];

// ---------- per-world facts (computed once, shared by the world page and the README) ----------
function facts(R, W) {
  const s = W.slug;
  const cards = W.cards.cards;
  const byId = new Map(cards.map((c) => [c.cardId, c]));
  const world = byId.get(`world:${s}`);
  const suffix = ` · ${W.cards.umbrella}`;
  const label = (c) => (c.kind === 'plaza' ? `${world.name} Plaza` : c.name || (c.displayName || '').replace(suffix, '') || c.cardId);
  const avatarRows = R.avatars.rows.filter((r) => r.world === s);
  const avatarWorld = R.avatars.worlds.find((w) => w.slug === s) || null;
  const voiceBy = new Map(R.voices.lines.map((l) => [l.avatarId, l]));
  const voicedOf = (row) => {
    const l = voiceBy.get(row.avatarId);
    return l && exists(l.path) ? l : null;
  };
  const omega = R.hive.omegas.find((o) => o.world === s) || null;
  const omegaLines = (omega?.lines || []).map((l) => ({ ...l, recorded: !!l.audio && exists(`agents/hive/${l.audio}`), file: l.audio ? `agents/hive/${l.audio}` : null }));
  const landmark = R.landmarks.worlds.find((w) => w.slug === s) || null;
  const conf = R.conformance.perPlan.find((p) => p.slug === s) || null;
  const buildings = cards.filter((c) => c.building);
  const introVoiced = avatarRows.filter((r) => r.kind !== 'omega' && voicedOf(r)).length;
  const omegaRecorded = omegaLines.filter((l) => l.recorded).length;
  return {
    s, cards, byId, world, label, avatarRows, avatarWorld, voicedOf, omega, omegaLines, landmark, conf, buildings,
    zones: cards.filter((c) => c.kind === 'zone'),
    agents: cards.filter((c) => c.kind === 'agent'),
    introVoiced, omegaRecorded, voicedLines: introVoiced + omegaRecorded,
    anchored: !!world.anchor?.rp1,
  };
}

// ---------- world page ----------
function worldDoc(R, W, F) {
  const s = W.slug;
  const d = new Doc(P.overview(s));
  const w = F.world;
  const brand = W.team?.brand || null;

  // Header
  d.p(`# ${w.name}`, '', `> ${w.tagline}`, '');
  d.table(['Field', 'Value'], [
    ['Status', w.status],
    ['Umbrella', W.cards.umbrella],
    ['Owner', W.cards.owner],
    ['Management style', w.management_style],
    ['Principle', W.cards.principle],
    ['RP1 anchor', F.anchored ? `lat ${w.anchor.lat}, lon ${w.anchor.lon} (rad ${fmt(w.anchor.rad)} m): ${w.anchor.rp1}` : 'no anchor yet'],
    ['Team brand mark', brand ? `${code(brand.mark)}, hue ${brand.hue}, lockup "${brand.lockup}"` : 'no team brand registered'],
    ['Root card', d.cid(w.cardId)],
    ['Master Cards', fmt(F.cards.length)],
  ]);
  d.blank().p(
    `Open: ${d.link('3-D viewer', SRC.viewer, `?world=${s}`)} · ${d.link('WorldForge console', SRC.console, `?world=${s}`)} · ` +
    `${d.link('cards.json', P.cards(s))} · ${d.link('GLB', P.glb(s))} · ${d.link('mount plan', P.plan(s))} · ${d.link('manifest', P.manifest(s))} · ${d.link('network overview', `${OUT_REL}/README.md`)}`,
  );
  d.src(P.cards(s) + '#world:' + s, P.team(s) + '#brand');

  // Ownership and permissions
  d.blank().p('## Ownership and permissions', '');
  d.p(`Every object in ${w.name} is a GLEWME Master Card owned by ${W.cards.owner}. The tree below follows ${code('parentCardId')}: world, plaza (coordinator and scripted advisors), gate, council (human seats), Omega Steward, then zones with their agent avatars.`, '');
  const kids = new Map();
  for (const c of F.cards) {
    const k = c.parentCardId ?? '__root';
    if (!kids.has(k)) kids.set(k, []);
    kids.get(k).push(c);
  }
  const detail = (c) => {
    switch (c.kind) {
      case 'world': return `${c.status}; ${c.management_style}`;
      case 'plaza': case 'gate': case 'council': case 'zone': return c.purpose || '';
      case 'coordinator': case 'agent': return c.role || '';
      case 'advisor': return `${c.scripted ? 'scripted guide' : 'guide'}: ${c.manages}`;
      case 'seat': return `${c.seat_type} seat, ${c.seated === null ? 'empty' : 'seated'}`;
      case 'omega': return `${c.status}; seated agent: ${c.seated_agent === null ? 'none' : c.seated_agent}`;
      default: return '';
    }
  };
  const walk = (c, depth) => {
    const det = detail(c);
    d.p(`${'  '.repeat(depth)}- **${F.label(c)}** (${c.kind}) ${d.cid(c.cardId)}${det ? ': ' + det : ''}`);
    for (const k of kids.get(c.cardId) || []) walk(k, depth + 1);
  };
  for (const r of kids.get('__root') || []) walk(r, 0);
  const count = (k) => F.cards.filter((c) => c.kind === k).length;
  d.blank().p(`Card counts: ${['world', 'plaza', 'coordinator', 'advisor', 'gate', 'council', 'seat', 'omega', 'zone', 'agent'].map((k) => `${k} ${count(k)}`).join(', ')}. The ${count('seat')} council seats are human seats; ${F.cards.filter((c) => c.kind === 'seat' && c.seated === null).length} are empty.`);

  // permission profiles
  const rights = W.cards.rights;
  const profiles = [];
  for (const c of F.cards) {
    const key = rights.map((r) => (c.permissions[r] || []).join('+')).join('|');
    let p = profiles.find((x) => x.key === key);
    if (!p) profiles.push((p = { key, perms: c.permissions, kinds: new Map() }));
    p.kinds.set(c.kind, (p.kinds.get(c.kind) || 0) + 1);
  }
  const colName = (p) => [...p.kinds].map(([k, n]) => (n > 1 ? `${k} x${n}` : k)).join(', ');
  d.blank().p('### Who holds each right', '');
  d.p(`Cards that share the same permission matrix are grouped into one column (${profiles.length} distinct ${profiles.length === 1 ? 'matrix' : 'matrices'} across ${F.cards.length} cards).`, '');
  d.table(['Right', ...profiles.map(colName)], rights.map((r) => [r, ...profiles.map((p) => (p.perms[r] || []).join(', ') || 'nobody')]));
  d.blank().p(`Holders are written as the cards store them. In the words of ${code(SRC.wfReadme)}: agents can view, enter and operate their own zone (${code('agents:zone')}), and nothing else; ${code('delegate')} belongs to stewards; ${code('transfer')} and ${code('govern')} are held for a 2-of-3 steward quorum.`);

  d.blank().p('### Actions reserved for people', '');
  const reserved = w.reserved_for_humans;
  const carried = F.cards.filter((c) => JSON.stringify(c.reserved_for_humans) === JSON.stringify(reserved)).length;
  const operators = F.cards.filter((c) => ['agent', 'coordinator', 'advisor', 'omega'].includes(c.kind));
  const barred = operators.filter((c) => reserved.every((r) => (c.may_never || []).includes(r.action))).length;
  d.table(['Action', 'Held for', 'Quorum', 'Seats'], reserved.map((r) => [code(r.action), r.held_for.holder, r.held_for.quorum, fmt(r.held_for.seats)]));
  d.blank().p(`The same ${reserved.length} reservations are carried on ${carried} of ${F.cards.length} cards. ${barred} of ${operators.length} agent, coordinator, advisor and Omega cards list all ${reserved.length} in ${code('may_never')}.`);
  d.src(P.cards(s), SRC.pbc + '#reserved_for_humans');

  // Volums
  d.blank().p('## Volums', '');
  d.p('Each card covers a Volum: a bounded 3-D region, a box given by its centre and half-extents in metres. Size is twice the half-extents.', '');
  const volCards = F.cards.filter((c) => ['world', 'plaza', 'gate', 'council', 'omega', 'zone'].includes(c.kind));
  d.table(['Card', 'Kind', 'Shape', 'Centre (m)', 'Half-extents (m)', 'Size (m)'], volCards.map((c) => [
    `${F.label(c)} ${d.cid(c.cardId)}`, c.kind, c.volum.shape, vec(c.volum.center), vec(c.volum.halfExtents), c.volum.halfExtents.map((h) => String(Math.round(h * 2 * 100) / 100)).join(' x '),
  ]));
  const small = F.cards.filter((c) => !volCards.includes(c));
  d.blank().p(`The other ${small.length} cards (coordinator, advisors, seats and agents) each hold a small box at their post; their Volums are in ${code(P.cards(s))}.`);
  d.src(P.cards(s) + '#cards[].volum');

  // Buildings
  d.blank().p('## Buildings and interiors', '');
  if (!F.buildings.length) d.p('No card in this world carries a building.');
  else {
    d.p(`${plural(F.buildings.length, 'card carries', 'cards carry')} a building: an exterior, an interior and a room model, with a door.`, '');
    d.table(['Card', 'Kind', 'Exterior', 'Interior', 'Room', 'Texture res. ext/int (px)', 'Triangles ext/int', 'Door (centre, half-width, head)'], F.buildings.map((c) => {
      const b = c.building;
      return [
        `${F.label(c)} ${d.cid(c.cardId)}`, b.kind, d.linkIf(path.posix.basename(b.exterior), b.exterior), d.linkIf(path.posix.basename(b.interior), b.interior), d.linkIf(path.posix.basename(b.room), b.room),
        `${fmt(b.resolution?.exterior)} / ${fmt(b.resolution?.interior)}`, `${fmt(b.triangles?.exterior)} / ${fmt(b.triangles?.interior)}`,
        b.door ? `${vec(b.door.centre)}, ${b.door.half_width} m, ${b.door.head} m` : 'none',
      ];
    }));
    const tri = F.buildings.reduce((a, c) => a + (c.building.triangles?.exterior || 0) + (c.building.triangles?.interior || 0), 0);
    d.blank().p(`Exterior plus interior triangles across these buildings: ${fmt(tri)}.`);
    d.src(P.cards(s) + '#cards[].building', [...new Set(F.buildings.map((c) => c.building.source))].join(', '));
  }

  // Avatars and agents
  d.blank().p('## Avatars and agents', '');
  const aw = F.avatarWorld;
  d.p(`${plural(F.avatarRows.length, 'avatar')} stand in this world${aw ? ` (registry: ${aw.avatars} avatars, ${aw.specialists} specialists, ${aw.advisors} advisors, Omega ${aw.omega ? 'present' : 'absent'})` : ''}. Voiced means a rendered intro file is listed in ${code(SRC.voices)} and exists on disk; otherwise the viewer falls back to a labelled browser voice.`, '');
  const order = ['coordinator', 'advisor', 'specialist', 'omega'];
  const heads = { coordinator: 'Coordinator', advisor: 'Scripted advisors', specialist: 'Specialist agents', omega: 'Omega Steward avatar' };
  for (const kind of order) {
    const rows = F.avatarRows.filter((r) => r.kind === kind);
    if (!rows.length) continue;
    d.blank().p(`### ${heads[kind]}`, '');
    for (const r of rows) {
      let voiced;
      if (kind === 'omega') {
        const g = F.omegaLines.find((l) => l.id === 'greet');
        voiced = g?.recorded ? `voiced: yes, hive greet line (${g.seconds} s, ${d.link('audio', g.file)})` : 'voiced: not recorded';
      } else {
        const v = F.voicedOf(r);
        voiced = v ? `voiced: yes (${v.seconds} s, ${d.link('audio', v.path)})` : 'voiced: not voiced';
      }
      const swarm = r.binding?.swarm ? `swarm ${code(r.binding.swarm)}` : r.binding?.hive ? `hive ${code(r.binding.hive)}` : r.binding?.advisor ? `advisor contract ${code(r.binding.advisor.file + '#' + r.binding.advisor.id)}` : 'no binding';
      d.p(`- **${r.name}** (${r.role}) ${d.cid(r.cardId)}, in ${r.zone}: ${swarm}; voice ${code(r.voice?.id || 'none')}; ${voiced}`);
      if (r.role_text) d.p(`  - Role: ${r.role_text}`);
      if (r.intro?.text) d.p(`  - Intro: "${r.intro.text}"`);
    }
  }
  d.blank().p(`Intro lines voiced: ${F.introVoiced} of ${F.avatarRows.filter((r) => r.kind !== 'omega').length} coordinator, advisor and specialist avatars.`);
  d.src(SRC.avatars + `#rows[world=${s}]`, SRC.voices + '#lines');

  // Omega Steward
  d.blank().p('## Omega Steward', '');
  const o = F.omega;
  const oc = F.cards.find((c) => c.kind === 'omega');
  if (!o) d.p(`No Omega persona for this world in ${code(SRC.hive)}.`);
  else {
    d.p(`**${o.title}** (${code(o.id)}), card ${d.cid(oc.cardId)}: ${oc.status}. Seated in the hive: ${o.seated ? 'yes' : 'no'}.`, '');
    d.p(`- Temperament: ${o.persona.temperament}`, `- Style: ${o.persona.style}`);
    d.p('- Values:', ...o.persona.values.map((v) => `  - ${v}`));
    d.p(`- Refuses (${o.persona.refuses.length}): ${o.persona.refuses.map(code).join(', ')}`);
    d.p(`- Voice: Kokoro ${code(o.voice.kokoro)}, speed ${o.voice.speed}; browser fallback pitch ${o.voice.browser_fallback?.pitch}, rate ${o.voice.browser_fallback?.rate}, ${o.voice.browser_fallback?.lang}`);
    if (o.metaprompt) d.p(`- Metaprompt: ${d.linkIf(o.metaprompt, o.metaprompt)}`);
    d.blank().p('### Voice lines', '');
    d.table(['Line', 'Text', 'Recorded'], F.omegaLines.map((l) => [l.id, `"${l.text}"`, l.recorded ? `yes, ${l.seconds} s (${d.link('audio', l.file)})` : 'not recorded']));
    d.blank().p(`${F.omegaRecorded} of ${F.omegaLines.length} lines are recorded.`);
    if (o.persona.grounded_in?.length) d.blank().p(`Persona grounded in: ${o.persona.grounded_in.map(code).join(', ')}.`);
  }
  d.src(SRC.hive + `#omegas[world=${s}]`, P.cards(s) + `#omega:${s}`);

  // Landmark
  d.blank().p('## Landmark', '');
  const L = F.landmark;
  if (!L) d.p(`No landmark for this world in ${code(SRC.landmarks)}.`);
  else {
    const st = R.landmarks.styles[L.style];
    const file = `worldforge/out/assets/landmarks/${L.file}`;
    d.p(`Registry note: "${R.landmarks.note}".`, '');
    d.table(['Field', 'Value'], [
      ['Model', d.linkIf(L.file, file)],
      ['Height', `${L.height_m} m`],
      ['Style', `${L.style}${st ? `: ${st.form}` : ''}`],
      ['Plaque (brand mark letters)', code(L.plaque_text)],
      ['Tint hue', String(L.hue)],
      ['Triangles / vertices', `${fmt(L.triangles)} / ${fmt(L.vertices)}`],
      ['File size', `${fmt(L.bytes)} bytes`],
      ['Scene node', L.node],
      ['Suggested placement (not applied)', L.placement ? `translation ${vec(L.placement.translation)}, yaw ${L.placement.yaw_deg} deg, clearance ${L.placement.clearance_m} m` : 'none'],
    ]);
    d.blank().p(`Height rule: ${R.landmarks.height_rule}.`);
  }
  d.src(SRC.landmarks + `#worlds[slug=${s}]`);

  // Onchain-ready
  d.blank().p('## Onchain-ready', '');
  const C = W.collection;
  if (!C) d.p(`No collection at ${code(P.collection(s))}.`);
  else {
    const net = R.onchain.worlds.find((x) => x.slug === s || x.collection === `${s}/collection.json`);
    d.p(`**Not deployed.** ${C.deployment.note}`, '');
    d.table(['Field', 'Value'], [
      ['Collection', `${C.name} (${d.link('collection.json', P.collection(s))}, ${d.linkIf('proofs.json', P.proofs(s))})`],
      ['Standard', C.standard],
      ['Tokens / cards', `${fmt(C.token_count)} / ${fmt(C.card_count)}`],
      ['Token id rule', C.token_id_rule],
      ['Merkle root', code(C.merkle_root)],
      ['Network root (all worlds)', code(R.onchain.network_root)],
      ['Deployment status', `${C.deployment.status}; chain ${C.deployment.chain ?? 'none'}, contract ${C.deployment.contract ?? 'none'}, minted ${fmt(C.deployment.minted)}, transactions ${fmt(C.deployment.transactions)}`],
      ['Network proof length', net?.network_proof ? String(net.network_proof.length) : 'not listed'],
    ]);
  }
  d.src(P.collection(s), SRC.onchain);

  // Sneeze/RP1 readiness
  d.blank().p('## Sneeze/RP1 readiness', '');
  const m = W.manifest;
  d.table(['Measure', 'Value'], [
    ['Mount plan nodes (plan file)', fmt(W.plan.nodes.length)],
    ['Plan nodes / resource nodes (manifest)', `${fmt(m.counts.planNodes)} / ${fmt(m.counts.resourceNodes)}`],
    ['Primitives / roads', `${fmt(m.counts.primitives)} / ${fmt(m.counts.roads)}`],
    ['Binding status', W.plan.bindingStatus],
    ['Mount parent', code(W.plan.mountParent)],
    ['Shared resource', W.plan.assets.map((a) => code(a.url)).join(', ')],
    ['Conformance (static check)', F.conf ? `${fmt(F.conf.nodes)} nodes, ${F.conf.nativeViolations} native violations, ${F.conf.jsonRouteViolations} JSON-route violations` : 'not in report'],
    ['Conformance report status', R.conformance.status],
  ]);
  d.blank().p('### Gates', '');
  d.table(['Gate', 'Status'], Object.entries(m.gates).map(([g, v]) => [g, v]));
  d.src(P.plan(s), P.manifest(s) + '#counts,gates', SRC.conformance + `#perPlan[slug=${s}]`);

  // Training
  d.blank().p('## Training', '');
  if (!W.training) d.p(`Not built yet: ${code(P.training(s))} did not exist when this overview was built.`);
  else {
    const T = W.training;
    d.p(`Training data is present at ${d.link(P.training(s), P.training(s))} (${code(T.schemaVersion || 'no schemaVersion')}${T.generator ? ', from ' + code(T.generator) : ''}).`, '');
    if (T.honesty) d.p(`Registry note: "${T.honesty}"`, '');
    if (Array.isArray(T.lessons)) {
      d.p(`### Lessons (${T.lessons.length})`, '');
      d.table(['Lesson', 'Kind', 'Mode', 'Zone', 'Steps', 'Status', 'Assessment', 'Certified'], T.lessons.map((l) => [
        `${l.title || l.id} ${l.id ? code(l.id) : ''}`, l.kind ?? 'none', l.mode ?? 'none', l.zone ?? 'none', Array.isArray(l.steps) ? String(l.steps.length) : 'none',
        l.status ?? 'none', l.assessment?.status ?? 'none', l.certification ? 'yes' : 'no',
      ]));
    }
    if (Array.isArray(T.tutors)) {
      d.blank().p(`### Tutors (${T.tutors.length})`, '');
      d.table(['Tutor', 'Kind', 'Lessons', 'Persona gates passed'], T.tutors.map((t) => [
        `${t.name || t.id} ${t.id ? code(t.id) : ''}`, t.kind ?? 'none', Array.isArray(t.lessons) ? String(t.lessons.length) : 'none',
        t.gates ? `${t.gates.passed} of ${t.gates.of}` : 'none',
      ]));
    }
    if (Array.isArray(T.gaps) && T.gaps.length) d.blank().p(`${plural(T.gaps.length, 'training gap')} listed under Gaps below.`);
    if (!Array.isArray(T.lessons) && !Array.isArray(T.tutors)) {
      const rows = [];
      for (const k of Object.keys(T).sort()) {
        const v = T[k];
        if (v === null || ['string', 'number', 'boolean'].includes(typeof v)) rows.push([k, typeof v === 'string' && v.length > 160 ? v.slice(0, 157) + '...' : String(v)]);
        else if (Array.isArray(v)) rows.push([k, `list of ${v.length}`]);
        else rows.push([k, `object with ${Object.keys(v).length} keys`]);
      }
      d.table(['Field', 'Value'], rows);
    }
  }
  d.src(P.training(s));

  // Evals
  d.blank().p('## Evals', '');
  const ev = Object.entries(m.evals);
  const evFail = ev.filter(([, v]) => v !== true);
  d.p(`WorldForge build evals: ${ev.length - evFail.length} of ${ev.length} pass${evFail.length ? `; failing: ${evFail.map(([k]) => code(k)).join(', ')}` : ''}.`, '');
  d.p(ev.map(([k, v]) => `${code(k)} ${v === true ? 'pass' : 'FAIL'}`).join(' · '));
  if (aw) {
    const ac = Object.entries(aw.checks);
    const af = ac.filter(([, v]) => v !== true);
    d.blank().p(`Avatar checks: ${ac.length - af.length} of ${ac.length} pass${af.length ? `; failing: ${af.map(([k]) => code(k)).join(', ')}` : ''}.`);
  }
  d.blank().p(`Onchain per-world evals (${R.onchain.evals.per_world.length}, network failing: ${R.onchain.evals.failing.length}): ${R.onchain.evals.per_world.map(code).join(', ')}.`);
  d.src(P.manifest(s) + '#evals', SRC.avatars + `#worlds[slug=${s}].checks`, SRC.onchain + '#evals');

  // Gaps
  d.blank().p('## Gaps', '');
  const gaps = [...W.cards.gaps.map((g) => `${g} (from ${code(P.cards(s) + '#gaps')})`)];
  if (F.world.omega_steward?.status) gaps.push(`Omega Steward is ${F.world.omega_steward.status}: no agent is seated (from ${code(P.cards(s) + '#world:' + s + '.omega_steward')}).`);
  const emptySeats = F.cards.filter((c) => c.kind === 'seat' && c.seated === null).length;
  if (emptySeats) gaps.push(`${emptySeats} human steward ${emptySeats === 1 ? 'seat is' : 'seats are'} empty.`);
  const missingModels = [...new Set(F.buildings.flatMap((c) => [c.building.exterior, c.building.interior, c.building.room]).filter((p) => !exists(p)))];
  if (missingModels.length) gaps.push(`Building model files not present: ${missingModels.map(code).join(', ')}.`);
  const missingAvatarModels = [...new Set(F.avatarRows.map((r) => r.model_ref).filter((p) => p && !exists(p)))];
  if (missingAvatarModels.length) gaps.push(`Avatar models not present: ${missingAvatarModels.map(code).join(', ')}.`);
  const unvoiced = F.avatarRows.filter((r) => r.kind !== 'omega' && !F.voicedOf(r));
  if (unvoiced.length) gaps.push(`${unvoiced.length} intro ${unvoiced.length === 1 ? 'line is' : 'lines are'} not voiced: ${unvoiced.map((r) => r.name).join(', ')}.`);
  const unrec = F.omegaLines.filter((l) => !l.recorded);
  if (unrec.length) gaps.push(`Omega lines not recorded: ${unrec.map((l) => code(l.id)).join(', ')}.`);
  if (!F.omega) gaps.push('No Omega persona in the hive.');
  if (!F.landmark) gaps.push('No landmark model.');
  if (!W.collection) gaps.push('No onchain collection.');
  if (!W.training) gaps.push('Training data not built yet.');
  else for (const g of W.training.gaps || []) gaps.push(`Training: ${g} (from ${code(P.training(s) + '#gaps')})`);
  if (W.entry.failed?.length) gaps.push(`Index lists failing evals: ${W.entry.failed.map(code).join(', ')}.`);
  for (const [g, v] of Object.entries(m.gates)) if (v !== 'done') gaps.push(`Gate ${g}: ${v}.`);
  d.p(...gaps.map((g) => `- ${g}`));
  d.src(P.cards(s) + '#gaps', P.manifest(s) + '#gates', SRC.voices, SRC.hive, P.training(s));

  return d;
}

// ---------- network README ----------
function readmeDoc(R, FS) {
  const d = new Doc(`${OUT_REL}/README.md`);
  const T = R.index.totals;
  const sum = (f) => FS.reduce((a, F) => a + f(F), 0);
  const hiveForWorlds = R.hive.omegas.filter((o) => FS.some((F) => F.s === o.world));
  const hiveLines = hiveForWorlds.reduce((a, o) => a + o.lines.length, 0);
  const recorded = sum((F) => F.omegaRecorded);
  const buildings = sum((F) => F.buildings.length);

  d.p('# SmartCiti.X worlds: GLEWME network overview', '');
  d.p(`${R.index.owner} · ${R.index.umbrella}. ${R.index.totals.worlds} agentic virtual worlds, each described card by card in its own overview. Every number below is read from a registry at build time by ${code('worldforge/overview.mjs')}; the source path sits next to it.`, '');
  d.p(`Open the ${d.link('3-D viewer', SRC.viewer)} or the ${d.link('WorldForge console', SRC.console)}.`);

  d.blank().p('## Totals', '');
  d.table(['Measure', 'Value', 'Source'], [
    ['Worlds', fmt(T.worlds), SRC.index + '#totals.worlds'],
    ['Master Cards', fmt(T.cards), SRC.index + '#totals.cards'],
    ['Zone cards', fmt(sum((F) => F.zones.length)), 'worldforge/out/<slug>/cards.json'],
    ['Agent cards', fmt(sum((F) => F.agents.length)), 'worldforge/out/<slug>/cards.json'],
    ['Cards with a building', fmt(buildings), 'worldforge/out/<slug>/cards.json#cards[].building'],
    ['Blockout primitives', fmt(T.primitives), SRC.index + '#totals.primitives'],
    ['WorldForge build evals (failed)', `${fmt(T.evals)} (${fmt(T.failed)})`, SRC.index + '#totals'],
    ['Worlds with an RP1 anchor', fmt(T.anchored), SRC.index + '#totals.anchored'],
    ['Avatars', `${fmt(R.avatars.totals.avatars)}: ${fmt(R.avatars.totals.specialists)} specialists, ${fmt(R.avatars.totals.coordinators)} coordinators, ${fmt(R.avatars.totals.advisors)} advisors, ${fmt(R.avatars.totals.omegas)} Omegas`, SRC.avatars + '#totals'],
    ['Voiced intro lines', `${fmt(R.voices.totals.lines)} (${R.voices.totals.seconds} s)`, SRC.voices + '#totals'],
    ['Omega voice lines for these worlds (recorded)', `${fmt(hiveLines)} (${fmt(recorded)})`, SRC.hive + '#omegas[].lines'],
    ['Landmarks (triangles)', `${fmt(R.landmarks.totals.worlds)} (${fmt(R.landmarks.totals.triangles)})`, SRC.landmarks + '#totals'],
    ['Landmark height range', `${R.landmarks.totals.min_height_m} to ${R.landmarks.totals.max_height_m} m`, SRC.landmarks + '#totals'],
    ['Onchain-ready tokens (deployed)', `${fmt(R.onchain.totals.tokens)} (${R.onchain.status})`, SRC.onchain + '#totals,status'],
    ['Onchain network root', code(R.onchain.network_root), SRC.onchain + '#network_root'],
    ['Mount plans / nodes', `${fmt(R.conformance.totals.plans)} / ${fmt(R.conformance.totals.nodes)}`, SRC.conformance + '#totals'],
    ['Native conformance violations', fmt(R.conformance.totals.native.violations), SRC.conformance + '#totals.native'],
  ]);

  d.blank().p('## The GLEWME model', '');
  const sample = FS[0].cards;
  const rights = R.worlds[0].cards.rights;
  d.p(`**Master Cards.** Every object in a world is one card (${code(R.worlds[0].cards.schemaVersion)}), owned by ${R.index.owner} and carrying the umbrella "${R.index.umbrella}". Cards form one tree per world through ${code('parentCardId')}: world, then plaza (a coordinator and scripted advisors), the Alignment Evaluation Gate, the Steward Council with its human seats, the Omega Steward, and zones holding agent avatars. Across the network the kinds are: ${Object.entries(R.onchain.totals.by_kind).map(([k, n]) => `${k} ${fmt(n)}`).join(', ')}.`, '');
  d.p(`**Volum.** Each card covers a bounded 3-D region, stored as a box centre and half-extents in metres (shapes used: ${[...new Set(FS.flatMap((F) => F.cards.map((c) => c.volum.shape)))].join(', ')}).`, '');
  d.p(`**Permissions.** Each card has a matrix over ${rights.length} rights: ${rights.map(code).join(', ')}. Holders are ${[...new Set(FS.flatMap((F) => F.cards.flatMap((c) => Object.values(c.permissions).flat())))].sort().map(code).join(', ')}. ${R.pbc.reserved_for_humans.length} actions are reserved for people and held for the Steward Council by a ${sample[0].reserved_for_humans[0].held_for.quorum} quorum of ${sample[0].reserved_for_humans[0].held_for.seats} seats: ${R.pbc.reserved_for_humans.map(code).join(', ')}.`, '');
  d.p(`**Agents operate; people govern.** That is the principle written on every cards file. Agents, coordinators, advisors and the Omega Steward list the reserved actions in ${code('may_never')}; council seats are human seats (all ${fmt(sum((F) => F.cards.filter((c) => c.kind === 'seat' && c.seated === null).length))} empty today); every Omega Steward is ${[...new Set(FS.map((F) => F.world.omega_steward?.status))].join(', ')}.`);
  d.src('worldforge/out/<slug>/cards.json', SRC.pbc, SRC.onchain + '#totals.by_kind');

  d.blank().p('## Worlds', '');
  d.p(`Kind is the landmark style, which ${code(SRC.landmarks)} assigns by a rule on each world's registry entry (see the key below). Voiced lines count rendered intro lines plus recorded Omega lines.`, '');
  d.table(['World', 'Kind', 'Zone cards', 'Agents', 'Buildings', 'Landmark height', 'Voiced lines', 'Anchor'], FS.map((F) => [
    d.link(F.world.name, P.overview(F.s)), F.landmark?.style || 'none', fmt(F.zones.length), fmt(F.agents.length), fmt(F.buildings.length),
    F.landmark ? `${F.landmark.height_m} m` : 'none', fmt(F.voicedLines), F.anchored ? `lat ${F.world.anchor.lat.toFixed(3)}, lon ${F.world.anchor.lon.toFixed(3)}` : 'no anchor yet',
  ]));
  const councilCounted = FS.every((F, i) => F.zones.length + 1 === R.worlds[i].entry.zones);
  if (councilCounted) d.blank().p(`Zone cards exclude the Steward Council: every spec lists it as a zone, but it is merged into the council card, so ${code(SRC.index)} reports one more zone per world than the table.`);
  d.blank().p('### Kind key', '');
  d.table(['Style', 'Worlds', 'Rule'], Object.entries(R.landmarks.styles).map(([k, v]) => [k, fmt(v.count), v.basis]));
  d.src(SRC.index + '#worlds', SRC.landmarks + '#styles,worlds', SRC.voices, SRC.hive);

  d.blank().p('## Roadmap and gates', '');
  d.p(`${R.roadmap.note}`, '');
  d.p('### Family roadmap', '');
  for (const ph of R.roadmap.phases) {
    d.p(`#### ${ph.name} (${ph.status})`, '');
    d.p(...ph.items.map((i) => `- ${i}`));
    d.blank().p(`**Human gate:** ${ph.gate}`, '');
  }
  d.src(SRC.roadmap + '#phases');
  d.blank().p('### WorldForge gates', '');
  const gateNames = Object.keys(R.worlds[0].manifest.gates);
  d.table(['Gate', 'Status across worlds'], gateNames.map((g) => {
    const c = new Map();
    for (const W of R.worlds) { const v = W.manifest.gates[g] ?? 'missing'; c.set(v, (c.get(v) || 0) + 1); }
    return [g, [...c].map(([v, n]) => `${v} (${n})`).join('; ')];
  }));
  d.blank().p(`Gates 1.2n and 1.4 need the Sneeze native host and a rendered frame (status strings above). Beside these engineering gates sit the human ones: ${T.worlds - T.anchored} worlds have no RP1 anchor until a steward writes one (cards.json gaps), all ${fmt(sum((F) => F.cards.filter((c) => c.kind === 'seat' && c.seated === null).length))} steward seats wait on ${code('steward.appoint')}, which is reserved for the Steward Council, and nothing onchain is deployed or minted.`);
  d.src('worldforge/out/<slug>/manifest.json#gates', SRC.index + '#totals.anchored');
  return d;
}

// ---------- evals ----------
const PII = [
  [/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/, 'email'],
  [/\bsk-[A-Za-z0-9_-]{16,}/, 'secret key'],
  [/-----BEGIN [A-Z ]*PRIVATE KEY-----/, 'private key'],
  [/\bAKIA[0-9A-Z]{16}\b/, 'access key'],
  [/\b0x[0-9a-fA-F]{40}\b/, 'address'],
  [/\b(?:postgres|postgresql):\/\/[^\s)]+/, 'connection string'],
  [/\/(?:Users|home)\/[A-Za-z0-9._-]+\//, 'absolute home path'],
];
const CARD_RE = /`((?:world|plaza|coordinator|advisor|gate|council|seat|omega|zone|agent):[a-z0-9][a-z0-9/_.-]*)`/g;
const LINK_RE = /\]\(([^)\s]+)\)/g;

function linkTargets(text, fileRel) {
  const out = [];
  for (const m of text.matchAll(LINK_RE)) {
    const t = m[1];
    if (/^[a-z]+:\/\//i.test(t) || t.startsWith('#') || t.startsWith('mailto:')) continue;
    out.push(path.posix.normalize(path.posix.join(path.posix.dirname(fileRel), t.split(/[?#]/)[0])));
  }
  return out;
}
function docEvals(text, fileRel, knownIds, generated = new Set(), requireIds = true) {
  const res = {};
  const ids = [...text.matchAll(CARD_RE)].map((m) => m[1]);
  res.card_ids_exist = (!requireIds || ids.length > 0) && ids.every((id) => knownIds.has(id));
  res.links_resolve = linkTargets(text, fileRel).every((t) => exists(t) || generated.has(t));
  res.never_forbidden_name = !text.includes(FORBIDDEN);
  res.no_pii_or_keys = !PII.some(([re]) => re.test(text));
  return res;
}

function build() {
  const R = loadAll();
  const FS = R.worlds.map((W) => facts(R, W));
  const docs = R.worlds.map((W, i) => worldDoc(R, W, FS[i]));
  const readme = readmeDoc(R, FS);
  return { R, FS, docs, readme };
}

function run() {
  const A = build();
  const B = build(); // deterministic: a second build must match byte for byte
  const files = new Map();
  for (const d of [...A.docs, A.readme]) files.set(d.rel, d.text());
  const filesB = new Map([...B.docs, B.readme].map((d) => [d.rel, d.text()]));
  const { R, FS } = A;

  const evals = [];
  const add = (scope, name, ok, why = '') => evals.push({ scope, name, ok: !!ok, why });
  const allIds = new Set(FS.flatMap((F) => F.cards.map((c) => c.cardId)));
  const gen = new Set(files.keys()); // generated pages count as existing link targets

  A.docs.forEach((d, i) => {
    const F = FS[i];
    const W = R.worlds[i];
    const text = files.get(d.rel);
    const known = new Set(F.cards.map((c) => c.cardId));
    add(F.s, 'file_for_world', text && d.rel === P.overview(F.s));
    for (const [k, v] of Object.entries(docEvals(text, d.rel, known, gen))) add(F.s, k, v);
    add(F.s, 'recorded_card_ids_exist', [...d.cardIds].every((id) => known.has(id)));
    add(F.s, 'recorded_links_exist', d.links.every((t) => exists(t) || gen.has(t)));
    add(F.s, 'sections_present', SECTIONS.every((h) => text.includes(`\n## ${h}\n`)));
    add(F.s, 'viewer_and_console_linked', text.includes(`viewer.html?world=${F.s})`) && text.includes(`index.html?world=${F.s})`));
    add(F.s, 'cards_match_registries', F.cards.length === W.entry.cards && F.cards.length === W.manifest.counts.cards && (!W.collection || W.collection.token_count === F.cards.length));
    add(F.s, 'agents_match_registries', F.agents.length === W.manifest.counts.agents && F.agents.length === W.entry.agents);
    add(F.s, 'avatars_match_registry', !!F.avatarWorld && F.avatarRows.length === F.avatarWorld.avatars);
    add(F.s, 'zones_match_registry', F.zones.length + 1 === W.entry.zones && W.manifest.counts.zones === W.entry.zones);
    add(F.s, 'plan_nodes_match', W.plan.nodes.length === W.manifest.counts.planNodes && (!F.conf || F.conf.nodes === W.plan.nodes.length));
    add(F.s, 'every_card_in_tree', F.cards.every((c) => text.includes(code(c.cardId))));
    add(F.s, 'not_deployed_stated', !W.collection || (W.collection.deployment.status === 'not deployed' && text.includes('**Not deployed.**')));
    add(F.s, 'anchor_stated', F.anchored ? text.includes(F.world.anchor.rp1) : text.includes('no anchor yet'));
    add(F.s, 'training_stated', W.training ? text.includes('Training data is present at') : text.includes('Not built yet'));
    add(F.s, 'deterministic', filesB.get(d.rel) === text);
  });

  // network
  const rd = files.get(A.readme.rel);
  const T = R.index.totals;
  const sum = (f) => FS.reduce((a, F) => a + f(F), 0);
  for (const [k, v] of Object.entries(docEvals(rd, A.readme.rel, allIds, gen, false))) add('network', 'readme_' + k, v);
  add('network', 'readme_recorded_links_exist', A.readme.links.every((t) => exists(t) || gen.has(t)));
  add('network', 'every_world_has_file', R.index.worlds.every((w) => files.has(P.overview(w.slug))) && A.docs.length === T.worlds);
  add('network', 'readme_indexes_every_world', R.index.worlds.every((w) => rd.includes(`(${w.slug}.md)`)));
  add('network', 'total_worlds', FS.length === T.worlds && R.avatars.totals.worlds === T.worlds && R.landmarks.totals.worlds === T.worlds && R.onchain.totals.worlds === T.worlds && R.conformance.totals.plans === T.worlds);
  add('network', 'total_cards', sum((F) => F.cards.length) === T.cards && R.onchain.totals.cards === T.cards && R.onchain.totals.tokens === T.cards);
  add('network', 'total_cards_by_kind', Object.entries(R.onchain.totals.by_kind).every(([k, n]) => sum((F) => F.cards.filter((c) => c.kind === k).length) === n));
  add('network', 'total_anchored', FS.filter((F) => F.anchored).length === T.anchored);
  add('network', 'total_avatars', R.avatars.rows.length === R.avatars.totals.avatars && sum((F) => F.avatarRows.length) === R.avatars.totals.avatars);
  add('network', 'total_specialists', sum((F) => F.agents.length) === R.avatars.totals.specialists);
  add('network', 'total_voiced_intros', R.voices.lines.length === R.voices.totals.lines && sum((F) => F.introVoiced) === R.voices.totals.lines);
  add('network', 'total_landmarks', FS.filter((F) => F.landmark).length === R.landmarks.totals.worlds);
  add('network', 'total_plan_nodes', sum((F) => R.worlds.find((W) => W.slug === F.s).plan.nodes.length) === R.conformance.totals.nodes);
  add('network', 'total_primitives', R.worlds.reduce((a, W) => a + W.manifest.counts.primitives, 0) === T.primitives);
  add('network', 'total_world_evals', R.worlds.reduce((a, W) => a + Object.keys(W.manifest.evals).length, 0) <= T.evals);
  add('network', 'readme_deterministic', filesB.get(A.readme.rel) === rd);

  // discrimination: each doc eval must fail on a deliberately broken copy
  const F0 = FS[0];
  const base = files.get(P.overview(F0.s));
  const known0 = new Set(F0.cards.map((c) => c.cardId));
  const broken = [
    ['card_ids_exist', base + `\n${code(`agent:${F0.s}/no-such-agent`)}\n`],
    ['links_resolve', base + '\n[missing](../no-such-file.json)\n'],
    ['never_forbidden_name', base + `\n${FORBIDDEN}\n`],
    ['no_pii_or_keys', base + '\nsomeone@example.org\n'],
  ];
  for (const [want, text] of broken) {
    const r = docEvals(text, P.overview(F0.s), known0, gen);
    const failed = Object.entries(r).filter(([, v]) => !v).map(([k]) => k);
    add('broken', `broken_${want}_discriminated`, failed.length === 1 && failed[0] === want, failed.join(','));
  }
  return { files, evals };
}

// ---------- main ----------
const { files, evals } = run();
const failing = evals.filter((e) => !e.ok);
const words = [...files.values()].reduce((a, t) => a + (t.match(/\S+/g) || []).length, 0);
const worldsN = files.size - 1;

const onDisk = fs.existsSync(OUT) ? fs.readdirSync(OUT).filter((f) => f.endsWith('.md')).map((f) => `${OUT_REL}/${f}`) : [];
if (CHECK) {
  const stale = [];
  for (const [rel, text] of files) if (!exists(rel) || fs.readFileSync(abs(rel), 'utf8') !== text) stale.push(rel);
  for (const rel of onDisk) if (!files.has(rel)) stale.push(rel + ' (not generated)');
  if (stale.length || failing.length) {
    for (const s of stale.slice(0, 20)) console.log('stale: ' + s);
    for (const e of failing) console.log(`FAIL ${e.scope} ${e.name}${e.why ? ' (' + e.why + ')' : ''}`);
    console.log(`OVERVIEW: ${worldsN} worlds, ${stale.length} stale, ${evals.length} evals, ${failing.length} failing`);
    process.exit(1);
  }
  console.log('overview current');
} else {
  fs.mkdirSync(OUT, { recursive: true });
  for (const rel of onDisk) if (!files.has(rel)) fs.unlinkSync(abs(rel));
  for (const [rel, text] of files) if (!exists(rel) || fs.readFileSync(abs(rel), 'utf8') !== text) fs.writeFileSync(abs(rel), text);
  for (const e of failing) console.log(`FAIL ${e.scope} ${e.name}${e.why ? ' (' + e.why + ')' : ''}`);
}
console.log(`OVERVIEW: ${worldsN} worlds, ${fmt(words)} words, ${evals.length} evals, ${failing.length} failing`);
process.exit(failing.length ? 1 : 0);
