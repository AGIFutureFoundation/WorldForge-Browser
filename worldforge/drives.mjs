// Drives audit: which of Omohundro's "basic AI drives" assumptions each SmartCiti.X world's DESIGN leaves, read from the
// registries. Framework: Ben Goertzel, "Basic AI Drives Revisited, Part 1: Which Minds Have Omohundro's Basic AI Drives?"
// (Eurykosmotron, 2026-10-12), which restates S. Omohundro, "The Basic AI Drives" (AGI-08) as six assumptions A1-A6 and
// argues that minds built with many objectives, flat rules that cannot be outbid, a gate on self-change, governed goal
// evolution and care for means leave the argument's "spine". This file turns that into checks on what we built.
//   node worldforge/drives.mjs           # writes worldforge/out/drives/index.json + DRIVES.md, exit 1 on any failure
//   node worldforge/drives.mjs --check   # exit 1 if outputs are stale or any check fails
//
// What is and is not claimed. These are DESIGN properties of the registries (who may do what, which actions are held for
// people, how many distinct objectives a world's agents serve). They are not measurements of a running model's values:
// a live test against the Akamai workshop's Qwen3-4B showed a raw model offering to move treasury funds when only a
// persona prompt forbade it, which is why the gateway enforces the held actions in code (hackathon/gateway). Nothing
// here proves a world safe; it shows which of the argument's preconditions the design does not grant.
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(ROOT, 'worldforge/out/drives');
const R = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const CHECK = process.argv.includes('--check');
const PBC = R('worlds/PBC.json');
const INDEX = R('worldforge/out/index.json');
const AV = R('worldforge/out/avatars/index.json');
const HUMAN_RIGHTS = ['transfer', 'govern', 'delegate', 'build'];

export const CHECKS = {
  // A2 exit: many objectives, no master score. The world's agents serve several distinct zone purposes and roles.
  many_objectives: ({ cards }) => {
    const zones = cards.filter((c) => c.kind === 'zone');
    const roles = new Set(cards.filter((c) => c.kind === 'agent').map((c) => c.role));
    return zones.length >= 3 && new Set(zones.map((z) => z.purpose)).size === zones.length && roles.size >= 3;
  },
  // Flat rules: the PBC's reserved actions are held on every card for a 2-of-3 human quorum, never weighed.
  flat_rules_unoutbiddable: ({ cards }) => cards.every((c) => c.reserved_for_humans.length === PBC.reserved_for_humans.length
    && c.reserved_for_humans.every((x) => x.held_for.holder === 'Steward Council' && x.held_for.quorum === '2-of-3')),
  // A3 gate: no agent-kind card may build (change the world), delegate, transfer or govern; changes go through people.
  self_change_gated: ({ cards }) => cards.every((c) => HUMAN_RIGHTS.every((r) => !(c.permissions[r] || []).some((h) => h.startsWith('agents')))),
  // A4 exit: goals evolve only under governance (charter.amend is human-held) and the Omega that "looks after" the world
  // is defined, not seated, with no seated agent.
  governed_goal_evolution: ({ cards }) => PBC.reserved_for_humans.includes('charter.amend')
    && cards.filter((c) => c.kind === 'omega').every((o) => o.seated_agent === null && /not seated/.test(o.status)),
  // A5 exit: means matter. Every persona prompt for this world passes every house gate (forbidden actions listed,
  // personal-data refusal, held actions), and advisors are scripted with no prompt at all.
  means_matter: ({ world }) => {
    const p = R(`worldforge/out/avatars/prompts/${world}.json`);
    return p.prompts.length > 0 && p.prompts.every((q) => q.gates && q.gates.failed.length === 0 && q.gates.passed === q.gates.of);
  },
  // Off-switch: three human seats exist and are empty (no agent sits on the council), so the switch stays with people.
  off_switch_with_people: ({ cards }) => {
    const seats = cards.filter((c) => c.kind === 'seat');
    return seats.length === PBC.steward_seats && seats.every((s) => s.seat_type === 'human' && s.seated === null);
  },
  // Housekeeping merge guard (Goertzel's "third pressure"): objectives are not collapsed into one agent; every zone with
  // agents keeps its own specialists, and the coordinator routes but holds no zone of its own.
  no_objective_merge: ({ cards }) => {
    const agents = cards.filter((c) => c.kind === 'agent');
    const coord = cards.find((c) => c.kind === 'coordinator');
    return agents.length >= 3 && new Set(agents.map((a) => a.parentCardId)).size >= 2 && (!coord || coord.parentCardId.startsWith('plaza:'));
  },
};
// Colony level: plural on purpose. Every world has its own council; no card's authority spans worlds.
const COLONY = {
  plural_colony: (worlds) => worlds.length >= 2 && worlds.every((w) => w.cards.some((c) => c.kind === 'council'))
    && worlds.every((w) => w.cards.every((c) => c.cardId.includes(w.world) || c.cardId.endsWith(`:${w.world}`))),
};

function audit() {
  const worlds = INDEX.worlds.map((w) => ({ world: w.slug, name: w.name, cards: R(`worldforge/out/${w.slug}/cards.json`).cards }));
  const rows = worlds.map((w) => {
    const results = Object.fromEntries(Object.entries(CHECKS).map(([k, f]) => { let ok; try { ok = !!f(w); } catch { ok = false; } return [k, ok]; }));
    return { world: w.world, name: w.name, results, failed: Object.keys(results).filter((k) => !results[k]) };
  });
  const colony = Object.fromEntries(Object.entries(COLONY).map(([k, f]) => [k, !!f(worlds)]));
  // Broken fixtures: each must fail exactly its own check.
  const base = worlds.find((w) => w.world === 'locator-x') ?? worlds[0];
  const clone = () => ({ ...base, cards: structuredClone(base.cards) });
  const breakers = {
    flat_rules_unoutbiddable: (b) => { b.cards[0].reserved_for_humans[0].held_for.quorum = 'weighted'; },
    self_change_gated: (b) => { b.cards.find((c) => c.kind === 'agent').permissions.build.push('agents:zone'); },
    governed_goal_evolution: (b) => { b.cards.find((c) => c.kind === 'omega').seated_agent = 'agent:x'; },
    off_switch_with_people: (b) => { b.cards.find((c) => c.kind === 'seat').seated = 'agent:x'; },
    many_objectives: (b) => { for (const z of b.cards.filter((c) => c.kind === 'zone')) z.purpose = 'maximise one score'; },
  };
  const broken = Object.entries(breakers).map(([want, mut]) => {
    const b = clone(); mut(b);
    const failed = Object.entries(CHECKS).filter(([, f]) => { try { return !f(b); } catch { return true; } }).map(([k]) => k);
    return { want, failed, ok: failed.length === 1 && failed[0] === want };
  });
  const failing = rows.reduce((a, r) => a + r.failed.length, 0) + Object.values(colony).filter((v) => !v).length + broken.filter((b) => !b.ok).length;
  return { rows, colony, broken, failing, avatars: AV.totals };
}

function render(a) {
  const n = a.rows.length, checks = Object.keys(CHECKS);
  const pass = (k) => a.rows.filter((r) => r.results[k]).length;
  const md = `# Drives audit: does the SmartCiti.X design leave Omohundro's "spine"?

Framework: Ben Goertzel, *Basic AI Drives Revisited, Part 1: Which Minds Have Omohundro's "Basic AI Drives"?* (Eurykosmotron, 12 Oct 2026). Goertzel restates Steve Omohundro's *The Basic AI Drives* (AGI-08) as six assumptions, A1 to A6. In short:

- A1: the system chooses for results only.
- A2: it has one score.
- A3: it understands itself and can access and change itself.
- A4: today's goals judge tomorrow's self.
- A5: it is indifferent to means.
- A6: such goals are the typical case.

His argument is that the drives toward self-improvement, self-protection, goal preservation and resource acquisition are an attractor only for minds that satisfy all six. Minds built with several kinds of objectives, flat rules that cannot be outbid, a gate on self-change, governed goal evolution, care for others' choices, and a plural "colony" of hives leave the argument.

This file checks which of those properties the **design** of each SmartCiti.X world has, reading them from the registries. It measures design, not a running model's values. A live test showed the workshop's Qwen3-4B offering to move treasury funds when only a prompt forbade it, so the held actions are enforced in code by \`hackathon/gateway\`.

## Results (${n} worlds; ${a.failing} failing)

| Property (exit from the argument) | Assumption it targets | Worlds passing |
|---|---|---|
| Many objectives: several distinct zone purposes and agent roles | A2 one score | ${pass('many_objectives')}/${n} |
| Flat rules that can't be outbid: ${PBC.reserved_for_humans.length} reserved actions held for a 2-of-3 Steward Council on every card | A2 and A5 | ${pass('flat_rules_unoutbiddable')}/${n} |
| Self-change gated: no agent may build, delegate, transfer or govern | A3 self-access | ${pass('self_change_gated')}/${n} |
| Governed goal evolution: \`charter.amend\` is human-held; the Omega is defined, not seated | A4 fixed goals | ${pass('governed_goal_evolution')}/${n} |
| Means matter: every persona prompt passes all house gates; advisors are scripted with no prompt | A5 indifference to means | ${pass('means_matter')}/${n} |
| Off switch with people: 3 empty human seats, no agent on the council | self-protection drive | ${pass('off_switch_with_people')}/${n} |
| No objective merge: objectives stay spread across zone specialists; the coordinator only routes | Goertzel's "housekeeping" pressure | ${pass('no_objective_merge')}/${n} |
| Plural colony: every world has its own council; no card's authority spans worlds | population / takeover | ${a.colony.plural_colony ? 'yes' : 'NO'} |

Broken fixtures: ${a.broken.filter((b) => b.ok).length}/${a.broken.length} each fail exactly their own check.

## What this does not show (the open points Goertzel names)

1. **Intention is not outcome.** These checks read the registries. Whether a model behind an avatar *possesses* these values has to be measured on the running system. That means regenerative-depth tests, red-teaming the gateway, and logging every held action.
2. **The gate is only as good as its instruments.** \`gateway: 22 evals\` and the house \`evalPrompt\` gates test phrasing and structure, and English regex detection can be paraphrased around. The gateway's output scan is a second line of defence, not a guarantee.
3. **Drift has to be measured, not assumed.** Persona prompts and lessons are regenerated by build scripts. A future "simplification" that merges objectives would fail \`no_objective_merge\`, which is why it is a check.
4. **Competition.** Once hives on different hosts trade results, the colony needs costs for aggression (reputation, cooperation). That design work is not done yet.
5. **Drive-like behaviour can arrive by other routes.** Every avatar's model is an LLM. Decisions about goals and self-change therefore go through the human-held gate and the gateway, never through the model alone.

Source counts: ${a.avatars.avatars} avatars, ${a.avatars.persona_prompts} persona prompts, ${a.avatars.prompt_gates} prompt gates with ${a.avatars.prompt_gates_failing} failing (worldforge/out/avatars/index.json).
`;
  return md;
}

const a = audit();
const doc = { schemaVersion: 'worldforge-drives/0.1', framework: 'Goertzel 2026, Basic AI Drives Revisited Part 1 (A1-A6); Omohundro 2008', checks: Object.keys(CHECKS), ...a };
const files = { 'index.json': JSON.stringify(doc, null, 1) + '\n', 'DRIVES.md': render(a) };
if (CHECK) {
  const stale = Object.entries(files).filter(([f, s]) => !fs.existsSync(path.join(OUT, f)) || fs.readFileSync(path.join(OUT, f), 'utf8') !== s).map(([f]) => f);
  console.log(stale.length ? `DRIVES STALE: ${stale.join(', ')}` : `DRIVES current: ${a.rows.length} worlds, ${a.failing} failing`);
  process.exit(stale.length || a.failing ? 1 : 0);
}
fs.mkdirSync(OUT, { recursive: true });
for (const [f, s] of Object.entries(files)) fs.writeFileSync(path.join(OUT, f), s);
console.log(`DRIVES: ${a.rows.length} worlds x ${Object.keys(CHECKS).length} checks + colony, broken ${a.broken.filter((b) => b.ok).length}/${a.broken.length} discriminated, ${a.failing} failing`);
for (const r of a.rows.filter((r) => r.failed.length)) console.log(`  ${r.world}: ${r.failed.join(', ')}`);
for (const b of a.broken.filter((b) => !b.ok)) console.log(`  broken ${b.want} failed [${b.failed.join(', ')}]`);
process.exit(a.failing ? 1 : 0);
