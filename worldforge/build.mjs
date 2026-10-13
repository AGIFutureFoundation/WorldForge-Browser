// WorldForge: the SmartCiti.X Master Card layer for every coming-soon world, carried through the gates the
// ChatGPT "Create SmartCiti.X Roadmap" thread laid out (generated core -> card-tagged GLB -> Sneeze mount plan).
//   node worldforge/build.mjs           # writes worldforge/out/, runs every world's evals, exit 1 on any failure
//   node worldforge/build.mjs --check   # exit 1 if worldforge/out/ is behind its sources (writes nothing)
//
// Per world (from my-fabric/worlds/index.json, worlds/PBC.json and agents/advisory/omega_agents.json):
//   cards.json                  Master Cards: world -> plaza, gate, council (3 human seats), zones -> agent avatars.
//                               Each card carries its owner, its Volum (the bounded 3-D region it governs) and a
//                               permission matrix. Agents operate; people govern: no agent card ever holds a right
//                               the PBC reserves for humans, and those rights are held for a 2-of-3 steward quorum.
//   blockout.generated.json     the generated core: zones, primitives and roads in metres, deterministic.
//   <slug>.glb                  glTF 2.0 binary, one shared unit-cube mesh, every node tagged with its cardId and
//                               parentCardId in extras so a native loader can index cards without display names.
//   sneeze-mount-plan.json      ordered SOM node specs (parents first) for CONTAINER::Node_Open, resource URL
//                               under the 128-byte Resource.sReference limit; plan only, nothing mounted.
//   manifest.json               hashes and counts for conformance.
//
// What is and is not claimed. Zones and agents come from the world's own spec and keep its source citations;
// geometry is synthetic placeholder massing (no imported coordinates, no imported geometry). The GLB is
// re-parsed here in JavaScript, which proves the file and its card tree, not that Sneeze has loaded or rendered
// it: Sneeze is not checked out in this project, and the native gates stay open until it is.
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');
const OUT = path.join(HERE, 'out');
const R = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const CHECK = process.argv.includes('--check');

export const SOURCES = ['my-fabric/worlds/index.json', 'worlds/PBC.json', 'agents/advisory/omega_agents.json', 'agents/hive/index.json', 'my-fabric/worlds/spaces_index.json', 'agents/swarms/*.json', 'worldforge/build.mjs'];
export const AVATAR_DIR = 'worldforge/out/assets/avatars';
export const AVATAR_ROLES = ['specialist', 'coordinator', 'omega', 'host', 'liaison', 'alignment'];
export const ASSET_URL = 'http://127.0.0.1:8789/unit-cube.glb';
export const NAME_LIMIT = 47;                       // Sneeze wsName[48] keeps a NUL (Map_Object.h:28), so 47 UTF-16 units
                                                    // round-trip; Artemis 0.4.0 aborts above 48, so 47 satisfies both.
export const RP1_NAME_BYTES = 47;                   // RP1 JSON route copies UTF-8 bytes one per unit: ASCII, <= 47 bytes
/** ASCII-safe native name for RP1/Sneeze JSON fabrics: '·' -> '-', '…' -> '~', other non-ASCII -> '?', clamped. */
export function rp1Name(s) {
  const a = s.replace(/\u00b7/g, '-').replace(/\u2026/g, '~').replace(/[^\x20-\x7e]/g, '?');
  return a.length <= RP1_NAME_BYTES ? a : a.slice(0, RP1_NAME_BYTES - 1) + '~';
}
export const RESOURCE_LIMIT = 128;                  // Sneeze Resource.sReference field
export const RIGHTS = ['view', 'enter', 'build', 'operate', 'delegate', 'transfer', 'govern'];
const HUMAN_ONLY_RIGHTS = ['transfer', 'govern', 'delegate'];
export const COUNCIL_ZONE = 'Steward Council';

const PBC = R('worlds/PBC.json');
const INDEX = R('my-fabric/worlds/index.json');
const OMEGAS = new Map(R('agents/advisory/omega_agents.json').omegas.map((o) => [o.corporation?.world, o]));
const optional = (p) => (fs.existsSync(path.join(ROOT, p)) ? R(p) : null);
const HIVE = new Map((optional('agents/hive/index.json')?.omegas ?? []).map((o) => [o.world, o]));
const SPACES = new Map((optional('my-fabric/worlds/spaces_index.json')?.worlds ?? []).map((w) => [w.slug, w]));
const SWARMS = new Map(INDEX.worlds.map((w) => [w.slug, new Set((optional(`agents/swarms/${w.slug}.json`)?.agents ?? []).map((a) => a.id))]));
const COORDS = new Map(INDEX.worlds.map((w) => { const sw = optional(`agents/swarms/${w.slug}.json`); return [w.slug, sw?.coordinator ? { ...sw.coordinator, topology: sw.topology } : null]; }));
const ADVISORS = new Map(INDEX.worlds.map((w) => [w.slug, (optional(`agents/advisors/${w.slug}.json`)?.advisors ?? []).map((a) => ({ id: a.id, name: a.name, manages: a.manages }))]));
const ADVISOR_ROLE = { host: 'host', steward: 'liaison', alignment: 'alignment' };   // advisor id -> avatar role
const MODELS_DIR = 'my-fabric/worlds/models';

/** Only the fields this build reads, so the advisory beat's run_at stamps and hive voicing progress don't stale it. */
export function sourceDigest() {
  const slice = {
    index: INDEX, pbc: PBC, build: fs.readFileSync(fileURLToPath(import.meta.url), 'utf8'),
    omegas: [...OMEGAS].map(([w, o]) => [w, o.id, o.status, o.seated_agent]),
    hive: [...HIVE].map(([w, o]) => [w, o.id, o.title, o.persona, o.voice?.kokoro, (o.lines ?? []).map((l) => [l.id, l.text])]),
    spaces: [...SPACES].map(([w, s]) => [w, s.exteriors, s.interiors]),
    swarms: [...SWARMS].map(([w, ids]) => [w, [...ids].sort()]),
    coordinators: [...COORDS], advisors: [...ADVISORS],
  };
  return sha256(JSON.stringify(slice));
}

/** A zone's building in the peer's spaces build: exterior shell, interior fit-out and its own room GLB. */
function buildingFor(slugW, zoneName) {
  const s = SPACES.get(slugW);
  const ext = s?.exteriors.find((e) => e.zone === zoneName);
  if (!ext) return null;
  const int = s.interiors.find((e) => e.zone === zoneName);
  return {
    kind: ext.kind, exterior: `${MODELS_DIR}/${ext.model}`, interior: int ? `${MODELS_DIR}/${int.model}` : null,
    room: `${MODELS_DIR}/${ext.room_model}`, door: ext.door, sign: ext.sign,
    resolution: { exterior: ext.resolution, interior: int?.resolution ?? null }, triangles: { exterior: ext.triangles, interior: int?.triangles ?? null },
    source: `my-fabric/worlds/spaces_index.json#worlds[slug=${slugW}]`,
  };
}
const avatarRef = (role) => `${AVATAR_DIR}/${role}.glb`;
function binding(slugW, name) {
  return { swarm: `${slugW}.${slug(name)}`, metaprompt: `agents/prompts/${slugW}.json`, fabricNode: `Agent · ${name}`, registry: `my-fabric/worlds/index.json#worlds[slug=${slugW}].agents[name=${name}]` };
}

const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const sha256 = (b) => createHash('sha256').update(b).digest('hex');
const r2 = (v) => Math.round(v * 100) / 100;
const stable = (v) => JSON.stringify(v, null, 1) + '\n';

/** "<label> · <umbrella>" within the node-name limit; the label is shortened, the umbrella never is. */
export function nodeName(label) {
  const tail = ` · ${PBC.umbrella}`;
  const budget = NAME_LIMIT - tail.length;
  return (label.length <= budget ? label : label.slice(0, budget - 1).trimEnd() + '…') + tail;
}

// ------------------------------------------------------------------------------------- master cards ----
const STEWARD_QUORUM = { holder: 'Steward Council', quorum: '2-of-3', seats: PBC.steward_seats };

function permissions(kind) {
  // Who may do what on a card. Agents get view/enter/operate on their own zone and nothing a person reserves.
  const p = Object.fromEntries(RIGHTS.map((r) => [r, []]));
  p.view = ['public'];
  p.enter = kind === 'council' || kind === 'seat' ? ['stewards'] : ['public'];
  p.build = ['stewards'];
  p.operate = kind === 'zone' || kind === 'agent' || kind === 'plaza' || kind === 'coordinator' ? ['stewards', 'agents:zone'] : ['stewards'];
  p.delegate = ['stewards'];
  p.transfer = ['steward-quorum'];
  p.govern = ['steward-quorum'];
  return p;
}

function card(id, kind, parent, fields) {
  return {
    cardId: id, kind, parentCardId: parent,
    owner: PBC.name, umbrella: PBC.umbrella,
    permissions: permissions(kind),
    reserved_for_humans: PBC.reserved_for_humans.map((action) => ({ action, held_for: STEWARD_QUORUM })),
    ...fields,
  };
}

/** Volum: a named, bounded 3-D region (centre + half-extents, metres, world frame). */
const volum = (c, half) => ({ shape: 'box', center: c.map(r2), halfExtents: half.map(r2) });

export function buildWorld(w) {
  const root = `world:${w.slug}`;
  // Every spec lists the Steward Council as a zone. It is folded into the one council card (keeping the spec's
  // purpose and citation) instead of becoming a zone, because a zone is operated by agents and a council is not.
  const councilZone = w.zones.find((z) => z.name === COUNCIL_ZONE);
  const zones = w.zones.filter((z) => z.name !== COUNCIL_ZONE);
  const ring = 60 + zones.length * 6;                 // zone ring radius grows with zone count
  const cards = [];
  const prims = [];
  const roads = [];
  const zoneOut = [];
  const omega = OMEGAS.get(w.slug);

  cards.push(card(root, 'world', null, {
    displayName: nodeName(w.name), name: w.name, tagline: w.tagline, status: w.status,
    management_style: w.management_style ?? PBC.management_style.name,
    anchor: w.anchor ?? null,
    omega_steward: omega ? { id: omega.id, status: omega.status, seated_agent: omega.seated_agent, source: 'agents/advisory/omega_agents.json' } : null,
    volum: volum([0, 40, 0], [ring + 60, 40, ring + 60]),
    source: 'my-fabric/worlds/index.json',
  }));

  // Plaza, gate and council are the PBC's shared management model: every world has them.
  const plaza = `plaza:${w.slug}`;
  cards.push(card(plaza, 'plaza', root, { displayName: nodeName(`${w.name} Plaza`), purpose: 'the shared round plaza every world opens onto', volum: volum([0, 5, 0], [24, 5, 24]), source: 'README.md (shared PBC management model)' }));
  prims.push({ primitiveId: `${plaza}/floor`, parentCardId: plaza, zoneCardId: null, shape: 'pad', massingType: 'plaza', position: [0, 0, 0], dimensions: [48, 0.4, 48] });

  // The swarm coordinator and the three scripted advisors (Host, Steward Liaison, Alignment) stand on the plaza.
  const coord = COORDS.get(w.slug);
  if (coord) {
    const cid = `coordinator:${w.slug}`;
    cards.push(card(cid, 'coordinator', plaza, {
      displayName: nodeName(coord.name), name: coord.name, role: `swarm coordinator (${coord.topology ?? 'hub'}): routes turns, answers unroutable ones, hands off to specialists`,
      avatar: { kind: 'agent-avatar', role: 'coordinator', model_ref: avatarRef('coordinator'), seated_model: null },
      binding: { swarm: coord.id, metaprompt: `agents/prompts/${w.slug}.json`, fabricNode: `Agent · ${coord.name}` },
      may_never: PBC.reserved_for_humans, volum: volum([0, 1, 8], [1, 1, 1]), source: `agents/swarms/${w.slug}.json#coordinator`,
    }));
    prims.push({ primitiveId: `${cid}/avatar`, parentCardId: cid, zoneCardId: null, shape: 'capsule', massingType: 'agent-avatar', position: [0, 0.4, 8], dimensions: [1, 1.8, 1] });
  }
  ADVISORS.get(w.slug).forEach((a, k) => {
    const aid = `advisor:${w.slug}/${a.id}`;
    const ang = Math.PI * (0.25 + 0.25 * k);           // NE, N-ish arc behind the coordinator, clear of the gate road
    const ax = r2(Math.cos(ang) * 14), az = r2(-Math.sin(ang) * 14);
    cards.push(card(aid, 'advisor', plaza, {
      displayName: nodeName(a.name), name: a.name, manages: a.manages, scripted: true,
      note: 'a scripted guide under the advisor contract (agents/advisors), not an AI model',
      avatar: { kind: 'advisor-avatar', role: ADVISOR_ROLE[a.id] ?? 'host', model_ref: avatarRef(ADVISOR_ROLE[a.id] ?? 'host'), seated_model: null },
      may_never: PBC.reserved_for_humans, volum: volum([ax, 1, az], [1, 1, 1]), source: `agents/advisors/${w.slug}.json#advisors[id=${a.id}]`,
    }));
    prims.push({ primitiveId: `${aid}/avatar`, parentCardId: aid, zoneCardId: null, shape: 'capsule', massingType: 'agent-avatar', position: [ax, 0.4, az], dimensions: [1, 1.8, 1] });
  });

  const gate = `gate:${w.slug}`;
  cards.push(card(gate, 'gate', root, { displayName: nodeName('Alignment Evaluation Gate'), purpose: PBC.programs.find((p) => p.name === 'Alignment Evaluation Gate')?.what, volum: volum([0, 6, ring + 40], [10, 6, 3]), source: 'worlds/PBC.json#programs' }));
  prims.push({ primitiveId: `${gate}/arch`, parentCardId: gate, zoneCardId: null, shape: 'arch', massingType: 'gate', position: [0, 0, ring + 40], dimensions: [16, 10, 2] });
  roads.push({ primitiveId: `road:${w.slug}/gate`, startXZ: [0, ring + 40], endXZ: [0, 24], widthMeters: 8 });

  const council = `council:${w.slug}`;
  cards.push(card(council, 'council', root, {
    displayName: nodeName(COUNCIL_ZONE), name: COUNCIL_ZONE,
    purpose: councilZone?.purpose ?? `${PBC.steward_seats} human seats; ${PBC.management_style.humans_hold.join(', ')}`,
    volum: volum([0, 6, -(ring + 40)], [14, 6, 10]), source: councilZone?.source ?? 'worlds/PBC.json#steward_seats',
    building: buildingFor(w.slug, COUNCIL_ZONE),
  }));
  prims.push({ primitiveId: `${council}/chamber`, parentCardId: council, zoneCardId: null, shape: 'box', massingType: 'council', position: [0, 0, -(ring + 40)], dimensions: [28, 8, 20] });
  roads.push({ primitiveId: `road:${w.slug}/council`, startXZ: [0, -24], endXZ: [0, -(ring + 30)], widthMeters: 6 });
  for (let i = 1; i <= PBC.steward_seats; i++) {
    const seat = `seat:${w.slug}/steward-${i}`;
    const x = (i - 2) * 6;
    cards.push(card(seat, 'seat', council, { displayName: nodeName(`Steward Seat ${i}`), seat_type: 'human', seated: null, volum: volum([x, 1, -(ring + 40)], [1.5, 1, 1.5]), source: 'worlds/PBC.json#steward_seats' }));
    prims.push({ primitiveId: `${seat}/chair`, parentCardId: seat, zoneCardId: council, shape: 'box', massingType: 'seat', position: [x, 8, -(ring + 40)], dimensions: [2, 2, 2] });
  }

  // The Omega Steward stands beside the council, never in it: defined, not seated, and bound to its hive persona.
  const hive = HIVE.get(w.slug);
  if (omega) {
    const oid = `omega:${w.slug}`;
    const ox = 26, oz = -(ring + 40);
    cards.push(card(oid, 'omega', root, {
      displayName: nodeName('Omega Steward'), name: omega.title, omega_id: omega.id, status: omega.status, seated_agent: omega.seated_agent,
      persona: hive ? { temperament: hive.persona?.temperament, style: hive.persona?.style, values: hive.persona?.values, refuses: hive.persona?.refuses } : null,
      voice: hive ? { kokoro: hive.voice?.kokoro, browser_fallback: hive.voice?.browser_fallback ?? null, audio_note: 'audio is the expected path; it exists once the hive voices the line (agents/hive.mjs --voice), else the viewer falls back to a labelled browser voice', lines: (hive.lines ?? []).map((l) => ({ id: l.id, text: l.text, audio: `agents/hive/voices/${w.slug}/${l.id}.mp4` })) } : null,
      hive_ref: hive ? `agents/hive/index.json#omegas[world=${w.slug}]` : null,
      avatar: { kind: 'omega-avatar', role: 'omega', model_ref: avatarRef('omega'), seated_model: null },
      may_never: PBC.reserved_for_humans,
      volum: volum([ox, 1, oz], [1.5, 1.2, 1.5]), source: 'agents/advisory/omega_agents.json',
    }));
    prims.push({ primitiveId: `${oid}/avatar`, parentCardId: oid, zoneCardId: null, shape: 'capsule', massingType: 'agent-avatar', position: [ox, 0.4, oz], dimensions: [1.2, 2.2, 1.2] });
  }

  zones.forEach((z, i) => {
    // Zones sit on a ring, skipping the gate (south) and council (north) axes.
    const a = (i + 0.5) / zones.length * Math.PI * 2 + Math.PI / 2;
    const cx = Math.cos(a) * ring, cz = Math.sin(a) * ring;
    const zid = `zone:${w.slug}/${slug(z.name)}`;
    const zAgents = w.agents.filter((g) => g.zone === z.name);
    const towerH = 12 + 4 * zAgents.length;
    cards.push(card(zid, 'zone', root, { displayName: nodeName(z.name), name: z.name, purpose: z.purpose, building: buildingFor(w.slug, z.name), volum: volum([cx, towerH / 2, cz], [18, towerH / 2 + 2, 18]), source: z.source }));
    zoneOut.push({ cardId: zid, displayName: z.name, centerXZ: [r2(cx), r2(cz)], researchTags: [], evidenceStatus: 'cited-in-spec' });
    prims.push({ primitiveId: `${zid}/pad`, parentCardId: zid, zoneCardId: zid, shape: 'pad', massingType: 'zone-pad', position: [r2(cx), 0, r2(cz)], dimensions: [32, 0.4, 32] });
    prims.push({ primitiveId: `${zid}/hall`, parentCardId: zid, zoneCardId: zid, shape: 'box', massingType: 'zone-hall', position: [r2(cx - Math.cos(a) * 8), 0.4, r2(cz - Math.sin(a) * 8)], dimensions: [14, towerH, 10] });
    roads.push({ primitiveId: `road:${w.slug}/${slug(z.name)}`, startXZ: [r2(Math.cos(a) * 24), r2(Math.sin(a) * 24)], endXZ: [r2(Math.cos(a) * (ring - 16)), r2(Math.sin(a) * (ring - 16))], widthMeters: 6 });
    zAgents.forEach((g, j) => {
      const gid = `agent:${w.slug}/${slug(g.name)}`;
      const ox = cx + Math.cos(a) * 6 + (j - (zAgents.length - 1) / 2) * 3.5 * -Math.sin(a);
      const oz = cz + Math.sin(a) * 6 + (j - (zAgents.length - 1) / 2) * 3.5 * Math.cos(a);
      cards.push(card(gid, 'agent', zid, {
        displayName: nodeName(g.name), name: g.name, role: g.role,
        avatar: { kind: 'agent-avatar', role: 'specialist', model_ref: avatarRef('specialist'), seated_model: null },
        binding: binding(w.slug, g.name),
        may_never: PBC.reserved_for_humans,
        volum: volum([ox, 1, oz], [1, 1, 1]), source: g.source,
      }));
      prims.push({ primitiveId: `${gid}/avatar`, parentCardId: gid, zoneCardId: zid, shape: 'capsule', massingType: 'agent-avatar', position: [r2(ox), 0.4, r2(oz)], dimensions: [1, 1.8, 1] });
    });
  });

  // An agent whose zone the spec does not name still gets a card, parented to the plaza and listed as a gap.
  const gaps = [];
  for (const g of w.agents.filter((g) => !zones.some((z) => z.name === g.zone))) {
    const gid = `agent:${w.slug}/${slug(g.name)}`;
    gaps.push(`agent "${g.name}" names zone "${g.zone}", which the spec does not list; parented to the plaza`);
    cards.push(card(gid, 'agent', plaza, { displayName: nodeName(g.name), name: g.name, role: g.role, avatar: { kind: 'agent-avatar', role: 'specialist', model_ref: avatarRef('specialist'), seated_model: null }, binding: binding(w.slug, g.name), may_never: PBC.reserved_for_humans, volum: volum([0, 1, 0], [1, 1, 1]), source: g.source }));
    prims.push({ primitiveId: `${gid}/avatar`, parentCardId: gid, zoneCardId: null, shape: 'capsule', massingType: 'agent-avatar', position: [0, 0.4, 0], dimensions: [1, 1.8, 1] });
  }
  if (!w.anchor?.lat) gaps.push('no RP1 anchor yet: lat/lon are null until a steward writes them into worlds/focus.json');
  if (!omega) gaps.push('no Omega Steward defined for this world in agents/advisory/omega_agents.json');

  const blockout = {
    schemaVersion: 'worldforge-blockout/0.1', blockoutId: `blockout:${w.slug}`, rootCardId: root,
    coordinateFrame: { units: 'metres', up: 'Y', extentXZ: [-(ring + 60), ring + 60] },
    provenance: { authorship: 'independently-generated-synthetic-massing', sourceCoordinatesImported: false, externalGeometryImported: false, spec: 'my-fabric/worlds/index.json' },
    zones: zoneOut, primitives: prims, roads,
  };
  return { world: w, cards, blockout, gaps };
}

// ---------------------------------------------------------------------------------------------- GLB ----
const pad4 = (b, fill) => Buffer.concat([b, Buffer.alloc((4 - (b.length % 4)) % 4, fill)]);
const COLORS = { plaza: [0.78, 0.8, 0.84], gate: [0.95, 0.75, 0.25], council: [0.55, 0.42, 0.75], seat: [0.7, 0.55, 0.9], 'zone-pad': [0.4, 0.6, 0.7], 'zone-hall': [0.62, 0.67, 0.72], 'agent-avatar': [0.2, 0.8, 0.6], road: [0.3, 0.3, 0.33], ground: [0.22, 0.27, 0.22] };
const MAT_KEYS = Object.keys(COLORS);

function cubeBuffers() {
  const faces = [
    [[[-.5, -.5, .5], [.5, -.5, .5], [.5, .5, .5], [-.5, .5, .5]], [0, 0, 1]],
    [[[.5, -.5, -.5], [-.5, -.5, -.5], [-.5, .5, -.5], [.5, .5, -.5]], [0, 0, -1]],
    [[[.5, -.5, .5], [.5, -.5, -.5], [.5, .5, -.5], [.5, .5, .5]], [1, 0, 0]],
    [[[-.5, -.5, -.5], [-.5, -.5, .5], [-.5, .5, .5], [-.5, .5, -.5]], [-1, 0, 0]],
    [[[-.5, .5, .5], [.5, .5, .5], [.5, .5, -.5], [-.5, .5, -.5]], [0, 1, 0]],
    [[[-.5, -.5, -.5], [.5, -.5, -.5], [.5, -.5, .5], [-.5, -.5, .5]], [0, -1, 0]],
  ];
  const pos = [], nrm = [], idx = [];
  faces.forEach(([vs, n], i) => { vs.forEach((v) => { pos.push(...v); nrm.push(...n); }); const b = i * 4; idx.push(b, b + 1, b + 2, b, b + 2, b + 3); });
  return { pos: Buffer.from(new Float32Array(pos).buffer), nrm: Buffer.from(new Float32Array(nrm).buffer), idx: Buffer.from(new Uint16Array(idx).buffer), vcount: pos.length / 3, icount: idx.length };
}

/** glTF 2.0 binary. `nodes` is [{name, extras, translation, rotation, scale, mat|null, children:[indices]}], node 0 is the root. */
export function writeGlb(nodes, generator, materials = MAT_KEYS) {
  const c = cubeBuffers();
  const bin = Buffer.concat([c.pos, c.nrm, c.idx]);
  const meshes = materials.map((m) => ({ name: `WF_Cube_${m}`, primitives: [{ attributes: { POSITION: 0, NORMAL: 1 }, indices: 2, material: materials.indexOf(m), mode: 4 }] }));
  const doc = {
    asset: { version: '2.0', generator, extras: { authorship: 'independently-generated-generic-geometry', externalGeometryImported: false, sourceCoordinatesImported: false } },
    scene: 0, scenes: [{ name: generator, nodes: [0] }],
    nodes: nodes.map((n) => {
      const o = { name: n.name, extras: n.extras };
      if (n.translation) o.translation = n.translation;
      if (n.rotation) o.rotation = n.rotation;
      if (n.scale) o.scale = n.scale;
      if (n.mat != null) o.mesh = materials.indexOf(n.mat);
      if (n.children?.length) o.children = n.children;
      return o;
    }),
    meshes,
    materials: materials.map((m) => ({ name: `WF_${m}`, pbrMetallicRoughness: { baseColorFactor: [...(COLORS[m] ?? [0.6, 0.6, 0.6]), 1], metallicFactor: 0, roughnessFactor: 0.9 } })),
    buffers: [{ byteLength: bin.length }],
    bufferViews: [
      { buffer: 0, byteOffset: 0, byteLength: c.pos.length, target: 34962 },
      { buffer: 0, byteOffset: c.pos.length, byteLength: c.nrm.length, target: 34962 },
      { buffer: 0, byteOffset: c.pos.length + c.nrm.length, byteLength: c.idx.length, target: 34963 },
    ],
    accessors: [
      { bufferView: 0, componentType: 5126, count: c.vcount, type: 'VEC3', min: [-0.5, -0.5, -0.5], max: [0.5, 0.5, 0.5] },
      { bufferView: 1, componentType: 5126, count: c.vcount, type: 'VEC3' },
      { bufferView: 2, componentType: 5123, count: c.icount, type: 'SCALAR', min: [0], max: [23] },
    ],
  };
  const j = pad4(Buffer.from(JSON.stringify(doc)), 0x20);
  const b = pad4(bin, 0);
  const header = Buffer.alloc(12); header.write('glTF', 0); header.writeUInt32LE(2, 4); header.writeUInt32LE(12 + 8 + j.length + 8 + b.length, 8);
  const ch = (len, type) => { const h = Buffer.alloc(8); h.writeUInt32LE(len, 0); h.write(type, 4, 'latin1'); return h; };
  return Buffer.concat([header, ch(j.length, 'JSON'), j, ch(b.length, 'BIN\0'), b]);
}

/** Parse a GLB back: header, chunks, JSON. Throws on any structural fault. */
export function readGlb(buf) {
  if (buf.toString('latin1', 0, 4) !== 'glTF') throw new Error('bad magic');
  if (buf.readUInt32LE(4) !== 2) throw new Error('not glTF 2');
  if (buf.readUInt32LE(8) !== buf.length) throw new Error('length mismatch');
  const jlen = buf.readUInt32LE(12);
  if (buf.toString('latin1', 16, 20) !== 'JSON') throw new Error('first chunk is not JSON');
  const doc = JSON.parse(buf.toString('utf8', 20, 20 + jlen));
  const boff = 20 + jlen;
  if (buf.toString('latin1', boff + 4, boff + 8) !== 'BIN\0') throw new Error('second chunk is not BIN');
  if (buf.readUInt32LE(boff) < doc.buffers[0].byteLength) throw new Error('BIN chunk shorter than buffer');
  return doc;
}

/** Card-tagged GLB from the blockout: root -> card nodes (empty) -> primitive nodes (meshes), tree mirrors cards. */
export function blockoutToGlb(built) {
  const { cards, blockout } = built;
  const nodes = [];
  const at = new Map();
  const centre = (c) => c.volum.center;
  for (const c of cards) {
    const parent = c.parentCardId ? nodes[at.get(c.parentCardId)] : null;
    const pc = parent ? cards.find((x) => x.cardId === c.parentCardId) : null;
    const t = c.parentCardId ? centre(c).map((v, i) => r2(v - centre(pc)[i])) : [0, 0, 0];
    const n = { name: c.displayName, translation: [t[0], 0, t[2]], extras: { cardId: c.cardId, parentCardId: c.parentCardId, kind: c.kind }, children: [], _abs: c.parentCardId ? [centre(c)[0], (parent._abs?.[1] ?? 0), centre(c)[2]] : [0, 0, 0] };
    n._abs[1] = 0;
    if (!c.parentCardId) Object.assign(n.extras, { blockoutId: blockout.blockoutId, authorship: blockout.provenance.authorship, sourceCoordinatesImported: false, externalGeometryImported: false });
    at.set(c.cardId, nodes.length);
    if (parent) parent.children.push(nodes.length);
    nodes.push(n);
  }
  const abs = (i) => { let x = 0, z = 0, k = i; const parents = new Map(); nodes.forEach((n, p) => n.children.forEach((ch) => parents.set(ch, p))); while (k != null) { x += nodes[k].translation[0]; z += nodes[k].translation[2]; k = parents.get(k); } return [x, z]; };
  const addMesh = (parentIdx, id, mat, pos, dims, extras, rotation) => {
    const [ax, az] = abs(parentIdx);
    nodes.push({ name: id.slice(-NAME_LIMIT), mat, translation: [r2(pos[0] - ax), r2(pos[1]), r2(pos[2] - az)], scale: dims, rotation, extras: { worldforgePrimitiveId: id, ...extras }, children: [] });
    nodes[parentIdx].children.push(nodes.length - 1);
  };
  const ext = blockout.coordinateFrame.extentXZ[1] * 2;
  addMesh(0, `ground:${built.world.slug}`, 'ground', [0, -0.1, 0], [ext, 0.2, ext], { parentCardId: blockout.rootCardId, zoneCardId: null, shape: 'ground' });
  for (const p of blockout.primitives) {
    const mat = MAT_KEYS.includes(p.massingType) ? p.massingType : 'zone-hall';
    const cy = p.shape === 'pad' ? p.position[1] + p.dimensions[1] / 2 : p.position[1] + p.dimensions[1] / 2;
    addMesh(at.get(p.parentCardId), p.primitiveId, mat, [p.position[0], cy, p.position[2]], p.dimensions, { parentCardId: p.parentCardId, zoneCardId: p.zoneCardId, shape: p.shape });
  }
  for (const rd of blockout.roads) {
    const [ax, az] = rd.startXZ, [bx, bz] = rd.endXZ;
    const dx = bx - ax, dz = bz - az, len = Math.hypot(dx, dz), yaw = Math.atan2(dx, dz);
    addMesh(0, rd.primitiveId, 'road', [(ax + bx) / 2, 0.04, (az + bz) / 2], [rd.widthMeters, 0.08, r2(len)], { parentCardId: blockout.rootCardId, zoneCardId: null, shape: 'road_segment' }, [0, r2(Math.sin(yaw / 2) * 1e4) / 1e4, 0, r2(Math.cos(yaw / 2) * 1e4) / 1e4]);
  }
  nodes.forEach((n) => { delete n._abs; });
  return writeGlb(nodes, `WorldForge SmartCiti.X Core · ${built.world.slug}`);
}

// ------------------------------------------------------------------------------------- mount plan ----
export function mountPlan(built, glbHash, cubeHash) {
  const { cards, blockout } = built;
  const nodes = cards.map((c) => ({
    cardId: c.cardId, displayName: rp1Name(c.displayName), parentCardId: c.parentCardId,
    nativeClass: 'MAP_OBJECT_TERRESTRIAL', bound: { d3Max: c.volum.halfExtents },
    transform: { translation: c.parentCardId ? c.volum.center.map((v, i) => r2(v - cards.find((x) => x.cardId === c.parentCardId).volum.center[i])).map((v, i) => (i === 1 ? 0 : v)) : [0, 0, 0], rotation: [0, 0, 0, 1], scale: [1, 1, 1] },
    resource: null, extras: { kind: c.kind, label: c.displayName, source: c.source },
  }));
  const centreOf = new Map(cards.map((c) => [c.cardId, c.volum.center]));
  const absOf = (id) => { let x = 0, z = 0, k = id; while (k) { const n = nodes.find((m) => m.cardId === k); x += n.transform.translation[0]; z += n.transform.translation[2]; k = n.parentCardId; } return [x, z]; };
  for (const p of blockout.primitives) {
    const [ax, az] = absOf(p.parentCardId);
    nodes.push({
      cardId: p.primitiveId, displayName: rp1Name(p.primitiveId.slice(-NAME_LIMIT)), parentCardId: p.parentCardId, nativeClass: 'MAP_OBJECT_PHYSICAL', bound: { d3Max: p.dimensions.map((d) => r2(d / 2)) },
      transform: { translation: [r2(p.position[0] - ax), r2(p.position[1] + p.dimensions[1] / 2), r2(p.position[2] - az)], rotation: [0, 0, 0, 1], scale: p.dimensions },
      resource: { sReference: ASSET_URL }, extras: { zoneCardId: p.zoneCardId, shape: p.shape, massingType: p.massingType, geometrySource: 'procedurally-generated-original' },
    });
  }
  void centreOf;
  return {
    schemaVersion: 'worldforge-sneeze-mount-plan/0.1', engine: 'Sneeze',
    bindingStatus: 'decoder-available-not-mounted',
    bindingNote: 'worldforge/native/rmcobject_decoder.* encodes these nodes against Sneeze headers (Y-up -> Z-up conversion in the decoder); nothing is mounted or rendered yet',
    rp1: { nameRule: 'ASCII, <= 47 bytes (displayName); UTF-8 label in extras.label', bound: 'd3Max = half-extents in metres from the card Volum or primitive size' },
    rootCardId: blockout.rootCardId, mountParent: 'SCENE::Fabric_Root()->Node_Root()',
    resourceCachePolicy: 'shared-by-exact-sReference-URL',
    coordinateFrame: blockout.coordinateFrame,
    assets: [{ url: ASSET_URL, localPath: 'worldforge/out/assets/unit-cube.glb', sha256: cubeHash, role: 'shared-generic-unit-cube' }],
    previewGlb: { path: `worldforge/out/${built.world.slug}/${built.world.slug}.glb`, sha256: glbHash },
    nodes,
    acceptanceRequirements: [
      'Parent nodes must be created before child nodes',
      'Each returned native handle must resolve via CONTAINER::Node_Find',
      'Every resource-bearing NODE must eventually expose Gltf_Render_Model()!=nullptr',
      'Timeout/fetch/parse failure must fail the load',
      'Scene mutations must use the engine\'s safe lifecycle/thread boundary',
    ],
  };
}

// ------------------------------------------------------------------------------------------- evals ----
export const EVALS = {
  unique_ids: ({ cards, plan }) => new Set(plan.nodes.map((n) => n.cardId)).size === plan.nodes.length && new Set(cards.map((c) => c.cardId)).size === cards.length,
  parents_first: ({ plan }) => { const seen = new Set(); return plan.nodes.every((n) => { const ok = n.parentCardId === null || seen.has(n.parentCardId); seen.add(n.cardId); return ok; }); },
  single_root: ({ cards }) => cards.filter((c) => c.parentCardId === null).length === 1 && cards[0].kind === 'world',
  umbrella_in_names: ({ cards }) => cards.every((c) => c.displayName.endsWith(` · ${PBC.umbrella}`)),
  name_limit: ({ plan }) => plan.nodes.every((n) => n.displayName.length <= NAME_LIMIT),
  agents_hold_no_reserved_right: ({ cards }) => cards.every((c) => HUMAN_ONLY_RIGHTS.every((r) => !c.permissions[r].some((h) => h.startsWith('agents')))),
  reserved_actions_verbatim: ({ cards }) => cards.every((c) => c.reserved_for_humans.map((x) => x.action).join() === PBC.reserved_for_humans.join() && c.reserved_for_humans.every((x) => x.held_for.quorum === '2-of-3')),
  three_human_seats: ({ cards }) => { const s = cards.filter((c) => c.kind === 'seat'); return s.length === PBC.steward_seats && s.every((x) => x.seat_type === 'human' && x.seated === null); },
  no_agent_on_council: ({ cards }) => { const council = cards.find((c) => c.kind === 'council'); return !cards.some((c) => c.kind === 'agent' && (c.parentCardId === council?.cardId || cards.find((p) => p.cardId === c.parentCardId)?.kind === 'seat')); },
  cited: ({ cards }) => cards.filter((c) => c.kind === 'zone' || c.kind === 'agent').every((c) => typeof c.source === 'string' && c.source.length > 4),
  omega_carded: ({ cards, world }) => { const o = cards.filter((c) => c.kind === 'omega'); const def = OMEGAS.get(world.slug); return def ? o.length === 1 && o[0].omega_id === def.id && o[0].seated_agent === null && o[0].status === def.status : o.length === 0; },
  omega_off_council: ({ cards }) => cards.filter((c) => c.kind === 'omega').every((o) => { const cl = cards.find((c) => c.kind === 'council'); const p = cards.find((c) => c.cardId === o.parentCardId); if (!cl || p?.kind === 'council' || p?.kind === 'seat') return false; return [0, 2].some((i) => Math.abs(o.volum.center[i] - cl.volum.center[i]) >= o.volum.halfExtents[i] + cl.volum.halfExtents[i]); }),
  omega_voice_bound: ({ cards, world }) => cards.filter((c) => c.kind === 'omega').every((o) => !HIVE.get(world.slug) || (o.voice?.lines?.length > 0 && o.voice.lines.every((l) => HIVE.get(world.slug).lines.some((h) => h.id === l.id && h.text === l.text)))),
  agents_bound: ({ cards, world }) => cards.filter((c) => c.kind === 'agent').every((c) => SWARMS.get(world.slug)?.has(c.binding?.swarm) && c.binding.fabricNode === `Agent · ${c.name}`),
  coordinator_bound: ({ cards, world }) => { const c = cards.filter((x) => x.kind === 'coordinator'); const def = COORDS.get(world.slug); return def ? c.length === 1 && c[0].binding.swarm === def.id && c[0].parentCardId === `plaza:${world.slug}` : c.length === 0; },
  advisors_scripted: ({ cards, world }) => { const a = cards.filter((x) => x.kind === 'advisor'); return a.length === ADVISORS.get(world.slug).length && a.every((x) => x.scripted === true && AVATAR_ROLES.includes(x.avatar.role) && x.permissions.operate.every((h) => !h.startsWith('agents'))); },
  avatar_roles_known: ({ cards }) => cards.filter((c) => c.avatar).every((c) => AVATAR_ROLES.includes(c.avatar.role) && c.avatar.model_ref === avatarRef(c.avatar.role)),
  buildings_resolve: ({ cards }) => cards.filter((c) => c.building).every((c) => [c.building.exterior, c.building.interior, c.building.room].filter(Boolean).every((p) => fs.existsSync(path.join(ROOT, p)))),
  council_not_a_zone: ({ cards, world }) => !cards.some((c) => c.kind === 'zone' && c.name === COUNCIL_ZONE) && cards.filter((c) => c.kind === 'council').every((c) => c.permissions.operate.every((h) => !h.startsWith('agents'))) && (!world.zones.some((z) => z.name === COUNCIL_ZONE) || cards.find((c) => c.kind === 'council').source === world.zones.find((z) => z.name === COUNCIL_ZONE).source),
  nothing_invented: ({ cards, world }) => cards.filter((c) => c.kind === 'zone').every((c) => world.zones.some((z) => z.name === c.name && z.source === c.source)) && cards.filter((c) => c.kind === 'agent').every((c) => world.agents.some((g) => g.name === c.name && g.source === c.source)),
  every_spec_entry_carded: ({ cards, world }) => world.zones.every((z) => cards.some((c) => (c.kind === 'zone' || c.kind === 'council') && c.name === z.name)) && world.agents.every((g) => cards.some((c) => c.kind === 'agent' && c.name === g.name)),
  rp1_names_and_bounds: ({ plan }) => plan.nodes.every((n) => /^[\x20-\x7e]+$/.test(n.displayName) && n.displayName.length <= RP1_NAME_BYTES && n.bound?.d3Max?.length === 3 && n.bound.d3Max.every((v) => v > 0)),
  resource_url_fits: ({ plan }) => plan.nodes.every((n) => !n.resource || Buffer.byteLength(n.resource.sReference) < RESOURCE_LIMIT),
  glb_parses: ({ glb }) => { try { readGlb(glb); return true; } catch { return false; } },
  glb_card_tree_matches: ({ glb, cards }) => {
    let doc; try { doc = readGlb(glb); } catch { return false; }
    const parent = new Map(); doc.nodes.forEach((n, i) => (n.children ?? []).forEach((ch) => parent.set(ch, i)));
    const keyed = doc.nodes.map((n, i) => ({ i, id: n.extras?.cardId })).filter((x) => x.id);
    if (keyed.length !== cards.length) return false;
    const root = doc.nodes[doc.scenes[doc.scene].nodes[0]];
    if (root.extras?.sourceCoordinatesImported !== false || root.extras?.externalGeometryImported !== false) return false;
    return keyed.every(({ i, id }) => { const want = cards.find((c) => c.cardId === id)?.parentCardId ?? null; let p = parent.get(i); while (p != null && !doc.nodes[p].extras?.cardId) p = parent.get(p); return (p == null ? null : doc.nodes[p].extras.cardId) === want; });
  },
  glb_primitives_tagged: ({ glb, blockout }) => { let doc; try { doc = readGlb(glb); } catch { return false; } const ids = new Set(doc.nodes.map((n) => n.extras?.worldforgePrimitiveId).filter(Boolean)); return blockout.primitives.every((p) => ids.has(p.primitiveId)); },
};

export function runEvals(ctx) {
  const results = Object.fromEntries(Object.entries(EVALS).map(([k, f]) => { let ok; try { ok = !!f(ctx); } catch { ok = false; } return [k, ok]; }));
  return { results, failed: Object.keys(results).filter((k) => !results[k]) };
}

// Six deliberately broken worlds; each must fail exactly its own check, or the suite is strict, not discriminating.
export function brokenCases(base) {
  const clone = (x) => structuredClone(x);
  const mk = (mut) => { const b = { world: base.world, cards: clone(base.cards), blockout: clone(base.blockout), gaps: [] }; mut(b); const glb = blockoutToGlb(b); return { ...b, glb, plan: mountPlan(b, sha256(glb), 'x') }; };
  return {
    agents_hold_no_reserved_right: mk((b) => { b.cards.find((c) => c.kind === 'agent').permissions.transfer.push('agents:zone'); }),
    three_human_seats: mk((b) => { b.cards.find((c) => c.kind === 'seat').seated = 'agent:somebody'; }),
    nothing_invented: mk((b) => { b.cards.find((c) => c.kind === 'zone').source = 'invented: not in the spec'; }),
    reserved_actions_verbatim: mk((b) => { b.cards[0].reserved_for_humans.pop(); }),
    council_not_a_zone: mk((b) => { b.cards.find((c) => c.kind === 'council').permissions.operate.push('agents:zone'); }),
    omega_off_council: mk((b) => { const o = b.cards.find((c) => c.kind === 'omega'); o.parentCardId = b.cards.find((c) => c.kind === 'council').cardId; }),
  };
}

// -------------------------------------------------------------------------------------------- main ----
function main() {
  const outputs = new Map();             // relative path -> Buffer
  const put = (rel, data) => outputs.set(rel, Buffer.isBuffer(data) ? data : Buffer.from(data));
  const cube = writeGlb([{ name: 'WF_Shared_Unit_Cube', mat: 'zone-hall', extras: { role: 'shared-generic-unit-cube' } }], 'WorldForge Shared Unit Cube', ['zone-hall']);
  const cubeHash = sha256(cube);
  put('assets/unit-cube.glb', cube);

  const sourceHash = sourceDigest();
  const rows = [];
  let failures = 0;

  for (const w of INDEX.worlds) {
    const built = buildWorld(w);
    const glb = blockoutToGlb(built);
    const glbHash = sha256(glb);
    const plan = mountPlan(built, glbHash, cubeHash);
    const ev = runEvals({ ...built, glb, plan });
    failures += ev.failed.length;
    const cardsDoc = { schemaVersion: 'smartcitix-master-cards/0.1', world: w.slug, owner: PBC.name, umbrella: PBC.umbrella, rights: RIGHTS, principle: 'Agents operate; people govern.', cards: built.cards, gaps: built.gaps };
    const files = { 'cards.json': stable(cardsDoc), 'blockout.generated.json': stable(built.blockout), [`${w.slug}.glb`]: glb, 'sneeze-mount-plan.json': stable(plan) };
    for (const [f, d] of Object.entries(files)) put(`${w.slug}/${f}`, d);
    const manifest = {
      schemaVersion: 'worldforge-sneeze-mount-package/0.1', world: w.slug, sourceHash,
      files: Object.fromEntries(Object.entries(files).map(([f, d]) => [f, sha256(Buffer.isBuffer(d) ? d : Buffer.from(d))])),
      assets: { 'unit-cube.glb': cubeHash },
      counts: { cards: built.cards.length, zones: w.zones.length, agents: w.agents.length, primitives: built.blockout.primitives.length, roads: built.blockout.roads.length, planNodes: plan.nodes.length, resourceNodes: plan.nodes.filter((n) => n.resource).length },
      evals: ev.results,
      gates: { '1.1 generated core': 'done', '1.2 GLB parsed + card tree verified (JavaScript)': ev.failed.length ? 'failed' : 'done', '1.2n native fastgltf load': 'open: Sneeze not checked out here', '1.3 SOM mount plan': 'prepared-not-mounted', '1.4 rendered frame': 'open' },
    };
    put(`${w.slug}/manifest.json`, stable(manifest));
    rows.push({ slug: w.slug, name: w.name, status: w.status, anchored: !!w.anchor?.lat, omega: !!OMEGAS.get(w.slug), ...manifest.counts, glbBytes: glb.length, failed: ev.failed, gaps: built.gaps.length });
  }

  // The suite must discriminate: each broken case fails exactly its own check.
  const base = buildWorld(INDEX.worlds.find((w) => w.slug === 'locator-x') ?? INDEX.worlds[0]);
  const broken = Object.entries(brokenCases(base)).map(([want, ctx]) => { const { failed } = runEvals(ctx); return { want, failed, ok: failed.length === 1 && failed[0] === want }; });
  failures += broken.filter((b) => !b.ok).length;

  const index = {
    schemaVersion: 'worldforge-index/0.1', umbrella: PBC.umbrella, owner: PBC.name, sourceHash, assetUrl: ASSET_URL,
    totals: { worlds: rows.length, cards: rows.reduce((a, r) => a + r.cards, 0), primitives: rows.reduce((a, r) => a + r.primitives, 0), evals: rows.length * Object.keys(EVALS).length, failed: rows.reduce((a, r) => a + r.failed.length, 0), anchored: rows.filter((r) => r.anchored).length },
    broken, worlds: rows,
  };
  put('index.json', stable(index));

  if (CHECK) {
    const stale = [...outputs].filter(([rel, d]) => { const p = path.join(OUT, rel); return !fs.existsSync(p) || !fs.readFileSync(p).equals(d); }).map(([rel]) => rel);
    const failed = rows.reduce((a, r) => a + r.failed.length, 0) + broken.filter((b) => !b.ok).length;
    console.log(stale.length ? `WORLDFORGE STALE: ${stale.length} files behind their sources (first: ${stale[0]})` : `WORLDFORGE current: ${rows.length} worlds, ${rows.reduce((a, r) => a + r.cards, 0)} cards, ${rows.length * Object.keys(EVALS).length} evals, ${failed} failing`);
    process.exit(stale.length || failures ? 1 : 0);
  }
  for (const [rel, d] of outputs) { const p = path.join(OUT, rel); fs.mkdirSync(path.dirname(p), { recursive: true }); fs.writeFileSync(p, d); }
  const t = index.totals;
  console.log(`WORLDFORGE ${failures ? 'RED' : 'GREEN'}: ${t.worlds} worlds, ${t.cards} master cards, ${t.primitives} primitives, ${t.evals} evals (${t.failed} failed), broken cases ${broken.filter((b) => b.ok).length}/${broken.length} discriminated, ${t.anchored} anchored in RP1`);
  for (const r of rows.filter((r) => r.failed.length)) console.log(`  ${r.slug}: ${r.failed.join(', ')}`);
  for (const b of broken.filter((b) => !b.ok)) console.log(`  broken case ${b.want} failed [${b.failed.join(', ')}]`);
  process.exit(failures ? 1 : 0);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
