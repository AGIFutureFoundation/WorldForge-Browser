#!/usr/bin/env node
// worldforge/native/mount_plan_conformance.mjs
//
// Checks every worldforge/out/<slug>/sneeze-mount-plan.json against the constraints verified in
// worldforge/native/RMCOBJECT_MAPPING.md. The constants are baked in below with header citations, so this
// script needs no Sneeze clone. It is deterministic: plans in worldforge/out/index.json order, nodes in
// plan order, no timestamps.
//
//   node worldforge/native/mount_plan_conformance.mjs                 writes worldforge/native/conformance-report.json
//   node worldforge/native/mount_plan_conformance.mjs --check         writes nothing; exit 1 if the report on disk is
//                                                                     stale or any violation exists
//   node worldforge/native/mount_plan_conformance.mjs --route=json    count the MSF "Data" route's limits instead
//
// Routes (see RMCOBJECT_MAPPING.md section 5):
//   native: CONTAINER::Node_Root / Node_Open with a MAP_OBJECT built from the decoded POD
//           (rmcobject_decoder.cpp). This is the route the plan names, and the default.
//   json:   MSF "Data" -> NODE_MAP_DATA -> CONTAINER::Branch_Add -> SNEEZE::MOCelestial_FromJson. Same rules, plus
//           the byte-copy name limits of RmcObject.cpp at this commit.
// The last line of output is always: "sneeze conformance: <plans> plans, <nodes> nodes, <violations> violations".
// Nothing here mounts or renders anything.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const REPORT = 'worldforge/native/conformance-report.json';
const CHECK = process.argv.includes('--check');
const ROUTE_ARG = process.argv.find((a) => a.startsWith('--route='));
const ROUTE = ROUTE_ARG ? ROUTE_ARG.slice('--route='.length) : 'native';
if (!['native', 'json'].includes(ROUTE)) {
  console.log(`sneeze conformance: unknown route '${ROUTE}' (use native or json)`);
  process.exit(1);
}

// ---- Verified sources ------------------------------------------------------------------------------------
export const VERIFIED = {
  sneeze: { url: 'https://github.com/MetaversalCorp/Sneeze', commit: '0008d08bc46546a29a93b447f3b173202358b69a' },
  map: { url: 'https://github.com/MetaversalCorp/Map', commit: '0e6d26ac34f4627baf86c333062a3981a6c40742' },
  rmap: { url: 'https://github.com/MetaversalCorp/RMAP', commit: '0fd7efba6febda9dc97a9f629732a380ef7f2dc7' },
};

// ---- Verified constants ----------------------------------------------------------------------------------
export const LIMITS = {
  nameUnitsField: { value: 48, cite: 'Map/include/Map/Map_Object.h:28 (uint16_t wsName[48])' },
  nameUnitsMax: {
    value: 47,
    cite: 'every engine writer that clamps keeps a NUL: Map/src/Map_Object.cpp:142 via RMAP/RMAP/src/Utils.cpp:192-202 (nLength - 1), Sneeze/src/deps/wasm/HostFunctions.cpp:1009-1013, Sneeze/src/context/scene/Scene.md:299-304. The only reader, Sneeze/src/context/scene/Node.cpp:715-717, stops at NUL or 48, so 47 is the round-trip limit, not a crash limit',
  },
  nameBmpOnly: { value: true, cite: 'Sneeze/src/context/scene/Node.cpp:713-735 (NODE::Name decodes BMP UTF-16 only)' },
  nameJsonBytesMax: {
    value: 47,
    cite: 'Sneeze/src/context/scene/RmcObject.cpp:136-145,172 (copies bytes one-per-unit with limit sizeof(wsName)-1 = 95, which overruns wsName[48] past 48 bytes)',
  },
  nameJsonAsciiOnly: { value: true, cite: 'Sneeze/src/context/scene/RmcObject.cpp:141-143 (static_cast<uint16_t>(s[i]) per byte, no UTF-8 decode)' },
  referenceBytesField: { value: 128, cite: 'Map/include/Map/Map_Object.h:48 (char sReference[128])' },
  referenceBytesMax: { value: 127, cite: 'Sneeze/src/context/scene/RmcObject.cpp:126-134,190 (copies nMax - 1); Node.cpp:155,208 read it as a C string' },
  referenceNotAction: { value: 'action:', cite: 'Sneeze/src/context/scene/Node.cpp:207 (an "action:" reference is never fetched)' },
  referenceMapServiceBytes: { value: 64, cite: 'Map/src/pch.h:48 MVO_SIZE_RMREFERENCE, Map/src/Source_SB_Object.h:86-91 (map-service route only; advisory here)' },
  classes: {
    value: {
      MAP_OBJECT_ROOT: 70, MAP_OBJECT_CELESTIAL: 71, MAP_OBJECT_TERRESTRIAL: 72, MAP_OBJECT_PHYSICAL: 73, MAP_OBJECT_PANEL: 74, MAP_OBJECT_LIGHT: 75,
      MAP_OBJECT_CLASS_ROOT: 70, MAP_OBJECT_CLASS_CELESTIAL: 71, MAP_OBJECT_CLASS_TERRESTRIAL: 72, MAP_OBJECT_CLASS_PHYSICAL: 73, MAP_OBJECT_CLASS_PANEL: 74, MAP_OBJECT_CLASS_LIGHT: 75,
    },
    cite: 'Map/include/Map/Map_Object.h:16-24 (enum MAP_OBJECT_CLASS); derived-type spellings from Sneeze/src/context/scene/Scene.md:364-371; Map/src/Map_Object.cpp:98-113 returns nullptr for any other value',
  },
  quaternion: {
    value: { order: 'x,y,z,w', tolerance: 1e-6 },
    cite: 'Map/include/Map/Map_Object.h:54,159-165; Map/src/Map_Object.cpp:185-192; Sneeze/src/sneeze/control/Compositor.cpp:231-249 (matrix built from q without normalising)',
  },
  scaleNonZero: { value: true, cite: 'Sneeze/src/context/scene/RmcObject.h:25-28 (a zero-scale ancestor collapses every descendant)' },
  parentBeforeChild: {
    value: true,
    cite: 'Sneeze/src/context/Container.cpp:297-312 (Node_Open needs the parent handle, found via Node_Find), 280-295 (Node_Root once per fabric), 409-489 (Branch_Add: first node is the root)',
  },
  upAxis: { value: 'Z', cite: 'Sneeze/src/context/viewport/GltfMesh.cpp:1827-1830, Sneeze/src/sneeze/control/Compositor.cpp:1125-1126' },
};

// ---- Helpers ---------------------------------------------------------------------------------------------
const read = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const finite = (a, n) => Array.isArray(a) && a.length === n && a.every((x) => typeof x === 'number' && Number.isFinite(x));
const utf8Bytes = (s) => Buffer.byteLength(s, 'utf8');
const hasAstralOrLoneSurrogate = (s) => {
  for (let i = 0; i < s.length; i++) {
    const c = s.charCodeAt(i);
    if (c >= 0xd800 && c <= 0xdfff) return true; // UTF-16 surrogate: non-BMP pair or a lone surrogate
  }
  return false;
};

// Where an over-long name came from in worldforge/build.mjs (read-only here). The umbrella is read from worlds/PBC.json,
// the same registry build.mjs reads, so the split is derived from the plans and not written by hand.
const UMBRELLA_TAIL = (() => {
  const p = path.join(ROOT, 'worlds/PBC.json');
  const u = fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, 'utf8')).umbrella : null;
  return typeof u === 'string' && u ? ` · ${u}` : null;
})();
const NAME_ORIGINS = {
  umbrellaSuffix: 'worldforge/build.mjs:94 nodeName(): "<label> · <PBC.umbrella>" budgeted to NAME_LIMIT = 48 (:37); clamping to 47 drops the last letter of the umbrella',
  primitiveIdTail: 'worldforge/build.mjs:388 mountPlan(): displayName = primitiveId.slice(-NAME_LIMIT); clamping to 47 drops the last character of the path (".../pad" -> ".../pa")',
  other: 'neither of the above',
};
const nameOrigin = (n) => {
  const name = n.displayName;
  if (n.nativeClass === 'MAP_OBJECT_PHYSICAL' && typeof n.cardId === 'string' && n.cardId.endsWith(name)) return 'primitiveIdTail';
  if (UMBRELLA_TAIL && name.endsWith(UMBRELLA_TAIL)) return 'umbrellaSuffix';
  return 'other';
};

function checkPlan(slug, plan) {
  const native = []; // violations that apply to the native route (and so to the json route too)
  const jsonOnly = []; // extra violations for the json route
  const advisories = { frameConversion: 0, mountParentRootFabric: 0, noNativeSlot: 0, noBound: 0, mapServiceReference: 0, classNotACppType: 0 };
  const origins = { umbrellaSuffix: 0, primitiveIdTail: 0, other: 0 }; // name-utf16-units only
  const originKinds = { umbrellaSuffix: {}, primitiveIdTail: {}, other: {} }; // same, by extras.kind
  const jsonBytes = { exactly48NoNul: 0, over48IntoType: 0 }; // json-name-bytes only
  const v = (list, cardId, rule, detail) => list.push({ plan: slug, cardId, rule, detail });

  const nodes = Array.isArray(plan.nodes) ? plan.nodes : [];
  if (!Array.isArray(plan.nodes)) v(native, null, 'plan-nodes', 'plan has no nodes array');

  const up = plan.coordinateFrame?.up;
  if (up === 'Y') advisories.frameConversion = 1;
  else if (up !== 'Z') v(native, null, 'frame', `coordinateFrame.up is ${JSON.stringify(up)}; must be "Y" (converted) or "Z"`);
  if (typeof plan.mountParent === 'string' && plan.mountParent.startsWith('SCENE::Fabric_Root()')) advisories.mountParentRootFabric = 1;

  const seen = new Set();
  let roots = 0;
  nodes.forEach((n, i) => {
    const id = typeof n.cardId === 'string' ? n.cardId : null;
    if (!id) v(native, null, 'card-id', `node ${i} has no cardId`);
    else if (seen.has(id)) v(native, id, 'card-id', 'duplicate cardId');

    // Parents first; one root; root first and equal to rootCardId.
    if (n.parentCardId === null) {
      roots++;
      if (i !== 0) v(native, id, 'parent-before-child', 'root is not the first node');
      if (plan.rootCardId && id !== plan.rootCardId) v(native, id, 'parent-before-child', `root is not rootCardId ${plan.rootCardId}`);
    } else if (typeof n.parentCardId !== 'string' || !seen.has(n.parentCardId)) {
      v(native, id, 'parent-before-child', `parent ${JSON.stringify(n.parentCardId)} is not an earlier node`);
    }
    if (id) seen.add(id);

    // Name: native POD limits.
    const name = n.displayName;
    if (typeof name !== 'string' || name.length === 0) v(native, id, 'name-missing', 'displayName missing or empty');
    else {
      if (name.length > LIMITS.nameUnitsMax.value) {
        v(native, id, 'name-utf16-units', `${name.length} UTF-16 units > 47 (wsName[48] keeps a NUL); "${name}"`);
        const o = nameOrigin(n);
        const kind = typeof n.extras?.kind === 'string' ? n.extras.kind : '(no kind)';
        origins[o]++;
        originKinds[o][kind] = (originKinds[o][kind] ?? 0) + 1;
      }
      if (hasAstralOrLoneSurrogate(name)) v(native, id, 'name-bmp', 'contains a non-BMP code point or lone surrogate');
      if (name.includes('\u0000')) v(native, id, 'name-nul', 'contains U+0000');
      // Name: json route (byte copy at RmcObject.cpp:136-145).
      if (/[^\x00-\x7f]/.test(name)) v(jsonOnly, id, 'json-name-ascii', `non-ASCII bytes are copied one-per-unit; "${name}"`);
      if (utf8Bytes(name) > LIMITS.nameJsonBytesMax.value) {
        v(jsonOnly, id, 'json-name-bytes', `${utf8Bytes(name)} UTF-8 bytes > 47; past 48 the copy overruns wsName into Type`);
        jsonBytes[utf8Bytes(name) === 48 ? 'exactly48NoNul' : 'over48IntoType']++;
      }
    }

    // Class discriminator.
    const cls = LIMITS.classes.value[n.nativeClass];
    if (cls === undefined) v(native, id, 'class', `nativeClass ${JSON.stringify(n.nativeClass)} is not a MAP_OBJECT_CLASS`);
    else if (cls === 73 || cls === 74) advisories.classNotACppType++; // PHYSICAL / PANEL build a base MAP_OBJECT

    // Resource.
    if (n.resource !== null && n.resource !== undefined) {
      const ref = n.resource?.sReference;
      if (typeof ref !== 'string' || ref.length === 0) v(native, id, 'resource-reference', 'resource without a non-empty sReference');
      else {
        if (utf8Bytes(ref) > LIMITS.referenceBytesMax.value) v(native, id, 'resource-reference', `${utf8Bytes(ref)} bytes > 127`);
        if (ref.startsWith(LIMITS.referenceNotAction.value)) v(native, id, 'resource-reference', '"action:" references are never fetched');
        if (utf8Bytes(ref) > LIMITS.referenceMapServiceBytes.value - 1) advisories.mapServiceReference++;
      }
    }

    // Transform.
    const t = n.transform ?? {};
    if (!finite(t.translation, 3)) v(native, id, 'transform-translation', 'translation must be 3 finite numbers');
    if (!finite(t.rotation, 4)) v(native, id, 'quaternion', 'rotation must be 4 finite numbers [x,y,z,w]');
    else {
      const len = Math.hypot(...t.rotation);
      if (Math.abs(len - 1) > LIMITS.quaternion.value.tolerance) v(native, id, 'quaternion', `|q| = ${len} (must be unit length within 1e-6)`);
    }
    if (!finite(t.scale, 3)) v(native, id, 'transform-scale', 'scale must be 3 finite numbers');
    else if (t.scale.some((s) => s === 0)) v(native, id, 'transform-scale', 'scale has a zero axis');

    advisories.noNativeSlot++; // cardId / parentCardId / extras have no field in MAP_OBJECT_POD
    if (!n.volum) advisories.noBound++; // Bound.d3Max stays zero
  });
  if (roots !== 1) v(native, null, 'parent-before-child', `${roots} roots (need exactly 1)`);

  return { nodes: nodes.length, native, jsonOnly, advisories, origins, originKinds, jsonBytes };
}

// ---- Self-test: deliberately broken variants must each trip exactly their own rule ---------------------------
// Base: the first plan with names clamped to 47 units, so it starts at zero violations on both routes.
function selftest(slug, plan) {
  const clone = (o) => JSON.parse(JSON.stringify(o));
  const base = clone(plan);
  for (const n of base.nodes) n.displayName = n.displayName.slice(0, 47).replace(/[^\x00-\x7f]/g, '-');
  const rulesOf = (p) => {
    const r = checkPlan(slug, p);
    return { native: new Set(r.native.map((x) => x.rule)), json: new Set(r.jsonOnly.map((x) => x.rule)) };
  };
  const b = rulesOf(base);
  const failures = [];
  if (b.native.size || b.json.size) failures.push(`clean base not clean: ${[...b.native, ...b.json].join(',')}`);
  const resIx = base.nodes.findIndex((n) => n.resource);
  const childIx = base.nodes.findIndex((n, i) => i > 1 && base.nodes.findIndex((m) => m.cardId === n.parentCardId) > 0);
  const cases = [
    ['name-utf16-units', 'native', (p) => { p.nodes[1].displayName = 'x'.repeat(48); }],
    ['name-bmp', 'native', (p) => { p.nodes[1].displayName = 'Plaza \u{1F310}'; }],
    ['class', 'native', (p) => { p.nodes[1].nativeClass = 'MAP_OBJECT_PLAZA'; }],
    ['resource-reference', 'native', (p) => { p.nodes[resIx].resource.sReference = 'http://127.0.0.1:8789/' + 'a'.repeat(106) + '.glb'; }],
    ['resource-reference', 'native', (p) => { p.nodes[resIx].resource.sReference = 'action:open'; }],
    ['quaternion', 'native', (p) => { p.nodes[1].transform.rotation = [0, 0, 0, 2]; }],
    ['transform-scale', 'native', (p) => { p.nodes[1].transform.scale = [1, 0, 1]; }],
    ['parent-before-child', 'native', (p) => { const [c] = p.nodes.splice(childIx, 1); p.nodes.splice(1, 0, c); }],
    ['parent-before-child', 'native', (p) => { p.nodes[2].parentCardId = null; }],
    ['card-id', 'native', (p) => { p.nodes.push({ ...clone(p.nodes[p.nodes.length - 1]) }); }],
    ['frame', 'native', (p) => { p.coordinateFrame.up = 'X'; }],
    ['json-name-ascii', 'json', (p) => { p.nodes[1].displayName = 'Plaza · Powered by AGI Corp'; }],
    ['json-name-bytes', 'json', (p) => { p.nodes[1].displayName = 'x'.repeat(48 - 2) + 'é'; }], // 47 units, 48 bytes
  ];
  for (const [rule, route, mutate] of cases) {
    const p = clone(base);
    mutate(p);
    const r = rulesOf(p);
    // A native case must raise exactly its own rule on the native route. Its test name may also trip a json-route
    // rule, which is the json route's business. A json case must leave the native route clean; the 48-byte name
    // necessarily contains a non-ASCII character, so json-name-ascii is allowed alongside json-name-bytes.
    const got = route === 'native' ? r.native : new Set([...r.json].filter((x) => !(rule === 'json-name-bytes' && x === 'json-name-ascii')));
    const ok = got.size === 1 && got.has(rule) && (route === 'native' || r.native.size === 0);
    if (!ok) failures.push(`${rule}: got native[${[...r.native]}] json[${[...r.json]}]`);
  }
  return { cases: cases.length, failures };
}

// ---- Run -------------------------------------------------------------------------------------------------
const index = read('worldforge/out/index.json');
const slugs = (index.worlds ?? []).map((w) => w.slug);
const perPlan = [];
const totals = { plans: 0, nodes: 0 };
const nativeAll = [];
const jsonAll = [];
const adv = { frameConversion: 0, mountParentRootFabric: 0, noNativeSlot: 0, noBound: 0, mapServiceReference: 0, classNotACppType: 0 };
const origins = { umbrellaSuffix: 0, primitiveIdTail: 0, other: 0 };
const originKinds = { umbrellaSuffix: {}, primitiveIdTail: {}, other: {} };
const jsonBytes = { exactly48NoNul: 0, over48IntoType: 0 };

for (const slug of slugs) {
  const rel = `worldforge/out/${slug}/sneeze-mount-plan.json`;
  if (!fs.existsSync(path.join(ROOT, rel))) {
    nativeAll.push({ plan: slug, cardId: null, rule: 'plan-missing', detail: rel });
    continue;
  }
  const r = checkPlan(slug, read(rel));
  totals.plans++;
  totals.nodes += r.nodes;
  nativeAll.push(...r.native);
  jsonAll.push(...r.native, ...r.jsonOnly);
  for (const k of Object.keys(adv)) adv[k] += r.advisories[k];
  for (const k of Object.keys(origins)) origins[k] += r.origins[k];
  for (const k of Object.keys(originKinds)) for (const [kind, c] of Object.entries(r.originKinds[k])) originKinds[k][kind] = (originKinds[k][kind] ?? 0) + c;
  for (const k of Object.keys(jsonBytes)) jsonBytes[k] += r.jsonBytes[k];
  perPlan.push({ slug, nodes: r.nodes, nativeViolations: r.native.length, jsonRouteViolations: r.native.length + r.jsonOnly.length });
}

// json-route violations: count nodes once per rule (a node can break both json-name rules).
const byRule = (list) => list.reduce((m, x) => ((m[x.rule] = (m[x.rule] ?? 0) + 1), m), {});
const sortObj = (o) => Object.fromEntries(Object.entries(o).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0)));
const jsonNodes = new Set(jsonAll.map((x) => `${x.plan}\u0000${x.cardId}`)).size;

const report = {
  schemaVersion: 'worldforge-sneeze-conformance/0.1',
  generator: 'worldforge/native/mount_plan_conformance.mjs',
  status: 'static-check-only-nothing-mounted-or-rendered',
  verifiedAgainst: VERIFIED,
  limits: LIMITS,
  totals: {
    plans: totals.plans,
    nodes: totals.nodes,
    native: {
      violations: nativeAll.length,
      byRule: sortObj(byRule(nativeAll)),
      nameUnitsByOrigin: Object.fromEntries(Object.entries(origins).map(([k, nodes]) => [k, { nodes, byKind: sortObj(originKinds[k]), source: NAME_ORIGINS[k] }])),
    },
    json: {
      violations: jsonAll.length,
      nodesAffected: jsonNodes,
      byRule: sortObj(byRule(jsonAll)),
      nameBytesSplit: {
        exactly48NoNul: { nodes: jsonBytes.exactly48NoNul, note: 'fills wsName[48] with no NUL; NODE::Name stops at 48 (Node.cpp:715-717), so no overrun' },
        over48IntoType: { nodes: jsonBytes.over48IntoType, note: 'bytes 49 on land at POD offset 96 (Type) and beyond (RmcObject.cpp:141-143, 172; U1)' },
      },
    },
  },
  advisories: {
    frameConversion: { plans: adv.frameConversion, note: 'plan declares up = "Y"; the decoder applies Rx(+90) per node (GltfMesh.cpp:1827-1830)' },
    mountParentRootFabric: {
      plans: adv.mountParentRootFabric,
      note: 'mountParent names the scene root fabric. Node_Root needs a fabric without a root (Container.cpp:290), so the plan root would be Node_Open-ed under the root container\'s ROOT node (as Scene.cpp:205-221 does for the primary attach node), owned by no MSF. The content route is a fabric of its own: RMCOBJECT_MAPPING.md section 5.',
    },
    noNativeSlot: { nodes: adv.noNativeSlot, note: 'cardId, parentCardId and extras have no MAP_OBJECT_POD field (Map_Object.h:124-134); the mounting code keeps cardId -> handle' },
    noBound: { nodes: adv.noBound, note: 'plan carries no volume, so Bound.d3Max stays zero (Compositor.cpp:647-653 use it for framing)' },
    mapServiceReference: { nodes: adv.mapServiceReference, note: 'references over 63 bytes would not fit the map-service STRING(64) (map-managed route only)' },
    classNotACppType: { nodes: adv.classNotACppType, note: 'MAP_OBJECT_PHYSICAL is not a C++ class in Map; class 73 builds a base MAP_OBJECT (Map_Object.cpp:107). The discriminator is valid.' },
  },
  perPlan,
  violations: {
    native: nativeAll,
    jsonOnlyExamples: jsonAll.filter((x) => x.rule.startsWith('json-')).slice(0, 12),
  },
};

const text = JSON.stringify(report, null, 1) + '\n';
const diskPath = path.join(ROOT, REPORT);
const onDisk = fs.existsSync(diskPath) ? fs.readFileSync(diskPath, 'utf8') : null;
const counted = ROUTE === 'native' ? nativeAll.length : jsonAll.length;

if (CHECK) {
  if (onDisk !== text) console.error(`${REPORT} is stale or missing; run without --check to regenerate`);
} else {
  if (onDisk !== text) fs.writeFileSync(diskPath, text);
  const rules = ROUTE === 'native' ? report.totals.native.byRule : report.totals.json.byRule;
  for (const [rule, count] of Object.entries(rules)) console.log(`  ${ROUTE} ${rule}: ${count}`);
  for (const [k, o] of Object.entries(report.totals.native.nameUnitsByOrigin)) if (o.nodes) console.log(`    name-utf16-units from ${k}: ${o.nodes}`);
  if (ROUTE === 'json') for (const [k, o] of Object.entries(report.totals.json.nameBytesSplit)) console.log(`    json-name-bytes ${k}: ${o.nodes}`);
  console.log(`  other route (${ROUTE === 'native' ? 'json' : 'native'}): ${ROUTE === 'native' ? jsonAll.length : nativeAll.length} violations`);
  for (const [k, a] of Object.entries(report.advisories)) console.log(`  advisory ${k}: ${a.plans ?? a.nodes}`);
  console.log(`  report: ${REPORT}`);
}

const st = slugs.length ? selftest(slugs[0], read(`worldforge/out/${slugs[0]}/sneeze-mount-plan.json`)) : { cases: 0, failures: ['no plans'] };
if (st.failures.length) for (const f of st.failures) console.error(`selftest: ${f}`);
if (!CHECK) console.log(`  selftest: ${st.cases - st.failures.length}/${st.cases} broken variants caught by exactly their own rule`);

console.log(`sneeze conformance: ${totals.plans} plans, ${totals.nodes} nodes, ${counted} violations`);
if (st.failures.length) process.exit(1);
if (CHECK && (onDisk !== text || counted > 0 || totals.plans !== slugs.length)) process.exit(1);
