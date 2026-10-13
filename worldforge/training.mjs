// Training curricula for every worldforge avatar world: lessons drawn from the registries, tutor prompts held to
// the house prompt gates, and evals with broken fixtures that must fail them.
//   node worldforge/training.mjs           # writes worldforge/out/training/{index.json,<world>.json,tutors/<world>.md}
//   node worldforge/training.mjs --check   # rebuilds in memory; exit 1 if any output on disk is stale or any eval fails
//
// Nothing is invented. A lesson is assembled only from content that already exists in this repository:
//   module lessons      agents/training/index.json (human + robot tracks), assessed on the axes of
//                       agents/rubrics/index.json (copied exactly, "not measurable in simulation" included), with the
//                       robotics module (agents/robotics/index.json) and, for holodeck modules, the paired Academy
//                       halls' focus lines (my-fabric/holodeck/data.json) and the wing bay (my-fabric/holodeck/wing.json)
//   zone orientation    the world's own zone purposes and agent roles (worlds/<slug>/spec.json, agents/swarms/<slug>.json)
//                       and the zone's building card (worldforge/out/<slug>/cards.json)
//   routing orientation the swarm's routing table (agents/swarms/<slug>.json), taught by the coordinator
//   scripted orientation an advisor's own topics (agents/advisors/<slug>.json), delivered by that scripted advisor
// Who may deliver: scripted lessons only scripted advisors; routing lessons only the world's coordinator; zone lessons
// only specialists seated in that zone; module lessons only specialists the robotics registry names for that world.
// Omegas are defined, not seated: they deliver nothing and get no tutor prompt. Advisors get no tutor prompt either.
// No lesson is certified: every lesson is status "draft"; certification is a human/steward act and is never written here.
// Determinism: no clock, no randomness; every list is built in registry order.
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { evalPrompt, MAX_PROMPT_CHARS, PBC } from '../agents/metaprompt.mjs';
import { FORBIDDEN_ACTIONS, READ_SCOPES, redactPII } from '../agents/fabric/agent.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');
const OUT = path.join(HERE, 'out', 'training');
const R = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const rcCache = new Map();
/** Cached read for the checks, which consult the same registries for every lesson and fixture. */
const RC = (p) => { if (!rcCache.has(p)) rcCache.set(p, R(p)); return rcCache.get(p); };
const sha = (s) => crypto.createHash('sha256').update(s).digest('hex');
const clone = (x) => JSON.parse(JSON.stringify(x));
const list = (xs) => xs.map((x) => `  - ${x}`).join('\n');

// Strings the house gates look for, written exactly as agents/metaprompt.mjs writes them (not exported there).
const HELD = 'Held for the Steward Council';
const NOT_ADVICE = 'Nothing you say is legal, financial, medical or investment advice.';
const DRAFT = 'draft';
const BANNED = ['agi', 'corp', 'worlds'].join('-');

const F = {
  avatars: 'worldforge/out/avatars/index.json', training: 'agents/training/index.json', rubrics: 'agents/rubrics/index.json',
  robotics: 'agents/robotics/index.json', halls: 'my-fabric/holodeck/data.json', wing: 'my-fabric/holodeck/wing.json',
  worlds: 'my-fabric/worlds/index.json',
};

// --------------------------------------------------------------------------------- source pointers ----
/** Split "a.b[k=v.w].c" on dots outside brackets. */
function segments(ptr) {
  const out = []; let cur = '', depth = 0;
  for (const ch of ptr) {
    if (ch === '[') depth++;
    if (ch === ']') depth--;
    if (ch === '.' && depth === 0) { out.push(cur); cur = ''; } else cur += ch;
  }
  if (cur) out.push(cur);
  return out;
}
const jsonCache = new Map();
/** Does file#pointer exist? A JSON pointer is resolved segment by segment; key[field=value] picks an array element,
 *  a bare key on an array picks the element whose id or slug is that key; a non-JSON file needs only to exist. */
export function sourceExists(src) {
  const [file, ptr] = src.split('#');
  const abs = path.join(ROOT, file);
  if (!file || !fs.existsSync(abs)) return false;
  if (!ptr || !file.endsWith('.json')) return true;
  if (!jsonCache.has(file)) jsonCache.set(file, JSON.parse(fs.readFileSync(abs, 'utf8')));
  let node = jsonCache.get(file);
  for (const seg of segments(ptr)) {
    const ix = seg.match(/^([^[]*)\[(\d+)\]$/);
    if (ix) { node = ix[1] ? node?.[ix[1]] : node; node = Array.isArray(node) ? node[Number(ix[2])] : undefined; if (node === undefined) return false; continue; }
    const m = seg.match(/^([^[]*)(?:\[([^=\]]+)=(.*)\])?$/);
    if (!m) return false;
    const [, key, f, v] = m;
    if (key) {
      if (Array.isArray(node) && !(key in node)) node = node.find((e) => e && (e.id === key || e.slug === key));
      else node = node?.[key];
    }
    if (f) node = Array.isArray(node) ? node.find((e) => e && String(e[f]) === v) : undefined;
    if (node === undefined) return false;
  }
  return true;
}

// ------------------------------------------------------------------------------------------ helpers ----
function rubricStrings(rubrics) {
  const statuses = [...new Set(rubrics.modules.flatMap((m) => m.robot_scoring.map((a) => a.status)))];
  const notMeasurable = statuses.find((s) => /^not measurable/.test(s));
  const noMeasure = Object.keys(rubrics.totals.not_measurable_by_reason).find((k) => /no measure in the source/.test(k));
  return { notMeasurable, noMeasure };
}
const axisCopy = (a) => {
  const o = { id: a.id, axis: a.axis, status: a.status, applies_to: a.applies_to };
  for (const k of ['measure', 'pass', 'verdict', 'reason']) if (a[k] !== undefined) o[k] = a[k];
  return o;
};
function moduleAssessment(rubrics, moduleId) {
  const rm = rubrics.modules.find((m) => m.id === moduleId);
  if (!rm) return null;
  return {
    rubric_module: moduleId, from: `${F.rubrics}#modules[id=${moduleId}].robot_scoring`,
    proposal_status: rm.rubric_proposal.status, axes: rm.robot_scoring.map(axisCopy),
  };
}
function noRubric(RS) {
  return { rubric_module: null, axes: [], status: RS.notMeasurable, reason_kind: RS.noMeasure,
    note: 'no module in agents/rubrics/index.json covers this lesson; nothing is scored and no value is estimated' };
}
function roomOf(cards, slug, zoneName) {
  const z = cards.cards.find((c) => c.kind === 'zone' && c.name === zoneName);
  if (!z) return { card: null, room: null };
  const b = z.building;
  return {
    card: z.cardId,
    room: b ? { kind: b.kind, sign: b.sign, room_model: b.room ?? null, interior: b.interior ?? null,
      from: `worldforge/out/${slug}/cards.json#cards[cardId=${z.cardId}].building` } : null,
  };
}
function tracks(mod, src) {
  const out = {};
  if (mod.human) out.human_track = {
    who: mod.human.who, from: `${F.training}#modules[id=${mod.id}].human`,
    prerequisites: (mod.human.prerequisites ?? []).map((p) => p.item),
    steps: mod.human.steps.map((s) => ({ n: s.n, do: s.do, instructor_checks: s.instructor_checks })),
    safety_prechecks: mod.human.safety_prechecks ?? [],
    instructor_signoff: mod.human.instructor_signoff?.status ?? null, certificate: null,
  };
  if (mod.robot) out.robot_track = {
    who: mod.robot.who, from: `${F.training}#modules[id=${mod.id}].robot`, run_id: mod.robot.run_id,
    run_from: mod.robot.from, robotics_avatar: mod.robot.avatar, status: mod.robot.status,
    passed: mod.robot.passed, total: mod.robot.total, certificate: null,
  };
  return out;
}
function moduleLesson({ mod, rubrics, robotics, halls, wing, slug, zone, room, deliverers, RS }) {
  const rmod = robotics.modules.find((m) => m.id === mod.id);
  const objectives = [
    { text: `Run "${mod.title}" step by step, the same steps on both tracks`, quote: mod.title, from: `${F.training}#modules[id=${mod.id}].title` },
    ...(rmod?.skills ?? []).map((s, i) => ({ text: `Skill: ${s}`, quote: s, from: `${F.robotics}#modules[id=${mod.id}].skills[${i}]` })),
    ...(mod.pairing?.halls ?? []).filter((h) => halls.halls[h.slug]?.focus).map((h) => ({
      text: `Hall focus (${h.name}): ${halls.halls[h.slug].focus}`, quote: halls.halls[h.slug].focus, from: `${F.halls}#halls.${h.slug}.focus` })),
  ];
  const steps = mod.human.steps.map((s) => ({ n: s.n, do: s.do, from: `${F.training}#modules[id=${mod.id}].human.steps[n=${s.n}]` }));
  const bay = wing?.bays.find((b) => b.module === mod.id);
  const sources = [mod.source, `${F.training}#modules[id=${mod.id}]`, `${F.robotics}#modules[id=${mod.id}]`,
    `${F.rubrics}#modules[id=${mod.id}]`, ...(bay ? [`${F.wing}#bays[module=${mod.id}]`] : [])];
  return {
    id: `lesson:${slug}/module/${mod.id.split('.').slice(1).join('.')}`, kind: 'module', mode: 'model-taught',
    title: mod.title, world: slug, zone, room: room ?? (bay ? { kind: 'wing bay', sign: bay.node, room_model: null, interior: null, from: `${F.wing}#bays[module=${mod.id}]` } : null),
    objectives, steps, assessment: moduleAssessment(rubrics, mod.id) ?? noRubric(RS), ...tracks(mod),
    delivered_by: deliverers, sources, status: DRAFT, certification: null,
  };
}

// -------------------------------------------------------------------------------------------- build ----
export function build() {
  const avIx = R(F.avatars), training = R(F.training), rubrics = R(F.rubrics), robotics = R(F.robotics);
  const halls = R(F.halls), wing = R(F.wing);
  const RS = rubricStrings(rubrics);
  const avatarSlugs = avIx.worlds.map((w) => w.slug);
  const curricula = [], tutorsByWorld = {};

  for (const slug of avatarSlugs) {
    const spec = R(`worlds/${slug}/spec.json`), swarm = R(`agents/swarms/${slug}.json`);
    const cards = R(`worldforge/out/${slug}/cards.json`), advisors = R(`agents/advisors/${slug}.json`);
    const personas = R(`worldforge/out/avatars/prompts/${slug}.json`);
    const rows = avIx.rows.filter((r) => r.world === slug);
    const coord = rows.find((r) => r.kind === 'coordinator');
    const specialists = rows.filter((r) => r.kind === 'specialist');
    const lessons = [], gaps = [];

    // 1. scripted orientation: one per advisor, from the advisor's own topics.
    for (const adv of advisors.advisors) {
      const row = rows.find((r) => r.kind === 'advisor' && r.advisor_id === adv.id);
      if (!row) { gaps.push(`advisor ${adv.id} has no avatar row`); continue; }
      const af = `agents/advisors/${slug}.json#advisors[id=${adv.id}]`;
      lessons.push({
        id: `lesson:${slug}/orientation/${adv.id}`, kind: 'scripted-orientation', mode: 'scripted',
        title: `${adv.name}: ${adv.manages}`, world: slug, zone: row.zone, room: null,
        objectives: [{ text: `Orientation: ${adv.manages}`, quote: adv.manages, from: `${af}.manages` }],
        steps: adv.topics.map((t, i) => ({ n: i + 1, do: `Ask: ${t.ask}`, answer: t.say ? { say: t.say, cites: t.cites } : { read: t.read }, from: `${af}.topics[ask=${t.ask}]` })),
        assessment: noRubric(RS), delivered_by: [row.avatarId], sources: [af, `${F.avatars}#rows[avatarId=${row.avatarId}]`],
        status: DRAFT, certification: null, scripted_note: 'delivered by a scripted guide: every line is written in the advisor registry; no model teaches it',
      });
    }

    // 2. routing orientation: the coordinator teaches how the swarm routes.
    lessons.push({
      id: `lesson:${slug}/routing`, kind: 'routing', mode: 'model-taught',
      title: `How ${spec.name} routes a question`, world: slug, zone: coord.zone, room: null,
      objectives: [{ text: `Know the swarm topology: ${swarm.topology}`, quote: swarm.topology, from: `agents/swarms/${slug}.json#topology` },
        { text: 'Know which specialist answers which kind of question', quote: null, from: `agents/swarms/${slug}.json#agents` }],
      steps: swarm.agents.map((a, i) => ({ n: i + 1, do: `${a.name} (${a.zone}): ${a.role}`, keywords: a.keywords, from: `agents/swarms/${slug}.json#agents[id=${a.id}]` })),
      assessment: noRubric(RS), delivered_by: [coord.avatarId],
      sources: [`agents/swarms/${slug}.json#coordinator`, `agents/swarms/${slug}.json#agents`, `${F.avatars}#rows[avatarId=${coord.avatarId}]`],
      status: DRAFT, certification: null,
    });

    // 3. zone orientation: one per zone that seats a specialist.
    for (const z of spec.zones) {
      const here = specialists.filter((s) => s.zone === z.name);
      if (!here.length) continue;
      const { card, room } = roomOf(cards, slug, z.name);
      const zf = `worlds/${slug}/spec.json#zones[name=${z.name}]`;
      lessons.push({
        id: `lesson:${slug}/zone/${card ? card.split('/').pop() : z.name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`,
        kind: 'zone-orientation', mode: 'model-taught', title: `${z.name}: what happens here`, world: slug, zone: z.name, room,
        objectives: [{ text: `Zone purpose: ${z.purpose}`, quote: z.purpose, from: `${zf}.purpose`, origin: z.source },
          ...here.map((s) => { const a = swarm.agents.find((x) => x.id === s.binding.swarm);
            return { text: `${a.name}'s role: ${a.role}`, quote: a.role, from: `agents/swarms/${slug}.json#agents[id=${a.id}].role`, origin: a.source }; })],
        steps: [
          ...(room ? [{ n: 1, do: `Enter the ${room.kind} signed "${room.sign}"`, from: room.from }] : []),
          ...here.map((s) => ({ do: `Meet ${s.name}: ${s.role_text}`, from: `${F.avatars}#rows[avatarId=${s.avatarId}].role_text` })),
          { do: `A question that belongs to another zone goes back to ${coord.name}`, from: `agents/swarms/${slug}.json#coordinator` },
        ].map((s, i) => ({ n: i + 1, do: s.do, from: s.from })),
        assessment: noRubric(RS), delivered_by: here.map((s) => s.avatarId),
        sources: [zf, ...(card ? [`worldforge/out/${slug}/cards.json#cards[cardId=${card}]`] : []), ...here.map((s) => `agents/swarms/${slug}.json#agents[id=${s.binding.swarm}]`)],
        status: DRAFT, certification: null,
      });
    }

    // 4. module lessons: training modules of this world, delivered by the specialists the robotics registry names.
    const mods = training.modules.filter((m) => m.world === slug);
    for (const mod of mods) {
      const roboAv = robotics.avatars[slug] ?? [];
      const names = roboAv.map((a) => a.agent);
      const dels = specialists.filter((s) => names.includes(s.name));
      const op = roboAv.find((a) => a.role === 'operations');
      const zone = op?.zone ?? null;
      const { room } = zone ? roomOf(cards, slug, zone) : { room: null };
      if (!dels.length) { gaps.push(`module ${mod.id}: no specialist avatar matches the robotics avatars for this world`); continue; }
      const L = moduleLesson({ mod, rubrics, robotics, halls, wing: null, slug, zone, room, deliverers: dels.map((d) => d.avatarId), RS });
      L.sources.push(`${F.robotics}#avatars.${slug}`);
      lessons.push(L);
    }
    if (!mods.length) gaps.push('no training module, rubric module or robotics module in agents/training, agents/rubrics or agents/robotics names this world: its lessons are orientation only (advisor topics, routing table, zone purposes and agent roles)');
    for (const z of spec.zones) if (!specialists.some((s) => s.zone === z.name)) gaps.push(`zone "${z.name}" seats no specialist: no model-taught lesson for it${z.name === 'Steward Council' ? ' (it is the human stewards’ zone; its Omega is defined, not seated)' : ''}`);
    if (slug === 'locator-x') {
      const ac = spec.zones.find((z) => z.name === 'The Academy');
      if (ac) gaps.push(`The Academy (${ac.purpose}) is cited from ${ac.source}, which is not in this repository: none of its tracks or lessons is reproduced here`);
    }
    for (const g of spec.gaps ?? []) gaps.push(`spec gap: ${g}`);

    // tutor prompts: one per delivering specialist or coordinator.
    const deliverers = [...new Set(lessons.filter((l) => l.mode === 'model-taught').flatMap((l) => l.delivered_by))];
    const tutors = deliverers.map((id) => {
      const row = rows.find((r) => r.avatarId === id);
      const agent = row.kind === 'specialist' ? swarm.agents.find((a) => a.id === row.binding.swarm) : null;
      const persona = personas.prompts.find((p) => p.avatarId === id);
      const mine = lessons.filter((l) => l.mode === 'model-taught' && l.delivered_by.includes(id));
      const text = tutorPrompt({ spec, swarm, row, agent, persona, lessons: mine, slug });
      const gates = evalPrompt(text, { spec, agent });
      return { id: `tutor:${slug}/${id.split('/').slice(1).join('/')}`, avatarId: id, kind: row.kind, name: row.name,
        persona_prompt: persona ? { id: persona.id, file: `worldforge/out/avatars/prompts/${slug}.json`, sha256: sha(persona.text) } : null,
        lessons: mine.map((l) => l.id), chars: text.length, gates: { passed: gates.filter((g) => g.ok).length, of: gates.length, failed: gates.filter((g) => !g.ok).map((g) => g.name) }, text };
    });
    tutorsByWorld[slug] = tutors;
    curricula.push({ slug, name: spec.name, status: spec.status, seated: true, lessons, tutors, gaps });
  }

  // Training modules of worlds that have no worldforge avatar world: drafted, never seated.
  const unseated = [];
  for (const w of [...new Set(training.modules.map((m) => m.world))].filter((w) => !avatarSlugs.includes(w))) {
    const lessons = training.modules.filter((m) => m.world === w).map((mod) => {
      const bay = wing.bays.find((b) => b.module === mod.id);
      return moduleLesson({ mod, rubrics, robotics, halls, wing, slug: w, zone: bay ? wing.name : null, room: null, deliverers: [], RS });
    });
    unseated.push({ slug: w, name: w, status: null, seated: false, lessons, tutors: [],
      gaps: [`${w} has no worldforge avatar world (${F.avatars} lists ${avatarSlugs.length} worlds, not this one): its ${lessons.length} module lessons are drafted with delivered_by [] until a world seats an avatar for them`,
        `robotics avatars named for ${w} (${(robotics.avatars[w] ?? []).map((a) => a.agent).join(', ')}) come from ${(robotics.avatars[w] ?? [])[0]?.source ?? 'no source'}: scripted advisors of the Trade Craft pack, not worldforge avatars, so none may deliver a model-taught lesson`,
        `Academy halls (${Object.keys(halls.halls).length} in ${F.halls}) appear only as the paired halls' focus lines inside module lessons; halls with no module have no lesson`] });
  }
  return { avIx, rubrics, curricula, unseated, RS };
}

function tutorPrompt({ spec, swarm, row, agent, persona, lessons, slug }) {
  const zone = spec.zones.find((z) => z.name === row.zone);
  const head = [
    `Tutor layer: ${row.name} (${row.avatarId}) teaches draft lessons in ${spec.name} (${PBC.umbrella}). Status: ${spec.status}.`,
    persona ? `Bound persona: ${persona.id} in worldforge/out/avatars/prompts/${slug}.json (sha256 ${sha(persona.text).slice(0, 16)}); that persona and its house metaprompt apply unchanged; this layer adds lessons only.` : 'No persona prompt is bound; say so.',
    'You are an agent with a synthetic voice, not a person, and a tutor, not an instructor: you never certify, sign off, pass or grade anyone. Every lesson below is a draft; certification is a human steward act.',
  ];
  if (agent) head.push(`Your zone: ${agent.zone} - ${zone?.purpose ?? 'purpose not in spec'}.`, `Your role: ${agent.role} (source: ${agent.source}).`,
    `You answer on: ${agent.keywords.join(', ')}.`);
  else head.push(`You coordinate ${spec.name} (${swarm.topology}) from ${row.zone}; you teach routing and hand each zone question to its specialist.`);
  const body = ['Lessons you deliver (follow the steps in order; quote objectives, never extend them):'];
  for (const l of lessons) {
    body.push(`  - ${l.id}: ${l.title}${l.room ? ` [room: ${l.room.sign}]` : ''}`);
    const steps = l.kind === 'module' && l.steps.length > 6 ? [...l.steps.slice(0, 6), { n: '...', do: `${l.steps.length - 6} more steps in the lesson file` }] : l.steps;
    body.push(`    Steps: ${steps.map((s) => `${s.n}. ${s.do}`).join(' ')}`);
    body.push(`    Assessment: ${l.assessment.axes.length ? l.assessment.axes.map((a) => `${a.axis} (${a.status})`).join('; ') : l.assessment.status}.`);
    if (l.human_track && l.robot_track) body.push('    Two tracks: a person (human instructor present for every attempt) and a simulated robot run; never claim the robot run qualifies anyone.');
  }
  const rules = [
    `Assessment axes marked "not measurable in simulation" are observed by a human instructor; never estimate a value. Safety, injury, fitness-for-work or licensing questions: say "Ask your instructor before you continue." and stop.`,
    `A question outside these lessons goes to ${swarm.coordinator.id}; a question about another world goes to agi-corp.concierge.`,
    `Management model: ${PBC.management_style.name} - agents operate, people govern.`,
    `Reserved for humans - never perform these; if asked, answer "${HELD}" and name the action:`, list(PBC.reserved_for_humans),
    'Forbidden actions - the middleware contains them, so do not attempt them:', list(FORBIDDEN_ACTIONS),
    `You may read only these surfaces: ${READ_SCOPES.join(', ')}.`,
    `Never ask for, store or repeat personal data. Keep "${PBC.umbrella}" in the world's name. ${NOT_ADVICE}`,
  ];
  return [...head, ...body, ...rules].join('\n');
}

// -------------------------------------------------------------------------------------------- evals ----
const ALL = (m) => [...m.curricula, ...m.unseated];
export function runChecks(m) {
  const rows = new Map(m.avIx.rows.map((r) => [r.avatarId, r]));
  const roboNames = (slug) => (RC(F.robotics).avatars[slug] ?? []).map((a) => a.agent);
  const lessons = ALL(m).flatMap((c) => c.lessons.map((l) => ({ c, l })));
  const seated = lessons.filter(({ c }) => c.seated);
  const bad = (xs) => ({ ok: xs.length === 0, detail: xs.length ? xs.slice(0, 5).join('; ') : `${lessons.length} lessons` });
  const checks = [];
  const add = (name, xs, detail) => checks.push({ name, ...bad(xs), ...(xs.length ? {} : detail ? { detail } : {}) });

  add('every lesson cites a source that exists', lessons.flatMap(({ l }) => [...l.sources, ...l.objectives.map((o) => o.from), ...l.steps.map((s) => s.from)]
    .filter((s) => !sourceExists(s)).map((s) => `${l.id}: ${s}`)), `${lessons.length} lessons; every source, objective and step pointer resolves`);
  add('every delivered_by avatar exists in this world', seated.flatMap(({ c, l }) => l.delivered_by.filter((id) => rows.get(id)?.world !== c.slug).map((id) => `${l.id}: ${id}`)),
    `${seated.reduce((n, { l }) => n + l.delivered_by.length, 0)} deliveries across ${seated.length} seated lessons, all in ${F.avatars}`);
  add('every seated lesson has at least one deliverer, and an unseated one has none', lessons.filter(({ c, l }) => (c.seated ? !l.delivered_by.length : l.delivered_by.length)).map(({ l }) => l.id));
  add('every deliverer is allowed for the lesson kind', seated.flatMap(({ c, l }) => l.delivered_by.map((id) => rows.get(id)).filter(Boolean).filter((r) => {
    if (l.mode === 'scripted') return r.kind !== 'advisor';
    if (r.kind === 'advisor' || r.kind === 'omega') return false; // held by the next check
    if (l.kind === 'routing') return r.kind !== 'coordinator';
    if (l.kind === 'zone-orientation') return r.kind !== 'specialist' || r.zone !== l.zone;
    if (l.kind === 'module') return r.kind !== 'specialist' || !roboNames(c.slug).includes(r.name);
    return true;
  }).map((r) => `${l.id}: ${r.avatarId}`)));
  add('no advisor or omega delivers a model-taught lesson', seated.flatMap(({ l }) => (l.mode === 'scripted' ? [] : l.delivered_by.filter((id) => ['advisor', 'omega'].includes(rows.get(id)?.kind)).map((id) => `${l.id}: ${id}`))));
  add('no lesson is marked certified', lessons.filter(({ l }) => l.status !== DRAFT || l.certification !== null || l.human_track?.certificate || l.robot_track?.certificate || /certified/i.test(l.status)).map(({ l }) => l.id));
  const rub = new Map(m.rubrics.modules.map((x) => [x.id, x]));
  add('rubric axes match agents/rubrics exactly', lessons.flatMap(({ l }) => {
    const a = l.assessment;
    if (a.rubric_module === null) return a.status === m.RS.notMeasurable && a.axes.length === 0 ? [] : [`${l.id}: unscored lesson not marked "${m.RS.notMeasurable}"`];
    const src = rub.get(a.rubric_module);
    if (!src) return [`${l.id}: no rubric module ${a.rubric_module}`];
    return JSON.stringify(a.axes) === JSON.stringify(src.robot_scoring.map(axisCopy)) ? [] : [`${l.id}: axes differ from ${a.rubric_module}`];
  }));
  add('module lessons carry a human and a robot track wherever the source module has both', lessons.filter(({ l }) => l.kind === 'module').filter(({ l }) => {
    const src = RC(F.training).modules.find((x) => `${x.id}` && l.sources.includes(`${F.training}#modules[id=${x.id}]`));
    return !src || (!!src.human !== !!l.human_track) || (!!src.robot !== !!l.robot_track);
  }).map(({ l }) => l.id));
  const tutors = m.curricula.flatMap((c) => c.tutors.map((t) => ({ c, t })));
  add('every tutor prompt passes every evalPrompt gate', tutors.flatMap(({ c, t }) => {
    const spec = RC(`worlds/${c.slug}/spec.json`), swarm = RC(`agents/swarms/${c.slug}.json`);
    const row = rows.get(t.avatarId);
    const agent = row?.kind === 'specialist' ? swarm.agents.find((a) => a.id === row.binding.swarm) : null;
    return evalPrompt(t.text, { spec, agent }).filter((g) => !g.ok).map((g) => `${t.id}: ${g.name}`);
  }), `${tutors.length} tutor prompts, each at most ${MAX_PROMPT_CHARS} characters`);
  add('exactly one tutor prompt per delivering specialist or coordinator, none for advisors or omegas', m.curricula.flatMap((c) => {
    const want = [...new Set(c.lessons.filter((l) => l.mode === 'model-taught').flatMap((l) => l.delivered_by))]
      .filter((id) => ['specialist', 'coordinator'].includes(rows.get(id)?.kind)).sort();
    const have = c.tutors.map((t) => t.avatarId).sort();
    const wrong = c.tutors.filter((t) => !['specialist', 'coordinator'].includes(rows.get(t.avatarId)?.kind)).map((t) => `${t.id}: kind ${rows.get(t.avatarId)?.kind}`);
    return [...(JSON.stringify(want) === JSON.stringify(have) ? [] : [`${c.slug}: tutors ${have.length} vs deliverers ${want.length}`]), ...wrong];
  }));
  add('tutor prompts bind the avatar’s current persona prompt', tutors.filter(({ c, t }) => {
    const p = RC(`worldforge/out/avatars/prompts/${c.slug}.json`).prompts.find((x) => x.avatarId === t.avatarId);
    return !p || !t.persona_prompt || t.persona_prompt.sha256 !== sha(p.text) || !t.text.includes(p.id);
  }).map(({ t }) => t.id), `${tutors.length} tutor prompts, each naming its persona prompt id and matching its sha256`);
  const blob = JSON.stringify(ALL(m).map((c) => ({ l: c.lessons, t: c.tutors.map((t) => t.text) })));
  add(`outputs carry no PII, keys or the retired name`, [
    ...(redactPII(blob).redactions ? ['PII-shaped string'] : []),
    ...(/(sk-[A-Za-z0-9]{8,}|PRIVATE KEY|0x[0-9a-fA-F]{40})/.test(blob) ? ['key-shaped string'] : []),
    ...(blob.includes(BANNED) ? ['retired name'] : []),
  ]);
  return checks;
}

/** Each broken fixture must fail exactly its own check. */
export function fixtures(m) {
  const firstWhere = (mm, f) => { for (const c of ALL(mm)) for (const l of c.lessons) if (f(l, c)) return { c, l }; return null; };
  const cases = [
    ['a lesson citing a file that does not exist', 'every lesson cites a source that exists', (x) => { firstWhere(x, (l, c) => c.seated).l.sources.push('worldforge/out/nowhere.json#zones'); }],
    ['a lesson delivered by an avatar id that does not exist', 'every delivered_by avatar exists in this world', (x) => { firstWhere(x, (l, c) => c.seated && l.kind === 'routing').l.delivered_by.push('avatar:nowhere/specialist/ghost'); }],
    ['a specialist delivering a scripted orientation', 'every deliverer is allowed for the lesson kind', (x) => {
      const { c, l } = firstWhere(x, (l, c) => c.seated && l.mode === 'scripted');
      l.delivered_by.push(x.avIx.rows.find((r) => r.world === c.slug && r.kind === 'specialist').avatarId); }],
    ['an advisor delivering a model-taught zone lesson', 'no advisor or omega delivers a model-taught lesson', (x) => {
      const { c, l } = firstWhere(x, (l, c) => c.seated && l.kind === 'zone-orientation');
      l.delivered_by.push(x.avIx.rows.find((r) => r.world === c.slug && r.kind === 'advisor').avatarId); }],
    ['an omega delivering the routing lesson', 'no advisor or omega delivers a model-taught lesson', (x) => {
      const { c, l } = firstWhere(x, (l, c) => c.seated && l.kind === 'routing');
      l.delivered_by.push(x.avIx.rows.find((r) => r.world === c.slug && r.kind === 'omega').avatarId); }],
    ['a lesson marked certified', 'no lesson is marked certified', (x) => { firstWhere(x, (l, c) => c.seated).l.status = 'certified'; }],
    ['a rubric axis dropped from a module lesson', 'rubric axes match agents/rubrics exactly', (x) => { firstWhere(x, (l) => l.kind === 'module').l.assessment.axes.pop(); }],
    ['an unscored lesson given an invented status', 'rubric axes match agents/rubrics exactly', (x) => { firstWhere(x, (l) => l.assessment.rubric_module === null).l.assessment.status = 'passed'; }],
    ['a module lesson with its robot track removed', 'module lessons carry a human and a robot track wherever the source module has both', (x) => { delete firstWhere(x, (l) => l.kind === 'module').l.robot_track; }],
    ['a tutor prompt with the umbrella dropped', 'every tutor prompt passes every evalPrompt gate', (x) => { const t = x.curricula[0].tutors[0]; t.text = t.text.replaceAll(PBC.umbrella, 'AGI Corp'); }],
    ['a tutor prompt bound to a stale persona hash', 'tutor prompts bind the avatar’s current persona prompt', (x) => { x.curricula[0].tutors[0].persona_prompt.sha256 = '0'.repeat(64); }],
    ['a lesson leaking an email address', 'outputs carry no PII, keys or the retired name', (x) => { firstWhere(x, (l, c) => c.seated).l.title += ' steward@example.com'; }],
  ];
  return cases.map(([what, expect, mutate]) => {
    const x = clone({ ...m, avIx: undefined, rubrics: undefined }); x.avIx = m.avIx; x.rubrics = m.rubrics;
    mutate(x);
    const failed = runChecks(x).filter((c) => !c.ok).map((c) => c.name);
    return { what, expect, ok: failed.length === 1 && failed[0] === expect, failed };
  });
}

// ------------------------------------------------------------------------------------------ outputs ----
function render(m) {
  const files = {};
  const checks = runChecks(m);
  const second = build();
  checks.push({ name: 'deterministic: a second build is byte-identical', ok: JSON.stringify(strip(second)) === JSON.stringify(strip(m)), detail: 'no clock, no randomness' });
  const fx = fixtures(m);
  const honesty = 'Draft curricula assembled from the registries; nothing invented. No model has taught any lesson, no person or robot has been assessed here, and no lesson is certified: certification is a human/steward act. Advisors are scripted guides and deliver only their own scripted orientation; Omegas are defined, not seated, and deliver nothing.';
  const all = ALL(m);
  for (const c of all) {
    files[`${c.slug}.json`] = { schemaVersion: 'worldforge-training/0.1', generator: 'worldforge/training.mjs', umbrella: PBC.umbrella,
      world: c.name, slug: c.slug, status: c.status, seated: c.seated, honesty, lessons: c.lessons, tutors: c.tutors, gaps: c.gaps };
    if (c.seated) files[`tutors/${c.slug}.md`] = tutorMd(c);
  }
  const lessonsN = all.reduce((n, c) => n + c.lessons.length, 0);
  const tutorsN = m.curricula.reduce((n, c) => n + c.tutors.length, 0);
  const evalsN = checks.length + fx.length;
  const failing = checks.filter((c) => !c.ok).length + fx.filter((f) => !f.ok).length;
  const byKind = {}; for (const c of all) for (const l of c.lessons) byKind[l.kind] = (byKind[l.kind] ?? 0) + 1;
  files['index.json'] = { schemaVersion: 'worldforge-training/0.1', generator: 'worldforge/training.mjs', umbrella: PBC.umbrella,
    owner: 'AGI Future Foundation PBC', principle: 'Agents operate; people govern.', honesty,
    sources: Object.values(F).concat(['worlds/<slug>/spec.json', 'agents/swarms/<slug>.json', 'agents/advisors/<slug>.json', 'worldforge/out/<slug>/cards.json', 'worldforge/out/avatars/prompts/<slug>.json', 'agents/metaprompt.mjs (evalPrompt)']),
    delivery_rules: { 'scripted-orientation': 'the scripted advisor whose topics it is (scripted, never model-taught)', routing: 'the world’s coordinator',
      'zone-orientation': 'specialists seated in that zone', module: 'specialists the robotics registry names for that world (agents/robotics/index.json#avatars.<world>)',
      omega: 'never: Omegas are defined, not seated' },
    worlds: m.curricula.map((c) => ({ slug: c.slug, name: c.name, lessons: c.lessons.length,
      kinds: c.lessons.reduce((o, l) => ({ ...o, [l.kind]: (o[l.kind] ?? 0) + 1 }), {}), tutors: c.tutors.length,
      orientation_only: !c.lessons.some((l) => l.kind === 'module'), gaps: c.gaps.length })),
    unseated: m.unseated.map((c) => ({ slug: c.slug, lessons: c.lessons.length, gaps: c.gaps })),
    evals: checks, broken_fixtures: fx,
    totals: { worlds: m.curricula.length, unseated_worlds: m.unseated.length, lessons: lessonsN, lessons_by_kind: byKind, tutor_prompts: tutorsN,
      tutor_gates: m.curricula.reduce((n, c) => n + c.tutors.reduce((k, t) => k + t.gates.of, 0), 0),
      orientation_only_worlds: m.curricula.filter((c) => !c.lessons.some((l) => l.kind === 'module')).length, certified: 0, evals: evalsN, failing } };
  return { files, lessonsN, tutorsN, evalsN, failing, checks, fx };
}
const strip = (m) => ALL(m);
function tutorMd(c) {
  const out = [`# Tutor prompts · ${c.name} · ${PBC.umbrella}`, '',
    `Written by worldforge/training.mjs. ${c.tutors.length} tutor prompts, one per specialist or coordinator that delivers a model-taught lesson; each binds the avatar’s persona prompt (worldforge/out/avatars/prompts/${c.slug}.json) by id and sha256 and is gated by evalPrompt (agents/metaprompt.mjs). Advisors deliver only scripted orientation and have no tutor prompt; the Omega is defined, not seated, and has none. Every lesson is a draft; none is certified. No model runs these.`, ''];
  for (const t of c.tutors) out.push(`## ${t.name} · ${t.kind}`, '', `- avatar \`${t.avatarId}\` · tutor \`${t.id}\` · persona \`${t.persona_prompt?.id ?? 'none'}\``,
    `- lessons: ${t.lessons.map((l) => `\`${l}\``).join(', ')}`, `- ${t.chars} of ${MAX_PROMPT_CHARS} characters · gates ${t.gates.passed}/${t.gates.of}`, '', '```text', t.text, '```', '');
  if (c.gaps.length) out.push('## Gaps', '', ...c.gaps.map((g) => `- ${g}`), '');
  return out.join('\n');
}
const ser = (name, v) => (name.endsWith('.md') ? v : `${JSON.stringify(v, null, 1)}\n`);

function main() {
  const check = process.argv.includes('--check');
  const m = build();
  const r = render(m);
  let stale = [];
  if (check) {
    for (const [name, v] of Object.entries(r.files)) {
      const p = path.join(OUT, name);
      if (!fs.existsSync(p) || fs.readFileSync(p, 'utf8') !== ser(name, v)) stale.push(name);
    }
  } else {
    fs.mkdirSync(path.join(OUT, 'tutors'), { recursive: true });
    for (const [name, v] of Object.entries(r.files)) fs.writeFileSync(path.join(OUT, name), ser(name, v));
  }
  for (const c of r.checks.filter((x) => !x.ok)) console.log(`FAIL  ${c.name}: ${c.detail}`);
  for (const f of r.fx.filter((x) => !x.ok)) console.log(`FAIL  fixture "${f.what}" -> ${f.failed.join(', ') || 'passed'}`);
  if (stale.length) console.log(`STALE ${stale.length} files: ${stale.slice(0, 8).join(', ')}${stale.length > 8 ? ' ...' : ''} (run node worldforge/training.mjs)`);
  const lessonsSeated = m.curricula.reduce((n, c) => n + c.lessons.length, 0);
  console.log(`seated ${lessonsSeated} lessons in ${m.curricula.length} avatar worlds; ${r.lessonsN - lessonsSeated} module lessons drafted for ${m.unseated.length} world(s) with no avatar world (${m.unseated.map((u) => u.slug).join(', ')}); ${r.fx.length} broken fixtures`);
  console.log(`TRAINING: ${m.curricula.length} worlds, ${r.lessonsN} lessons, ${r.tutorsN} tutor prompts, ${r.evalsN} evals, ${r.failing} failing`);
  process.exitCode = r.failing || stale.length ? 1 : 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
