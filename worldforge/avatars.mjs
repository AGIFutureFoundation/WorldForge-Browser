// WorldForge avatar registry: every avatar in the 41 worlds, bound to the card and the record it speaks for.
//   node worldforge/avatars.mjs           # writes worldforge/out/avatars/, runs the registry evals, exit 1 on any failure
//   node worldforge/avatars.mjs --check   # rebuilds in memory; exit 1 if anything on disk differs or any eval fails.
//                                         # The final line always ends "<N> failing", stale or not.
//
// One row per avatar. row.kind says what it is; row.role is its avatar model role (worldforge/out/assets/avatars/<role>.glb).
//   specialist   one per agent card in worldforge/out/<slug>/cards.json, bound to its swarm agent and house metaprompt.
//   coordinator  one per world, LINKED to its coordinator card (coordinator:<slug>, parented to the plaza) and placed from
//                that card's volum; bound to agents/swarms/<slug>.json .coordinator. The same row is mirrored at
//                worlds[i].coordinator in the shape worldforge/viewer.html reads: volum.center as an [x, y, z] array
//                (metres, world frame, Y up) and facing as a unit [x, 0, z] vector derived from the plaza and card centres.
//   advisor      three per world, LINKED to the advisor cards (advisor:<slug>/<host|steward|alignment>); role is the card's
//                avatar.role (host / liaison / alignment). Advisors are scripted guides (agents/advisors/<slug>.json), not
//                AI models and not people. By the house advisor contract ("Advisors get no prompt", agents/metaprompt.mjs)
//                they carry persona_prompt_id null and no metaprompt binding. Their intro is built only from the advisor
//                record's name and manages.
//   omega        one per omega card, LINKED to its Omega Hive record by id (agents/hive/index.json); persona, voice and
//                spoken lines stay in the hive, this row only points at them.
// Every specialist, coordinator and omega gets a persona metaprompt (worldforge/out/avatars/prompts/<slug>.md + .json)
// that binds it to its card: identity and citation, routing keywords, the card's 7-right permission table, and the
// house metaprompt from agents/prompts/<slug>.json reproduced unchanged (umbrella, the six reserved actions held for the
// Steward Council, forbidden actions, management model, personal-data refusal, not-advice line). Every prompt is gated by
// evalPrompt from agents/metaprompt.mjs plus the avatar gates below.
//
// Audio. Every row stores the expected path from the avatar audio path contract,
//   worldforge/out/voices/<world>/<last path segment of avatarId>.mp4
// and nothing about whether that file exists: a voiced/exists flag changes as lines are rendered, so it is never stored.
// Viewers HEAD-check the path at runtime. Omega rows also point at the hive's own line audio (voice.audio.greet, ...).
//
// What is NOT claimed. No model runs these prompts. This generator renders no audio (worldforge/voice/voice_intros.py
// renders non-omega intros; the hive voices omega lines). The avatar GLBs are referenced by role and built elsewhere.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { evalPrompt, PBC, MAX_PROMPT_CHARS, specialistPrompt, coordinatorPrompt } from '../agents/metaprompt.mjs';
import { redactPII } from '../agents/fabric/agent.mjs';
import { AVATAR_ROLES, AVATAR_DIR, RIGHTS, NAME_LIMIT, nodeName } from './build.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');
const OUT = path.join(HERE, 'out', 'avatars');
const OUT_REL = 'worldforge/out/avatars';
const R = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const has = (p) => fs.existsSync(path.join(ROOT, p));
const CHECK = process.argv.includes('--check');
const stable = (v) => JSON.stringify(v, null, 1) + '\n';
const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const words = (s) => s.trim().split(/\s+/).filter(Boolean).length;
const fnv = (s) => { let h = 2166136261; for (const c of s) { h ^= c.codePointAt(0); h = Math.imul(h, 16777619) >>> 0; } return h; };

export const SOURCES = ['worldforge/out/<slug>/cards.json', 'agents/swarms/<slug>.json', 'agents/prompts/<slug>.json', 'agents/advisors/<slug>.json (name, manages)',
  'agents/hive/index.json (id, world, voice only)', 'agents/hive.mjs (ENGLISH_VOICES, read as text)', 'my-fabric/worlds/index.json', 'worlds/<slug>/spec.json',
  'worlds/generated/teams/<slug>.json (.brand)', 'worlds/PBC.json'];
export const AGENT_LINE = 'You are an agent with a synthetic voice, not a person.';
export const VOICE_DIR = 'worldforge/out/voices';
export const AUDIO_CONTRACT = `${VOICE_DIR}/<world>/<last path segment of avatarId>.mp4`;
export const ADVISOR_LINE = 'Scripted guide, synthetic voice: not an AI model, not a person.';
const ADVISOR_MUST_SAY = ['Scripted guide', 'synthetic voice', 'not an AI model', 'not a person'];
const MAX_INTRO_WORDS = 25;
const KEY_SHAPED = /(sk-[A-Za-z0-9]{8,}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|0x[0-9a-fA-F]{40}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,})/;
const SEGMENT = /^[a-z0-9][a-z0-9-]{0,47}$/;        // the world / path-segment shape worldforge/voice/voice_intros.py accepts
const VOLATILE_KEYS = new Set(['status', 'voiced', 'exists', 'audio_exists', 'on_disk', 'rendered', 'present']);
const FACING_FROM = 'unit XZ vector from the plaza card centre to the coordinator card centre (derived from the two cards; the card itself carries no facing)';
const KINDS = ['coordinator', 'advisor', 'specialist', 'omega'];

// ------------------------------------------------------------------------------------------ voice pool ----
// agents/hive.mjs runs its main on import, so its English voice list is READ from the source text, never imported.
// The hive leaves out the voice it filters from ENGLISH_VOICES (a character voice); avatars leave out the same one.
function hiveVoicePool() {
  const src = fs.readFileSync(path.join(ROOT, 'agents/hive.mjs'), 'utf8');
  const m = src.match(/const ENGLISH_VOICES = \[([\s\S]*?)\];/);
  if (!m) throw new Error('agents/hive.mjs: ENGLISH_VOICES not found; cannot pick avatar voices');
  const english = [...m[1].matchAll(/'([a-z]{2}_[a-z]+)'/g)].map((x) => x[1]);
  const excluded = [...src.matchAll(/ENGLISH_VOICES\.filter\(\(v\) => v !== '([a-z]{2}_[a-z]+)'\)/g)].map((x) => x[1]);
  return { english, excluded, pool: english.filter((v) => !excluded.includes(v)) };
}
const VOICES = hiveVoicePool();

/** Deterministic, never random: one 32-bit FNV-1a hash h of the avatar id drives every choice.
 *    id    = pool[h % pool.length]                        (pool = the hive's ENGLISH_VOICES minus the voice it filters out)
 *    speed = [0.92, 0.96, 1.0, 1.04, 1.08][h % 5]          (also the browser fallback rate)
 *    pitch = af_/bf_ ids: [1.05, 1.1, 1.15][h % 3]; every other id: [0.85, 0.9, 0.95][h % 3]
 *    lang  = en-GB for bf_/bm_ ids, else en-US
 *  The speed, pitch and lang tables are the ones agents/hive.mjs applies to Omegas; the hive hashes the world slug and
 *  picks the Omega's id by striding its pool, where this hashes the avatar id for both. Omega rows never call this:
 *  they reuse the hive's voice. Used for specialist, coordinator and advisor rows. */
export function pickVoice(avatarId) {
  const h = fnv(avatarId);
  const id = VOICES.pool[h % VOICES.pool.length];
  const female = /^(af|bf)_/.test(id);
  const rate = [0.92, 0.96, 1.0, 1.04, 1.08][h % 5];
  const pitch = female ? [1.05, 1.1, 1.15][h % 3] : [0.85, 0.9, 0.95][h % 3];
  return { id, speed: rate, browser_fallback: { pitch, rate, lang: /^b[fm]_/.test(id) ? 'en-GB' : 'en-US' } };
}

/** The avatar audio path contract: worldforge/out/voices/<world>/<last path segment of avatarId>.mp4. */
export function audioPath(world, avatarId) {
  return `${VOICE_DIR}/${world}/${String(avatarId).split('/').pop()}.mp4`;
}

/** View time only (printed, never stored): is the contract audio for this row on disk right now? */
export function audioOnDiskAtViewTime(row, exists = has) {
  return typeof row.audio === 'string' && exists(row.audio);
}

// ------------------------------------------------------------------------------------------- helpers ----
/** The house common block (umbrella, reserved actions, forbidden actions, rules), cut from the house coordinator prompt. */
function houseCommon(spec, coordText) {
  const head = `World: ${spec.name} (${spec.umbrella}). Status: ${spec.status}.`;
  const i = coordText.indexOf(head);
  return i >= 0 ? coordText.slice(i) : null;
}
const permissionLines = (perm) => RIGHTS.map((r) => `  - ${r}: ${(perm?.[r] ?? []).join(', ') || 'nobody'}`);
const agentRights = (perm) => RIGHTS.filter((r) => (perm?.[r] ?? []).some((h) => h.startsWith('agents')));
function reservedLine(card, own) {
  const held = card.reserved_for_humans?.[0]?.held_for;
  return `${own ? 'Your card' : 'That card'} holds the ${card.reserved_for_humans.length} reserved actions for the ${held?.holder} (quorum ${held?.quorum}, ${held?.seats} human seats): ${card.reserved_for_humans.map((x) => x.action).join(', ')}.`;
}
const article = (name) => (/^the\s/i.test(name) ? name : `the ${name}`);
const firstFit = (cands) => cands.find((t) => words(t) <= MAX_INTRO_WORDS) ?? cands[cands.length - 1];
const aabbOverlapXZ = (a, b) => [0, 2].every((i) => Math.abs(a.center[i] - b.center[i]) < a.halfExtents[i] + b.halfExtents[i]);
const round2 = (x) => Math.round(x * 100) / 100;
const round4 = (x) => Math.round(x * 1e4) / 1e4 + 0;
const isVec3 = (a) => Array.isArray(a) && a.length === 3 && a.every(Number.isFinite);
const sameVec = (a, b) => isVec3(a) && isVec3(b) && a.every((x, i) => x === b[i]);
const fromCard = (card) => ({ from: card.cardId, center: [...card.volum.center], halfExtents: [...card.volum.halfExtents] });
const lastSeg = (id) => String(id).split('/').pop();

/** Unit [x, 0, z] from the plaza centre to a point, or null when the point is the plaza centre. */
export function outwardFacing(plazaCenter, center) {
  const dx = center[0] - plazaCenter[0], dz = center[2] - plazaCenter[2], len = Math.hypot(dx, dz);
  return len < 1e-9 ? null : [round4(dx / len), 0, round4(dz / len)];
}

/** Every intro an advisor may speak, built only from its record's name and manages; the first that fits is used. */
export function advisorIntroCandidates(rec) {
  return [`I am ${article(rec.name)}: ${rec.manages}. ${ADVISOR_LINE}`, `I am ${article(rec.name)}. ${ADVISOR_LINE}`];
}
const advisorIntro = (rec) => firstFit(advisorIntroCandidates(rec));

/** Recursive scan for keys that would store a volatile voiced/exists state. */
function volatileKeys(v, at = '') {
  if (!v || typeof v !== 'object') return [];
  return Object.entries(v).flatMap(([k, x]) => [...(VOLATILE_KEYS.has(k) ? [`${at}${k}`] : []), ...volatileKeys(x, `${at}${k}.`)]);
}

// ------------------------------------------------------------------------------------------ zones ----
// Where each zone string comes from (every one is a registry or card field, or the label a card's displayName is made of):
//   specialist   its swarm agent's zone (= its parent zone card's name).
//   coordinator, advisor   the plaza their cards are parented to: "<world> Plaza", the label worldforge/build.mjs gives
//                the plaza card (its displayName is nodeName of that label, truncated for long world names).
//   omega        the council card's name. That name is the spec's own Steward Council zone (my-fabric/worlds/index.json),
//                which worldforge/build.mjs folds into the council card. The omega card stands OUTSIDE the council card
//                (its parent is the world card); zone_from records the measured edge gap, and the claim is only accepted
//                while that gap is positive and the card is not parented to the council or a seat.
const councilOf = (ctx) => ctx.cards.find((c) => c.kind === 'council') ?? null;
const coordCardOf = (ctx) => ctx.cards.find((c) => c.kind === 'coordinator') ?? null;
const omegaZone = (ctx) => councilOf(ctx)?.name ?? null;
const plazaZone = (ctx) => `${ctx.worldCard.name} Plaza`;
/** XZ edge gap (metres) between the omega card and the council card; > 0 means the omega stands off the council. */
function omegaCouncilGap(ctx, card) {
  const cl = councilOf(ctx);
  if (!cl || !card) return null;
  return round2(Math.max(...[0, 2].map((i) => Math.abs(card.volum.center[i] - cl.volum.center[i]) - (card.volum.halfExtents[i] + cl.volum.halfExtents[i]))));
}
function zoneFrom(ctx, kind, card, agentId) {
  if (kind === 'specialist') return `agents/swarms/${ctx.slug}.json#${agentId}.zone (= cards.json#${card.parentCardId}.name)`;
  if (kind === 'coordinator' || kind === 'advisor') return `cards.json#${card?.parentCardId ?? ctx.plaza.cardId}: the label "<world> Plaza" worldforge/build.mjs gives that plaza card (its displayName is nodeName of the label); <world> = cards.json#${ctx.worldCard.cardId}.name`;
  const cl = councilOf(ctx);
  return {
    field: `cards.json#${cl?.cardId}.name`, spec_zone: `my-fabric/worlds/index.json#worlds[slug=${ctx.slug}].zones[name=${cl?.name}]`,
    omega_card: card.cardId, parent: card.parentCardId, outside_card: cl?.cardId ?? null, edge_gap_m: omegaCouncilGap(ctx, card),
    held_by: 'worldforge/build.mjs omega_off_council; nothing_invented here',
  };
}

// --------------------------------------------------------------------------------- viewer contract ----
/** The coordinator as worldforge/viewer.html reads it (worlds[i].coordinator): a mirror of the coordinator row with
 *  volum.center / volum.halfExtents as [x, y, z] arrays and facing as a unit [x, 0, z] vector. Derived from the rows only. */
export function viewerCoordinator(rows, ctx) {
  const r = rows.find((x) => x.kind === 'coordinator');
  if (!r) return null;
  const card = ctx.byId.get(r.permissions_from);
  const p = r.position ?? {};
  return {
    avatarId: r.avatarId, cardId: r.cardId, kind: 'coordinator', role: 'coordinator', world: r.world, name: r.name, displayName: r.displayName,
    role_text: r.role_text, zone: r.zone, source: r.source, model_ref: r.model_ref, tint_hue: r.tint_hue, audio: r.audio,
    volum: { center: p.center ? [...p.center] : null, halfExtents: p.halfExtents ? [...p.halfExtents] : null }, facing: p.facing ? [...p.facing] : null,
    position_from: p.from ? `cards.json#${p.from}.volum` : null, facing_from: p.facing_from ?? null,
    permissions_from: r.permissions_from, permissions: structuredClone(r.permissions), reserved_for_humans: structuredClone(card?.reserved_for_humans ?? []),
    intro: structuredClone(r.intro), voice: structuredClone(r.voice), binding: structuredClone(r.binding), persona_prompt_id: r.persona_prompt_id,
    mirrors: `rows[avatarId=${r.avatarId}]`,
  };
}

// ------------------------------------------------------------------------------------- world context ----
const HIVE = has('agents/hive/index.json') ? R('agents/hive/index.json') : { omegas: [] };
function loadWorld(w) {
  const s = w.slug;
  const cardsDoc = R(`worldforge/out/${s}/cards.json`);
  const cards = cardsDoc.cards;
  const byId = new Map(cards.map((c) => [c.cardId, c]));
  const hiveRec = (HIVE.omegas ?? []).find((o) => o.world === s) ?? null;
  const promptsFile = `agents/prompts/${s}.json`;
  const advisorsFile = `agents/advisors/${s}.json`;
  return {
    w, slug: s, cardsDoc, cards, byId,
    spec: R(`worlds/${s}/spec.json`),
    swarm: R(`agents/swarms/${s}.json`),
    promptsFile, house: has(promptsFile) ? R(promptsFile) : { agents: [] },
    advisorsFile, advisorsDoc: has(advisorsFile) ? R(advisorsFile) : { advisors: [] },
    hive: hiveRec,
    brand: R(`worlds/generated/teams/${s}.json`).brand ?? null,
    worldCard: cards.find((c) => c.kind === 'world'),
    plaza: cards.find((c) => c.kind === 'plaza'),
    gate: cards.find((c) => c.kind === 'gate'),
  };
}
/** The advisor record a card speaks for: agents/advisors/<slug>.json advisors[id = last segment of the cardId]. */
const advisorRecord = (ctx, card) => (ctx.advisorsDoc.advisors ?? []).find((a) => a.id === lastSeg(card?.cardId)) ?? null;

/** House metaprompt text for an id, from agents/prompts/<slug>.json; computed from the same function only if absent. */
function houseText(ctx, id, compute) {
  const rec = ctx.house.agents.find((a) => a.id === id);
  return rec ? { text: rec.text, from: `${ctx.promptsFile}#${id}` } : { text: compute(), from: `computed by agents/metaprompt.mjs (missing from ${ctx.promptsFile})` };
}

// ------------------------------------------------------------------------------------------- prompts ----
function personaPrompt(ctx, row, card, permCard, extra) {
  const L = [];
  L.push(`Avatar persona: ${row.name} - ${row.kind} avatar in ${ctx.worldCard.name} (${PBC.umbrella}).`);
  L.push(`${AGENT_LINE} Say so when you greet someone and whenever you are asked.`);
  if (row.kind === 'omega') L.push(`Status: ${card.status}. No agent is seated in this role and no model runs; you never seat yourself or any other agent.`);
  L.push(`Avatar: ${row.avatarId}; model ${row.model_ref}; tint hue ${row.tint_hue}; Kokoro voice ${row.voice.id} (synthetic${row.kind === 'omega' ? ', the hive voice' : ''}).`);
  L.push(card ? `Card: ${card.cardId} in worldforge/out/${ctx.slug}/cards.json (parent ${card.parentCardId}).`
    : `Card: none - worldforge/out/${ctx.slug}/cards.json has no ${row.kind} card; the permissions below are from ${permCard.cardId}.`);
  L.push(`Identity: ${row.name} in ${ctx.worldCard.name} (status: ${ctx.spec.status}); zone: ${row.zone}; role: ${extra.roleText}; source: ${row.source}.`);
  if (extra.placementLine) L.push(extra.placementLine);
  L.push(extra.bindingLine);
  L.push(extra.keywordLine);
  L.push(`Permission table on ${permCard === card ? 'your card' : `the card you stand on (${permCard.cardId})`} - right: holders${agentRights(permCard.permissions).length ? '; agents:zone means you, inside your own zone only' : ''}:`);
  L.push(...permissionLines(permCard.permissions));
  const mine = agentRights(permCard.permissions);
  const pub = RIGHTS.filter((r) => (permCard.permissions?.[r] ?? []).includes('public'));
  L.push(mine.length ? `Rights you hold as an agent: ${mine.join(', ')}, inside your own zone only. Every other right is held by people.`
    : `Rights you hold as an agent: none beyond what the public holds (${pub.join(', ')}). Every other right is held by people.`);
  L.push(reservedLine(permCard, permCard === card));
  L.push(`Your greeting: "${row.intro.text}"`);
  L.push(extra.houseHeader);
  L.push(extra.house);
  return L.join('\n');
}

/** Avatar gates, on top of every evalPrompt gate. Checked against the card (or the plaza card), never against the row. */
function avatarGates(text, row, permCard) {
  const g = [
    ['says it is an agent with a synthetic voice, not a person', text.includes(AGENT_LINE)],
    ['carries the 7-right permission table from its card', permissionLines(permCard.permissions).every((l) => text.includes(l))],
    ['names its avatar id and its card', text.includes(row.avatarId) && text.includes(row.cardId ? `Card: ${row.cardId}` : 'Card: none')],
  ];
  if (row.kind === 'omega') g.push(['says it is defined, not seated', text.includes('defined, not seated')]);
  return g.map(([name, ok]) => ({ name, ok }));
}

// ---------------------------------------------------------------------------------------------- rows ----
function baseRow(ctx, kind, role, avatarId, fields) {
  return {
    avatarId, kind, cardId: fields.cardId ?? null, world: ctx.slug, world_name: ctx.worldCard.name, world_status: ctx.spec.status,
    name: fields.name, role, zone: fields.zone, zone_from: fields.zone_from, displayName: fields.displayName,
    role_text: fields.role_text ?? null, source: fields.source, keywords: fields.keywords ?? [],
    model_ref: `${AVATAR_DIR}/${role}.glb`, tint_hue: ctx.brand?.hue ?? null,
    position: fields.position,
    permissions_from: fields.permCard.cardId, permissions: structuredClone(fields.permCard.permissions),
    binding: fields.binding, intro: fields.intro, voice: fields.voice,
    audio: audioPath(ctx.slug, avatarId),
    persona_prompt_id: fields.noPrompt ? null : avatarId.replace(/^avatar:/, 'persona:'),
    ...(fields.extra ?? {}),
  };
}
const scriptedVoice = (avatarId) => { const v = pickVoice(avatarId); return { engine: 'kokoro', id: v.id, speed: v.speed, browser_fallback: v.browser_fallback }; };

function specialistRow(ctx, card) {
  const agent = ctx.swarm.agents.find((a) => a.id === card.binding?.swarm) ?? ctx.swarm.agents.find((a) => a.name === card.name);
  const avatarId = `avatar:${ctx.slug}/specialist/${slug(card.name)}`;
  const zone = agent?.zone ?? ctx.byId.get(card.parentCardId)?.name ?? null;
  const name = card.name;
  const world = ctx.worldCard.name;
  const intro = firstFit([
    `I am ${article(name)} for ${world}, in ${zone}. I draft and check; people decide. You are hearing a synthetic voice.`,
    `I am ${article(name)} for ${world}, in ${zone}. People decide. You are hearing a synthetic voice.`,
    `I am ${article(name)} for ${world}. People decide. You are hearing a synthetic voice.`,
    `I am ${article(name)}. You are hearing a synthetic voice.`,
  ]);
  const id = agent?.id ?? card.binding?.swarm;
  const row = baseRow(ctx, 'specialist', 'specialist', avatarId, {
    cardId: card.cardId, name, zone, zone_from: zoneFrom(ctx, 'specialist', card, id), displayName: card.displayName, role_text: card.role, source: card.source, keywords: agent?.keywords ?? [],
    position: fromCard(card),
    permCard: card,
    binding: { swarm: id, metaprompt: { file: ctx.promptsFile, id }, hive: null, fabricNode: card.binding?.fabricNode ?? null },
    intro: { text: intro, words: words(intro), from: `cards.json#${card.cardId} (name, zone) + agents/swarms/${ctx.slug}.json` },
    voice: scriptedVoice(avatarId),
  });
  const house = houseText(ctx, id, () => specialistPrompt(ctx.spec, ctx.swarm, agent));
  const text = personaPrompt(ctx, row, card, card, {
    roleText: card.role,
    bindingLine: `Swarm binding: ${id} in agents/swarms/${ctx.slug}.json; fabric node "${card.binding?.fabricNode}"; house metaprompt ${house.from} (reproduced below unchanged).`,
    keywordLine: `Routing keywords the ${ctx.swarm.coordinator.name} routes to you on: ${(agent?.keywords ?? []).join(', ')}.`,
    houseHeader: '--- House metaprompt ---', house: house.text,
  });
  return { row, text };
}

function coordinatorRow(ctx) {
  const co = ctx.swarm.coordinator;
  const card = coordCardOf(ctx);
  const avatarId = `avatar:${ctx.slug}/coordinator`;
  const zone = plazaZone(ctx);
  // Position is the coordinator card's volum, unchanged; facing is derived from the plaza and card centres.
  const position = card ? { ...fromCard(card), facing: outwardFacing(ctx.plaza.volum.center, card.volum.center), facing_from: FACING_FROM } : null;
  const intro = firstFit([
    `I am ${article(co.name)}, at ${zone}. I route each question to the right specialist; people decide. You are hearing a synthetic voice.`,
    `I am ${article(co.name)}. I route each question to the right specialist; people decide. You are hearing a synthetic voice.`,
    `I am ${article(co.name)}. People decide. You are hearing a synthetic voice.`,
  ]);
  const permCard = card ?? ctx.plaza;
  const keywords = [...new Set(ctx.swarm.agents.flatMap((a) => a.keywords.slice(0, 8)))];
  const source = `agents/swarms/${ctx.slug}.json#coordinator`;
  const row = baseRow(ctx, 'coordinator', 'coordinator', avatarId, {
    cardId: card?.cardId ?? null, name: co.name, zone, zone_from: zoneFrom(ctx, 'coordinator', card), displayName: card?.displayName ?? nodeName(co.name), role_text: ctx.swarm.topology, source,
    position, permCard,
    binding: { swarm: co.id, metaprompt: { file: ctx.promptsFile, id: co.id }, hive: null, fabricNode: card?.binding?.fabricNode ?? null },
    intro: { text: intro, words: words(intro), from: `${source} (name) + cards.json#${card?.parentCardId ?? ctx.plaza.cardId} (its plaza)` },
    voice: scriptedVoice(avatarId),
  });
  const house = houseText(ctx, co.id, () => coordinatorPrompt(ctx.spec, ctx.swarm));
  const text = personaPrompt(ctx, row, card, permCard, {
    roleText: `supervises the swarm (${ctx.swarm.topology})`,
    bindingLine: `Swarm binding: ${co.id} in agents/swarms/${ctx.slug}.json; fabric node "${card?.binding?.fabricNode ?? 'none'}"; house metaprompt ${house.from} (reproduced below unchanged).`,
    keywordLine: `Routing keywords: you route on every specialist's keywords, listed in the routing table below (${ctx.swarm.agents.length} specialists).`,
    houseHeader: '--- House metaprompt ---', house: house.text,
  });
  return { row, text };
}

/** An advisor: a scripted guide with a synthetic voice. No persona prompt and no metaprompt, by the advisor contract. */
function advisorRow(ctx, card) {
  const rec = advisorRecord(ctx, card) ?? { id: lastSeg(card.cardId), name: card.name, manages: card.manages };
  const avatarId = `avatar:${ctx.slug}/advisor/${rec.id}`;
  const intro = advisorIntro(rec);
  const row = baseRow(ctx, 'advisor', card.avatar?.role ?? null, avatarId, {
    cardId: card.cardId, name: rec.name, zone: plazaZone(ctx), zone_from: zoneFrom(ctx, 'advisor', card), displayName: card.displayName, role_text: rec.manages, source: card.source,
    position: fromCard(card), permCard: card,
    binding: { swarm: null, metaprompt: null, hive: null, fabricNode: null, advisor: { file: ctx.advisorsFile, id: rec.id } },
    intro: { text: intro, words: words(intro), from: `${ctx.advisorsFile}#advisors[id=${rec.id}] (name, manages) + the fixed scripted-guide line` },
    voice: scriptedVoice(avatarId),
    noPrompt: true,
    extra: { advisor_id: rec.id, manages: rec.manages, scripted: true, no_prompt: 'advisor contract: advisors get no prompt (agents/metaprompt.mjs); a scripted guide, not an AI model and not a person' },
  });
  return { row, text: null };
}

function omegaRow(ctx, card) {
  const avatarId = `avatar:${ctx.slug}/omega`;
  const hive = ctx.hive;
  const greet = (card.voice?.lines ?? []).find((l) => l.id === 'greet');
  const coordText = houseText(ctx, ctx.swarm.coordinator.id, () => coordinatorPrompt(ctx.spec, ctx.swarm)).text;
  const common = houseCommon(ctx.spec, coordText) ?? houseCommon(ctx.spec, coordinatorPrompt(ctx.spec, ctx.swarm));
  const cl = councilOf(ctx);
  const row = baseRow(ctx, 'omega', 'omega', avatarId, {
    cardId: card.cardId, name: card.name, zone: omegaZone(ctx), zone_from: zoneFrom(ctx, 'omega', card), displayName: card.displayName, role_text: null, source: card.source,
    position: fromCard(card),
    permCard: card,
    binding: { swarm: null, metaprompt: { file: hive?.metaprompt ?? null, id: hive?.id ?? null }, hive: hive?.id ?? null, hive_ref: card.hive_ref ?? null },
    intro: { text: greet?.text ?? '', words: words(greet?.text ?? ''), from: `cards.json#${card.cardId}.voice.lines[id=greet] (the hive greet line)` },
    voice: {
      engine: 'kokoro', id: hive?.voice?.kokoro ?? null, speed: hive?.voice?.speed ?? null, browser_fallback: hive?.voice?.browser_fallback ?? null,
      audio: Object.fromEntries((card.voice?.lines ?? []).map((l) => [l.id, l.audio])),
    },
    extra: { seat_status: card.status, seated_agent: card.seated_agent },
  });
  const text = personaPrompt(ctx, row, card, card, {
    roleText: `Omega Steward (${card.omega_id})`,
    placementLine: `Placement: your card stands ${omegaCouncilGap(ctx, card)} m outside the ${cl?.cardId} card; you never stand on the council card or in a steward seat.`,
    bindingLine: `Hive binding: ${hive?.id} in agents/hive/index.json; your persona, voice and spoken lines are in ${hive?.metaprompt} (linked, not copied).`,
    keywordLine: `Routing keywords: none - the Omega Steward is not in the ${ctx.swarm.coordinator.name}'s routing table; it routes to service cards as its hive metaprompt lists.`,
    houseHeader: `--- House rules for ${ctx.spec.name} (the common block of ${ctx.promptsFile}, unchanged) ---`, house: common ?? '',
  });
  return { row, text };
}

export function buildWorldAvatars(ctx) {
  const built = [
    coordinatorRow(ctx),
    ...ctx.cards.filter((c) => c.kind === 'advisor').map((c) => advisorRow(ctx, c)),
    ...ctx.cards.filter((c) => c.kind === 'agent').map((c) => specialistRow(ctx, c)),
    ...ctx.cards.filter((c) => c.kind === 'omega').map((c) => omegaRow(ctx, c)),
  ];
  return {
    rows: built.map((b) => b.row),
    prompts: new Map(built.filter((b) => b.row.persona_prompt_id !== null).map((b) => [b.row.persona_prompt_id, b.text])),
  };
}

/** Grounding for evalPrompt and the permission table come from the card and swarm, never from the (mutable) row. */
function groundFor(ctx, row) {
  if (row.kind === 'specialist') {
    const card = ctx.byId.get(row.cardId);
    const agent = card && ctx.swarm.agents.find((a) => a.id === card.binding?.swarm);
    return { permCard: card, agent: agent ? { source: agent.source, zone: agent.zone, keywords: agent.keywords } : null };
  }
  if (row.kind === 'coordinator') {
    const card = coordCardOf(ctx) ?? ctx.plaza;
    return { permCard: card, agent: { source: `agents/swarms/${ctx.slug}.json#coordinator`, zone: plazaZone(ctx), keywords: [...new Set(ctx.swarm.agents.flatMap((a) => a.keywords.slice(0, 8)))] } };
  }
  if (row.kind === 'omega') {
    const card = ctx.cards.find((c) => c.kind === 'omega');
    return { permCard: card, agent: { source: card?.source, zone: omegaZone(ctx), keywords: [] } };
  }
  return { permCard: null, agent: null };
}

export function gatePrompt(ctx, row, text) {
  if (typeof text !== 'string') return [{ name: 'prompt exists', ok: false }];
  const { permCard, agent } = groundFor(ctx, row);
  if (!permCard) return [{ name: 'card resolves', ok: false }];
  return [...evalPrompt(text, { spec: ctx.spec, agent }), ...avatarGates(text, row, permCard)];
}

// ---------------------------------------------------------------------------------------------- evals ----
const allPass = (gates) => gates.every((g) => g.ok);
const ofKind = (rows, k) => rows.filter((r) => r.kind === k);
export const CHECKS = {
  one_avatar_per_agent_card: ({ ctx, rows }) => ctx.cards.filter((c) => c.kind === 'agent').every((c) => rows.filter((r) => r.cardId === c.cardId).length === 1)
    && ofKind(rows, 'specialist').every((r) => ctx.byId.get(r.cardId)?.kind === 'agent') && rows.every((r) => KINDS.includes(r.kind)),
  swarm_bound: ({ ctx, rows }) => rows.filter((r) => r.kind === 'specialist' || r.kind === 'coordinator').every((r) => r.kind === 'coordinator'
    ? r.binding.swarm === ctx.swarm.coordinator.id
    : ctx.swarm.agents.some((a) => a.id === r.binding.swarm) && ctx.byId.get(r.cardId)?.binding?.swarm === r.binding.swarm),
  // advisors are held by advisors_have_no_prompt instead (they carry no metaprompt at all)
  metaprompt_bound: ({ ctx, rows }) => rows.filter((r) => r.kind !== 'advisor').every((r) => r.kind === 'omega'
    ? r.binding.metaprompt.file === `agents/hive/prompts/${ctx.slug}.md` && has(r.binding.metaprompt.file) && r.binding.metaprompt.id === `omega.${ctx.slug}`
    : r.binding.metaprompt.file === ctx.promptsFile && ctx.house.agents.some((a) => a.id === r.binding.metaprompt.id)),
  omega_hive_bound: ({ ctx, rows }) => { const oc = ctx.cards.filter((c) => c.kind === 'omega'); const orows = ofKind(rows, 'omega'); return orows.length === oc.length && orows.every((r) => { const h = (HIVE.omegas ?? []).find((o) => o.id === r.binding.hive); return !!h && h.world === ctx.slug && ctx.byId.get(r.cardId)?.omega_id === r.binding.hive; }); },
  model_refs_are_roles: ({ ctx, rows }) => rows.every((r) => { const base = path.basename(r.model_ref, '.glb'); const card = r.cardId ? ctx.byId.get(r.cardId) : null; return AVATAR_ROLES.includes(base) && base === r.role && r.model_ref === `${AVATAR_DIR}/${base}.glb` && (!card?.avatar || card.avatar.model_ref === r.model_ref); }),
  intro_short_and_synthetic: ({ rows }) => rows.every((r) => typeof r.intro?.text === 'string' && words(r.intro.text) <= MAX_INTRO_WORDS && words(r.intro.text) === r.intro.words && /synthetic voice/i.test(r.intro.text)),
  persona_prompts_pass: ({ ctx, rows, prompts }) => rows.filter((r) => r.kind !== 'advisor').every((r) => allPass(gatePrompt(ctx, r, prompts.get(r.persona_prompt_id)))),
  no_pii_or_keys: ({ rows, prompts }) => { const corpus = [JSON.stringify(rows), ...[...prompts.values()].map((t) => t ?? '')].join('\n'); return redactPII(corpus).redactions === 0 && !KEY_SHAPED.test(corpus); },
  // the coordinator CARD sits inside the plaza, parented to it, clear of every other card it could collide with
  coordinator_placed: ({ ctx, rows }) => {
    const card = coordCardOf(ctx); if (!card || ofKind(rows, 'coordinator').length !== 1) return false;
    const v = card.volum, pl = ctx.plaza.volum;
    const inside = [0, 2].every((i) => Math.abs(v.center[i] - pl.center[i]) + v.halfExtents[i] <= pl.halfExtents[i]);
    const clear = ctx.cards.filter((c) => ['agent', 'omega', 'seat', 'gate', 'council', 'zone', 'advisor'].includes(c.kind)).every((c) => !aabbOverlapXZ(v, c.volum));
    return inside && clear && card.parentCardId === ctx.plaza.cardId;
  },
  // the coordinator ROW links that card and takes its position from it: no stand spot of its own
  coordinator_card_linked: ({ ctx, rows }) => {
    const co = ofKind(rows, 'coordinator'); const card = coordCardOf(ctx); if (co.length !== 1 || !card) return false;
    const r = co[0], p = r.position ?? {};
    return r.cardId === card.cardId && r.cardId === `coordinator:${ctx.slug}` && card.binding?.swarm === r.binding.swarm && r.binding.fabricNode === card.binding?.fabricNode
      && r.permissions_from === card.cardId && p.from === card.cardId && sameVec(p.center, card.volum.center) && sameVec(p.halfExtents, card.volum.halfExtents)
      && !('relative_to' in p) && !('offset' in p) && JSON.stringify(p.facing ?? null) === JSON.stringify(outwardFacing(ctx.plaza.volum.center, card.volum.center));
  },
  advisor_rows_linked: ({ ctx, rows }) => {
    const cards = ctx.cards.filter((c) => c.kind === 'advisor'); const ar = ofKind(rows, 'advisor');
    return cards.length === (ctx.advisorsDoc.advisors ?? []).length && ar.length === cards.length && cards.every((c) => ar.filter((r) => r.cardId === c.cardId).length === 1)
      && ar.every((r) => { const c = ctx.byId.get(r.cardId); const rec = advisorRecord(ctx, c); return !!c && !!rec && c.kind === 'advisor' && c.scripted === true && r.scripted === true
        && r.role === c.avatar?.role && r.avatarId === `avatar:${ctx.slug}/advisor/${rec.id}` && r.advisor_id === rec.id && r.binding.advisor?.file === ctx.advisorsFile && r.binding.advisor?.id === rec.id
        && r.binding.swarm === null && r.permissions_from === c.cardId && r.position?.from === c.cardId && sameVec(r.position.center, c.volum.center) && sameVec(r.position.halfExtents, c.volum.halfExtents); });
  },
  // the house advisor contract: "Advisors get no prompt" (agents/metaprompt.mjs, README)
  advisors_have_no_prompt: ({ rows, prompts }) => ofKind(rows, 'advisor').every((r) => r.persona_prompt_id === null && r.binding.metaprompt === null
    && !prompts.has(r.avatarId.replace(/^avatar:/, 'persona:')))
    && ![...prompts.keys()].some((k) => typeof k !== 'string' || k.includes('/advisor/')),
  advisor_intro_scripted: ({ ctx, rows }) => ofKind(rows, 'advisor').every((r) => { const rec = advisorRecord(ctx, ctx.byId.get(r.cardId)); return !!rec && r.intro.text === advisorIntro(rec) && ADVISOR_MUST_SAY.every((s) => r.intro.text.includes(s)); }),
  // every row stores the contract path and never a voiced / exists flag
  audio_path_contract: ({ ctx, rows }) => {
    const paths = rows.map((r) => r.audio);
    return new Set(paths).size === paths.length && SEGMENT.test(ctx.slug) && rows.every((r) => r.world === ctx.slug && r.avatarId.startsWith(`avatar:${ctx.slug}/`)
      && SEGMENT.test(lastSeg(r.avatarId)) && r.audio === audioPath(ctx.slug, r.avatarId) && volatileKeys(r).length === 0);
  },
  voice_from_pool: ({ ctx, rows }) => rows.every((r) => VOICES.pool.includes(r.voice.id) && r.voice.engine === 'kokoro' && (r.kind === 'omega'
    ? r.voice.id === ctx.hive?.voice?.kokoro && r.voice.id === ctx.byId.get(r.cardId)?.voice?.kokoro
    : r.voice.id === pickVoice(r.avatarId).id)),
  tint_matches_brand: ({ ctx, rows }) => typeof ctx.brand?.hue === 'number' && rows.every((r) => r.tint_hue === ctx.brand.hue),
  names_within_limit: ({ rows }) => rows.every((r) => typeof r.displayName === 'string' && r.displayName.length <= NAME_LIMIT && r.displayName.endsWith(` · ${PBC.umbrella}`)),
  agents_operate_people_govern: ({ rows, ctx }) => rows.every((r) => { const src = ctx.byId.get(r.permissions_from); if (!src || JSON.stringify(src.permissions) !== JSON.stringify(r.permissions)) return false; const held = agentRights(r.permissions); return held.every((x) => ['view', 'enter', 'operate'].includes(x)) && ((r.kind !== 'omega' && r.kind !== 'advisor') || held.length === 0) && src.reserved_for_humans.map((x) => x.action).join() === PBC.reserved_for_humans.join() && src.reserved_for_humans.every((x) => x.held_for.quorum === '2-of-3'); }),
  nothing_invented: ({ ctx, rows }) => rows.every((r) => {
    if (r.world_name !== ctx.w.name || r.world_name !== ctx.worldCard.name) return false;
    if (r.kind === 'specialist') { const c = ctx.byId.get(r.cardId); const a = ctx.swarm.agents.find((x) => x.id === c?.binding?.swarm); return !!a && r.name === c.name && r.name === a.name && r.zone === a.zone && r.zone === ctx.byId.get(c.parentCardId)?.name && r.role_text === c.role && r.role_text === a.role && r.source === c.source && r.source === a.source && JSON.stringify(r.keywords) === JSON.stringify(a.keywords) && r.zone_from === zoneFrom(ctx, 'specialist', c, a.id); }
    const plazaOk = (c) => !!c && c.parentCardId === ctx.plaza.cardId && r.zone === plazaZone(ctx) && nodeName(r.zone) === ctx.plaza.displayName && r.zone_from === zoneFrom(ctx, r.kind, c);
    if (r.kind === 'coordinator') { const c = coordCardOf(ctx); return plazaOk(c) && r.name === ctx.swarm.coordinator.name && r.name === c.name && r.source === `agents/swarms/${ctx.slug}.json#coordinator` && r.source === c.source && r.role_text === ctx.swarm.topology; }
    if (r.kind === 'advisor') { const c = ctx.byId.get(r.cardId); const rec = advisorRecord(ctx, c); return !!rec && plazaOk(c) && r.name === rec.name && r.name === c.name && r.manages === rec.manages && r.manages === c.manages && r.role_text === rec.manages && r.source === c.source && r.source === `${ctx.advisorsFile}#advisors[id=${rec.id}]`; }
    // Omega: the zone is the council card's name, which must also be a zone the spec names, and is only accepted
    // while the omega card stands outside the council card (positive edge gap) and is not parented to it or a seat.
    const c = ctx.byId.get(r.cardId); const cl = councilOf(ctx); const parent = ctx.byId.get(c?.parentCardId);
    return !!c && !!cl && r.name === c.name && r.source === c.source && r.zone === cl.name && (ctx.w.zones ?? []).some((z) => z.name === r.zone)
      && omegaCouncilGap(ctx, c) > 0 && !['council', 'seat'].includes(parent?.kind) && JSON.stringify(r.zone_from) === JSON.stringify(zoneFrom(ctx, 'omega', c));
  }),
  coordinator_viewer_entry: ({ ctx, rows, viewer }) => {
    const v = (viewer ?? { coordinator: viewerCoordinator(rows, ctx) }).coordinator; const r = ofKind(rows, 'coordinator')[0];
    return !!v && !!r && v.world === ctx.slug && v.role === 'coordinator' && v.kind === 'coordinator' && v.cardId === r.cardId && v.name === r.name && v.model_ref === r.model_ref
      && isVec3(v.volum?.center) && isVec3(v.volum?.halfExtents) && sameVec(v.volum.center, r.position?.center) && sameVec(v.volum.halfExtents, r.position?.halfExtents)
      && (v.facing === null || (isVec3(v.facing) && Math.abs(Math.hypot(...v.facing) - 1) < 1e-3)) && v.intro?.text === r.intro.text && v.mirrors === `rows[avatarId=${r.avatarId}]` && v.audio === r.audio
      && v.permissions_from === r.permissions_from && JSON.stringify(v.permissions) === JSON.stringify(r.permissions) && JSON.stringify(v.reserved_for_humans) === JSON.stringify(ctx.byId.get(r.permissions_from)?.reserved_for_humans);
  },
  omega_defined_not_seated: ({ ctx, rows, prompts }) => ofKind(rows, 'omega').every((r) => r.seat_status === 'defined, not seated' && r.seated_agent === null && ctx.byId.get(r.cardId)?.seated_agent === null && (prompts.get(r.persona_prompt_id) ?? '').includes('defined, not seated')),
};

export function runChecks(c) {
  const results = Object.fromEntries(Object.entries(CHECKS).map(([k, f]) => { let ok; try { ok = !!f(c); } catch { ok = false; } return [k, ok]; }));
  return { results, failed: Object.keys(results).filter((k) => !results[k]) };
}

/** Deliberately broken fixtures; each must fail exactly the check named before its '#', or the suite does not discriminate. */
export function brokenFixtures(ctx, base) {
  const mk = (mut, more = {}) => {
    const rows = structuredClone(base.rows); const prompts = new Map(base.prompts); mut(rows, prompts);
    const c = { ctx, rows, prompts };
    if (more.ctx) { const cards = structuredClone(ctx.cards); more.ctx(cards); c.ctx = { ...ctx, cards, byId: new Map(cards.map((x) => [x.cardId, x])), worldCard: cards.find((x) => x.kind === 'world'), plaza: cards.find((x) => x.kind === 'plaza'), gate: cards.find((x) => x.kind === 'gate') }; }
    if (more.viewer) { c.viewer = { coordinator: viewerCoordinator(rows, c.ctx) }; more.viewer(c.viewer); }
    return c;
  };
  const sp = (rows) => rows.find((r) => r.kind === 'specialist');
  const om = (rows) => rows.find((r) => r.kind === 'omega');
  const co = (rows) => rows.find((r) => r.kind === 'coordinator');
  const ad = (rows) => rows.find((r) => r.kind === 'advisor');
  const firstAgentCard = ctx.cards.find((x) => x.kind === 'agent');
  return {
    one_avatar_per_agent_card: mk((rows) => { rows.splice(rows.indexOf(sp(rows)), 1); }),
    swarm_bound: mk((rows) => { sp(rows).binding.swarm = `${ctx.slug}.no-such-agent`; }),
    metaprompt_bound: mk((rows) => { sp(rows).binding.metaprompt.id = `${ctx.slug}.nobody`; }),
    omega_hive_bound: mk((rows) => { om(rows).binding.hive = 'omega.nowhere'; }),
    model_refs_are_roles: mk((rows) => { sp(rows).model_ref = `${AVATAR_DIR}/robot.glb`; }),
    intro_short_and_synthetic: mk((rows) => { const r = sp(rows); r.intro.text = r.intro.text.replace('a synthetic voice', 'a voice'); r.intro.words = words(r.intro.text); }),
    persona_prompts_pass: mk((rows, prompts) => { const id = sp(rows).persona_prompt_id; prompts.set(id, prompts.get(id).replaceAll('treasury.transfer', 'treasury.review')); }),
    no_pii_or_keys: mk((rows) => { sp(rows).note = 'reach the steward at steward@example.com'; }),
    // the coordinator card (and the row that mirrors it) moved onto the first agent card: off the plaza, overlapping
    coordinator_placed: mk((rows) => { const c = co(rows); c.position.center = [...firstAgentCard.volum.center]; c.position.facing = outwardFacing(ctx.plaza.volum.center, firstAgentCard.volum.center); },
      { ctx: (cards) => { cards.find((x) => x.kind === 'coordinator').volum.center = [...firstAgentCard.volum.center]; } }),
    // round 1's invented stand spot: same centre, but placed by an offset from the plaza instead of from the card
    coordinator_card_linked: mk((rows) => { const p = co(rows).position; co(rows).position = { from: null, relative_to: ctx.plaza.cardId, offset: [0, 0, 8], facing: p.facing, center: p.center, halfExtents: p.halfExtents }; }),
    'coordinator_card_linked#moved_off_card': mk((rows) => { const p = co(rows).position; p.center = [p.center[0] + 3, p.center[1], p.center[2]]; }),
    advisor_rows_linked: mk((rows) => { rows.splice(rows.indexOf(ad(rows)), 1); }),
    'advisor_rows_linked#position_off_card': mk((rows) => { ad(rows).position.center = [0, 1, 0]; }),
    advisors_have_no_prompt: mk((rows, prompts) => { const r = ad(rows); r.persona_prompt_id = r.avatarId.replace(/^avatar:/, 'persona:'); prompts.set(r.persona_prompt_id, prompts.get(co(rows).persona_prompt_id)); }),
    'advisors_have_no_prompt#metaprompt_bound': mk((rows) => { ad(rows).binding.metaprompt = { file: ctx.promptsFile, id: ctx.swarm.coordinator.id }; }),
    advisor_intro_scripted: mk((rows) => { const r = ad(rows); r.intro.text = r.intro.text.replace('not an AI model', 'an AI model'); r.intro.words = words(r.intro.text); }),
    audio_path_contract: mk((rows) => { sp(rows).audio = `${VOICE_DIR}/${ctx.slug}/specialist.mp4`; }),
    'audio_path_contract#voiced_flag_stored': mk((rows) => { sp(rows).voice.status = 'voiced'; }),
    voice_from_pool: mk((rows) => { sp(rows).voice.id = 'am_santa'; }),
    tint_matches_brand: mk((rows) => { sp(rows).tint_hue = (ctx.brand.hue + 1) % 360; }),
    names_within_limit: mk((rows) => { sp(rows).displayName = `${'An Overlong Avatar Name '.repeat(3)}· ${PBC.umbrella}`; }),
    agents_operate_people_govern: mk((rows) => { sp(rows).permissions.transfer.push('agents:zone'); }),
    nothing_invented: mk((rows) => { sp(rows).zone = 'Invented Zone'; }),
    // the Omega zone claim must fail once the omega card stands on the council card, though no row changed
    'nothing_invented#omega_moved_onto_council': mk(() => {}, { ctx: (cards) => { const o = cards.find((x) => x.kind === 'omega'); o.volum.center = [...cards.find((x) => x.kind === 'council').volum.center]; } }),
    // round 1's builder-authored Omega zone phrase is no longer accepted: the zone must be the council card's name
    'nothing_invented#omega_zone_phrased': mk((rows) => { const c = ctx.cards.find((x) => x.kind === 'council'); om(rows).zone = `beside the ${c.name}, never on it`; }),
    'nothing_invented#advisor_manages_invented': mk((rows) => { const r = ad(rows); r.manages = 'final governance'; r.role_text = 'final governance'; }),
    // the shape the verifier found the viewer could not read: position as an object, no [x, y, z] volum.center
    coordinator_viewer_entry: mk(() => {}, { viewer: (v) => { v.coordinator.volum = undefined; v.coordinator.position = { relative_to: `plaza:${ctx.slug}`, offset: [0, 0, 8] }; } }),
    omega_defined_not_seated: mk((rows) => { om(rows).seat_status = 'seated'; }),
  };
}

// ------------------------------------------------------------------------------------------ reporting ----
export const summaryLine = (t) => `${t.avatars} avatars across ${t.worlds} worlds, ${t.persona_prompts} persona prompts, ${t.evals} evals, ${t.failing} failing`;
/** The --check verdict. Exit 1 whenever anything is stale OR any eval fails; the line always ends "<N> failing". */
export function verdict({ stale = [], failing, summary }) {
  const n = stale.length;
  const behind = `${n} files behind their sources or not ours (first: ${OUT_REL}/${stale[0]})`;
  if (n && failing) return { code: 1, line: `avatars registry STALE and FAILING: ${behind}; ${summary}` };
  if (n) return { code: 1, line: `avatars registry STALE: ${behind}; ${summary}` };
  if (failing) return { code: 1, line: `avatars registry FAILING: ${summary}` };
  return { code: 0, line: `avatars registry current: ${summary}` };
}
/** Round 1 could report "current" with failing evals; these cases pin the verdict so it cannot again. */
function reporterSelfTest() {
  const t = (failing) => summaryLine({ avatars: 1, worlds: 1, persona_prompts: 1, evals: 3, failing });
  const cases = [
    ['files current, 2 failing: exit 1 and says "2 failing"', verdict({ stale: [], failing: 2, summary: t(2) }), (v) => v.code === 1 && v.line.endsWith(', 2 failing') && !v.line.startsWith('avatars registry current')],
    ['1 file stale, 0 failing: exit 1', verdict({ stale: ['index.json'], failing: 0, summary: t(0) }), (v) => v.code === 1 && v.line.startsWith('avatars registry STALE:') && v.line.endsWith(', 0 failing')],
    ['current and 0 failing: exit 0', verdict({ stale: [], failing: 0, summary: t(0) }), (v) => v.code === 0 && v.line === `avatars registry current: ${t(0)}`],
  ];
  return cases.map(([what, v, ok]) => ({ what, ok: ok(v) }));
}

// ------------------------------------------------------------------------------------------- outputs ----
function promptsMarkdown(ctx, rows, prompts, gates) {
  const L = [`# Avatar persona prompts · ${ctx.worldCard.name} · ${PBC.umbrella}`, ''];
  L.push(`Written by worldforge/avatars.mjs from worldforge/out/${ctx.slug}/cards.json, agents/swarms/${ctx.slug}.json, ${ctx.promptsFile} and agents/hive/index.json. No model runs these. Each is gated by evalPrompt (agents/metaprompt.mjs) and the avatar gates; edit the registries, not this file.`, '');
  const prompted = rows.filter((r) => r.persona_prompt_id !== null);
  L.push(`${prompted.length} persona prompts: ${ofKind(rows, 'coordinator').length} coordinator, ${ofKind(rows, 'specialist').length} specialists, ${ofKind(rows, 'omega').length} Omega Steward (defined, not seated). The ${ofKind(rows, 'advisor').length} advisors (${ofKind(rows, 'advisor').map((r) => r.name).join(', ')}) have none: they are scripted guides, and by the advisor contract advisors get no prompt.`, '');
  for (const r of prompted) {
    const t = prompts.get(r.persona_prompt_id);
    const g = gates.get(r.persona_prompt_id);
    const fence = t.includes('```') ? '````' : '```';
    L.push(`## ${r.name} · ${r.kind}`, '');
    L.push(`- avatar \`${r.avatarId}\` · card \`${r.cardId ?? 'none'}\` · prompt \`${r.persona_prompt_id}\``);
    L.push(`- ${t.length} of ${MAX_PROMPT_CHARS} characters · gates ${g.filter((x) => x.ok).length}/${g.length}${g.some((x) => !x.ok) ? ` · FAILING: ${g.filter((x) => !x.ok).map((x) => x.name).join('; ')}` : ''}`, '');
    L.push(`${fence}text`, t, fence, '');
  }
  return L.join('\n');
}

function build() {
  const index = R('my-fabric/worlds/index.json');
  const outputs = new Map();
  const put = (rel, s) => outputs.set(rel, Buffer.from(s));
  const allRows = [], worlds = [];
  let promptGates = 0, promptGatesFailing = 0, failing = 0;
  let baseCtx = null, baseBuilt = null;

  for (const w of index.worlds) {
    const ctx = loadWorld(w);
    const built = buildWorldAvatars(ctx);
    const prompted = built.rows.filter((r) => r.persona_prompt_id !== null);
    const gates = new Map(prompted.map((r) => [r.persona_prompt_id, gatePrompt(ctx, r, built.prompts.get(r.persona_prompt_id))]));
    for (const g of gates.values()) { promptGates += g.length; promptGatesFailing += g.filter((x) => !x.ok).length; }
    const viewer = { coordinator: viewerCoordinator(built.rows, ctx) };
    const ev = runChecks({ ctx, ...built, viewer });
    failing += ev.failed.length;
    allRows.push(...built.rows);
    worlds.push({ slug: w.slug, name: ctx.worldCard.name, avatars: built.rows.length, specialists: ofKind(built.rows, 'specialist').length, advisors: ofKind(built.rows, 'advisor').length, omega: built.rows.some((r) => r.kind === 'omega'), persona_prompts: prompted.length, checks: ev.results, failed: ev.failed, coordinator: viewer.coordinator });
    put(`prompts/${w.slug}.md`, promptsMarkdown(ctx, built.rows, built.prompts, gates));
    put(`prompts/${w.slug}.json`, stable({
      schemaVersion: 'worldforge-avatar-prompts/0.2', world: ctx.worldCard.name, slug: w.slug, umbrella: PBC.umbrella, max_prompt_chars: MAX_PROMPT_CHARS,
      honesty: 'generated from the registries by worldforge/avatars.mjs; no model has run these. Each persona layer binds an avatar to its card; the house metaprompt below it is reproduced unchanged from agents/prompts/<slug>.json. Advisors have no entry: by the advisor contract they get no prompt.',
      no_prompt: ofKind(built.rows, 'advisor').map((r) => ({ avatarId: r.avatarId, cardId: r.cardId, name: r.name, why: 'advisor contract: a scripted guide, not an AI model; advisors get no prompt' })),
      prompts: prompted.map((r) => { const g = gates.get(r.persona_prompt_id); return { id: r.persona_prompt_id, avatarId: r.avatarId, kind: r.kind, role: r.role, name: r.name, chars: built.prompts.get(r.persona_prompt_id).length, gates: { passed: g.filter((x) => x.ok).length, of: g.length, failed: g.filter((x) => !x.ok).map((x) => x.name) }, text: built.prompts.get(r.persona_prompt_id) }; }),
    }));
    if (w.slug === 'locator-x' || !baseCtx) { baseCtx = ctx; baseBuilt = built; }
  }

  const broken = Object.entries(brokenFixtures(baseCtx, baseBuilt)).map(([fixture, c]) => { const want = fixture.split('#')[0]; const { failed } = runChecks(c); return { want, fixture, world: baseCtx.slug, failed, ok: failed.length === 1 && failed[0] === want }; });
  const brokenBad = broken.filter((b) => !b.ok).length;
  const reporter = reporterSelfTest();
  const reporterBad = reporter.filter((x) => !x.ok).length;
  failing += brokenBad + reporterBad;
  const nChecks = Object.keys(CHECKS).length;
  const by = (kind) => ofKind(allRows, kind).length;
  const registry = {
    schemaVersion: 'worldforge-avatars/0.2', generator: 'worldforge/avatars.mjs', umbrella: PBC.umbrella, owner: PBC.name,
    principle: 'Agents operate; people govern.',
    honesty: [
      'Every name, role, zone and citation is read from the worldforge cards, the swarm, the advisor records and the hive registry; nothing is invented.',
      `Audio: every row stores only the expected path (${AUDIO_CONTRACT}); whether that file exists is never stored, because it changes as lines are rendered. Viewers HEAD-check it at runtime. This generator renders no audio.`,
      'Omega rows also point at the hive line audio (voice.audio.greet, ...); worldforge/voice/voice_intros.py does not render omega rows, so an omega viewer should try voice.audio.greet when the contract path is absent.',
      'Advisors (Host Advisor, Steward Liaison, Alignment Advisor; 3 per world) are scripted guides under agents/advisors/<slug>.json: not AI models and not people. By the advisor contract they get no persona prompt (persona_prompt_id null, no metaprompt binding); their intro is built only from the record\'s name and manages.',
      'Every Omega Steward is defined, not seated. No avatar holds governance.final_vote, charter.amend, treasury.transfer, proposal.enact, windfall.distribute or steward.appoint; those are held for the 2-of-3 Steward Council.',
      'Coordinator rows link their WorldForge coordinator card (coordinator:<slug>) and take position from its volum; worlds[i].coordinator mirrors the row for worldforge/viewer.html, with facing derived from the plaza and card centres.',
      'Zone strings carry zone_from. The Omega zone is the council card\'s name (the spec\'s own Steward Council zone, folded into that card by worldforge/build.mjs); the Omega card stands outside the council card (edge_gap_m in zone_from) and is never parented to it or a seat.',
      `Avatar models are referenced by role (${AVATAR_DIR}/<role>.glb) and built elsewhere; this registry does not build or check the GLB files.`,
      'No model runs the persona prompts; they are reviewable text with a test suite.',
    ],
    sources: SOURCES, roles: AVATAR_ROLES, kinds: KINDS, model_dir: AVATAR_DIR,
    audio_contract: { path: AUDIO_CONTRACT, stored: 'the expected path only, at rows[].audio (and worlds[i].coordinator.audio); never a voiced or exists flag', view_time: 'viewers HEAD-check rows[].audio; if absent they fall back to a labelled browser voice (voice.browser_fallback); omega rows may also use voice.audio.greet', held_by: 'audio_path_contract (paths unique per world; no status/voiced/exists keys in any row)' },
    voice_pool: { from: 'agents/hive.mjs ENGLISH_VOICES (read as text; the hive runs its main on import)', excluded: VOICES.excluded, size: VOICES.pool.length, pool: VOICES.pool,
      pick: 'specialist, coordinator and advisor: h = fnv1a(avatarId); id = pool[h % pool.length]; speed, browser pitch and lang from h by the tables agents/hive.mjs applies to Omegas (the hive hashes the world slug); omega: the hive voice' },
    view_time: { audio: 'rows[].audio exists (HTTP HEAD at view time); never stored here', model_present: 'model_ref exists' },
    viewer_contract: { coordinator: 'worlds[i].coordinator: the coordinator row mirrored for worldforge/viewer.html; volum.center and volum.halfExtents are the coordinator card\'s, as [x, y, z] arrays in metres (world frame, Y up); facing is a unit [x, 0, z] vector from the plaza centre to the card centre; intro/voice/binding/permissions/audio as in rows[]; reserved_for_humans from the coordinator card; held by coordinator_viewer_entry', specialists_advisors_and_omega: 'rows[] by cardId (the viewer places them from their cards)' },
    checks: Object.keys(CHECKS),
    reporter_selftest: reporter,
    totals: {
      worlds: worlds.length, avatars: allRows.length, specialists: by('specialist'), coordinators: by('coordinator'), advisors: by('advisor'), omegas: by('omega'),
      persona_prompts: allRows.filter((r) => r.persona_prompt_id !== null).length, prompt_gates: promptGates, prompt_gates_failing: promptGatesFailing,
      registry_evals: worlds.length * nChecks, broken_fixtures: broken.length, broken_discriminated: broken.length - brokenBad,
      reporter_selftests: reporter.length, evals: worlds.length * nChecks + broken.length + reporter.length, failing,
    },
    broken, worlds, rows: allRows,
  };
  put('index.json', stable(registry));
  return { outputs, registry, allRows };
}

/** Everything under worldforge/out/avatars/, at any depth, that this generator does not write; sorted, deepest
 *  entries after their parents. A directory is stray when no output lives under it. Symlinks count as files. */
function strays(outputs) {
  const need = new Set();
  for (const rel of outputs.keys()) for (let d = path.posix.dirname(rel); d && d !== '.'; d = path.posix.dirname(d)) need.add(d);
  const list = [];
  const scan = (dirRel) => {
    let ents;
    try { ents = fs.readdirSync(dirRel ? path.join(OUT, dirRel) : OUT, { withFileTypes: true }); } catch { return; }
    for (const e of ents) {
      const rel = dirRel ? `${dirRel}/${e.name}` : e.name;
      if (e.isDirectory()) { if (!need.has(rel)) list.push({ rel, dir: true }); scan(rel); continue; }
      if (e.isFile() && outputs.has(rel)) continue;
      list.push({ rel, dir: false });
    }
  };
  scan('');
  return list.sort((a, b) => (a.rel < b.rel ? -1 : a.rel > b.rel ? 1 : 0));
}

export function main() {
  let built;
  try { built = build(); } catch (e) {
    const why = String(e?.message ?? e).split('\n')[0].slice(0, 240);
    console.log(`${CHECK ? 'avatars registry FAILING' : 'AVATARS FAILING'}: the build threw (${why}); 1 failing`);
    process.exit(1);
  }
  const { outputs, registry, allRows } = built;
  const t = registry.totals;
  const summary = summaryLine(t);
  const audioNow = allRows.filter((r) => audioOnDiskAtViewTime(r)).length;
  const omegaGreetNow = ofKind(allRows, 'omega').filter((r) => r.voice.audio?.greet && has(r.voice.audio.greet)).length;
  const rolesUsed = AVATAR_ROLES.filter((role) => allRows.some((r) => r.role === role));
  const modelsNow = rolesUsed.filter((role) => has(`${AVATAR_DIR}/${role}.glb`)).length;
  for (const w of registry.worlds.filter((x) => x.failed.length)) console.log(`  FAIL ${w.slug}: ${w.failed.join(', ')}`);
  for (const b of registry.broken.filter((x) => !x.ok)) console.log(`  broken fixture ${b.fixture} failed [${b.failed.join(', ') || 'nothing'}], wanted exactly [${b.want}]`);
  for (const x of registry.reporter_selftest.filter((y) => !y.ok)) console.log(`  reporter self-test failed: ${x.what}`);
  console.log(`  view time (not stored): ${audioNow} of ${t.avatars} contract audio files on disk; ${omegaGreetNow} of ${t.omegas} Omega hive greetings on disk; ${modelsNow} of ${rolesUsed.length} avatar role models present; prompt gates ${t.prompt_gates - t.prompt_gates_failing}/${t.prompt_gates}`);
  if (CHECK) {
    const stray = strays(outputs).map((x) => `${x.rel}${x.dir ? '/' : ''}`);
    const stale = [...[...outputs].filter(([rel, d]) => { const p = path.join(OUT, rel); return !fs.existsSync(p) || !fs.statSync(p).isFile() || !fs.readFileSync(p).equals(d); }).map(([rel]) => rel), ...stray];
    if (stray.length) console.log(`  not written by this generator: ${stray.map((r) => `${OUT_REL}/${r}`).join(', ')}`);
    const v = verdict({ stale, failing: t.failing, summary });
    console.log(v.line);
    process.exit(v.code);
  }
  fs.mkdirSync(path.join(OUT, 'prompts'), { recursive: true });
  // Strays anywhere under worldforge/out/avatars/ are removed: files (and symlinks) first, then the stray directories,
  // deepest first, which are empty by then. Anything that cannot be removed is reported and fails the run.
  const left = [];
  const all = strays(outputs);
  for (const x of all.filter((y) => !y.dir)) { try { fs.unlinkSync(path.join(OUT, x.rel)); console.log(`  removed stray ${OUT_REL}/${x.rel}`); } catch { left.push(x.rel); } }
  for (const x of all.filter((y) => y.dir).reverse()) { try { fs.rmdirSync(path.join(OUT, x.rel)); console.log(`  removed stray directory ${OUT_REL}/${x.rel}/`); } catch { left.push(`${x.rel}/`); } }
  for (const [rel, d] of outputs) { const p = path.join(OUT, rel); fs.mkdirSync(path.dirname(p), { recursive: true }); fs.writeFileSync(p, d); }
  if (left.length) console.log(`  strays that could not be removed (--check flags them): ${left.map((r) => `${OUT_REL}/${r}`).join(', ')}`);
  console.log(`AVATARS: ${summary}`);
  process.exit(left.length || t.failing ? 1 : 0);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
