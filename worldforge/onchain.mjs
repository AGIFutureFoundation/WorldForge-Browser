// WorldForge onchain export: every GLEWME Master Card as draft ERC-721 metadata JSON, committed to by sha256 Merkle
// roots (one per world, one network root over the world roots). Onchain-READY only: nothing here touches a chain.
//   node worldforge/onchain.mjs           # writes worldforge/out/onchain/ and worldforge/onchain/README.md, exit 1 on any failing eval
//   node worldforge/onchain.mjs --check   # rebuilds in memory; exit 1 if disk differs or any eval fails (writes nothing, one line)
//
// Inputs (read only): worldforge/out/<slug>/cards.json for every world in worldforge/out/index.json (written by
// worldforge/build.mjs) and worlds/PBC.json (owner, umbrella, the six actions reserved for humans, seat count).
// Outputs:
//   worldforge/out/onchain/<slug>/collection.json       '<World> Master Cards': tagline, umbrella, owner, standard,
//                                                        counts, Merkle root, governance note, not-deployed block
//   worldforge/out/onchain/<slug>/tokens/<tokenId>.json  one OpenSea-compatible ERC-721 metadata document per card
//   worldforge/out/onchain/<slug>/proofs.json            tokenId -> leaf and sibling hashes up to the world root
//   worldforge/out/onchain/index.json                    network root over the world roots, per-world proofs, evals
//   worldforge/onchain/README.md                         generated from the template at the bottom of this file
//
// What is and is not claimed. No chain, contract, deployment, wallet, key, address, transaction, price or sale exists;
// nothing is minted. Minting or transferring a card would itself be a human-reserved decision for the 2-of-3 Steward
// Council, and no agent holds it. The roots are commitments a future contract could anchor; none does today.
//
// Rules (also written into every collection.json and index.json):
//   tokenId  = first 16 hex chars of sha256(cardId), lowercase, no prefix (64 bits)
//   leaf     = sha256(canonical JSON of the token metadata); token files are written in exactly that form, so
//              sha256(file bytes) == leaf. Canonical JSON = keys sorted by UTF-16 code unit, no whitespace, no newline.
//   node     = sha256(min(a, b) || max(a, b)) over the raw 32-byte values (sorted pairs: proofs need no side flags);
//              an unpaired node moves up a level unchanged. Leaves are ordered by tokenId; the network tree's leaves
//              are the world roots ordered by slug. Hash is sha256 throughout (keccak-free).
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');
const OUT_REL = 'worldforge/out/onchain';
const README_REL = 'worldforge/onchain/README.md';
const CHECK = process.argv.includes('--check');
const readRel = (rel) => fs.readFileSync(path.join(ROOT, rel));
const readJson = (rel) => JSON.parse(readRel(rel).toString('utf8'));

const PBC = readJson('worlds/PBC.json');
export const STANDARD = 'ERC-721 metadata JSON (draft, not deployed)';
export const RIGHTS = ['view', 'enter', 'build', 'operate', 'delegate', 'transfer', 'govern'];
const HUMAN_ONLY_RIGHTS = ['delegate', 'transfer', 'govern'];      // as in worldforge/build.mjs
const QUORUM_HOLDER = 'steward-quorum';                             // the cards' holder token for the 2-of-3 quorum
const COUNCIL = 'Steward Council';
const QUORUM = '2-of-3';
const HELD = `held for steward quorum (${QUORUM})`;
const MINT_HELD = `${HELD}; not done`;
const BASE_WORLD = 'locator-x';                                     // the world the broken fixtures start from
const IMAGE_NOTE = 'No hosted image yet: no card image has been rendered or hosted, so image is null rather than a placeholder URL.';
const NOT_DEPLOYED = 'Nothing is deployed or minted. No chain, contract, wallet, key, address or transaction exists for this collection, and nothing is offered for sale (no price, royalty or fee recipient).';
const TOKEN_ID_RULE = 'first 16 hex characters of sha256(cardId), lowercase, no prefix (64 bits)';
const MERKLE_RULES = {
  hash: 'sha256 (keccak-free)',
  leaf: 'sha256 of the token metadata as canonical JSON (keys sorted by UTF-16 code unit, no whitespace, no trailing newline); each token file is written in exactly that form, so sha256(file bytes) is its leaf',
  order: 'leaves sorted by tokenId ascending',
  node: 'sha256(min(a, b) || max(a, b)) over the raw 32-byte values (sorted pairs, so proofs carry no left/right flags)',
  odd: 'an unpaired node moves up a level unchanged',
  proof: 'h = leaf; for each sibling s in order: h = node(h, s); valid when h equals the root',
};
const cap = (s) => s[0].toUpperCase() + s.slice(1);
const RIGHT_TRAITS = RIGHTS.map(cap);

// ------------------------------------------------------------------------------- canonical JSON + hashes ----
export function canonical(v) {
  if (v === null || typeof v === 'boolean' || typeof v === 'string') return JSON.stringify(v);
  if (typeof v === 'number') { if (!Number.isFinite(v)) throw new Error('non-finite number'); return JSON.stringify(v); }
  if (Array.isArray(v)) return `[${v.map(canonical).join(',')}]`;
  if (typeof v === 'object') return `{${Object.keys(v).filter((k) => v[k] !== undefined).sort().map((k) => `${JSON.stringify(k)}:${canonical(v[k])}`).join(',')}}`;
  throw new Error(`not JSON: ${typeof v}`);
}
export const sha256 = (d) => createHash('sha256').update(d).digest('hex');
export const tokenIdOf = (cardId) => sha256(cardId).slice(0, 16);
const HASH_RE = /^[0-9a-f]{64}$/;
const byStr = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

// --------------------------------------------------------------------------------------------- Merkle ----
/** Sorted-pair node: equal-length lowercase hex compares like the bytes it encodes. */
export const hashPair = (a, b) => { const [x, y] = a < b ? [a, b] : [b, a]; return sha256(Buffer.concat([Buffer.from(x, 'hex'), Buffer.from(y, 'hex')])); };
export function merkleLevels(leaves) {
  if (!leaves.length) throw new Error('empty Merkle tree');
  const levels = [leaves.slice()];
  while (levels.at(-1).length > 1) {
    const cur = levels.at(-1), next = [];
    for (let i = 0; i < cur.length; i += 2) next.push(i + 1 < cur.length ? hashPair(cur[i], cur[i + 1]) : cur[i]);
    levels.push(next);
  }
  return levels;
}
export function proofOf(levels, index) {
  const proof = [];
  for (let l = 0, i = index; l < levels.length - 1; l++, i >>= 1) if ((i ^ 1) < levels[l].length) proof.push(levels[l][i ^ 1]);
  return proof;
}
export const verifyProof = (leaf, proof, root) => HASH_RE.test(leaf) && Array.isArray(proof) && proof.every((s) => HASH_RE.test(s)) && proof.reduce(hashPair, leaf) === root;

// ------------------------------------------------------------------------------------------ token metadata ----
const sentence = (s) => { const t = String(s ?? '').trim(); if (!t) return ''; const u = t[0].toUpperCase() + t.slice(1); return /[.!?]$/.test(u) ? u : `${u}.`; };
const holders = (list) => (list ?? []).map((h) => (h === QUORUM_HOLDER ? HELD : h)).join(', ');
const A = (trait_type, value, display_type) => (display_type ? { display_type, trait_type, value } : { trait_type, value });

function reservedOf(c) {
  const actions = c.reserved_for_humans.map((x) => x.action);
  const held = [...new Set(c.reserved_for_humans.map((x) => canonical(x.held_for)))];
  return held.length === 1 ? { actions, held_for: c.reserved_for_humans[0].held_for } : { actions, held_for: null, per_action: c.reserved_for_humans };
}

/** Name: the card's own name; the plaza's is untruncated the way build.mjs composes it; else its display name minus the umbrella. */
function tokenName(c, world) {
  if (c.name) return c.name;
  if (c.kind === 'plaza') return `${world.name} Plaza`;
  return c.displayName.replace(` · ${c.umbrella}`, '');
}

/** Description: only the card's own fields, then one line on what the token is and is not. */
function bodyOf(c, parent) {
  switch (c.kind) {
    case 'world': return sentence(c.tagline);
    case 'plaza': case 'gate': case 'council': case 'zone': return sentence(c.purpose);
    case 'coordinator': case 'agent': return sentence(c.role);
    case 'advisor': return [sentence(`${c.name}: ${c.manages}`), sentence(c.note)].filter(Boolean).join(' ');
    case 'seat': return sentence(`${c.seat_type} seat on the ${parent?.name ?? COUNCIL}; ${c.seated === null ? 'no one is seated' : `seated: ${c.seated}`}`);
    case 'omega': return [sentence(`${c.name}: ${c.status}`), c.persona?.temperament ? sentence(`persona: ${c.persona.temperament}`) : ''].filter(Boolean).join(' ');
    default: return '';
  }
}

function tokenMeta(c, { slug, doc, world, byId }) {
  const id = tokenIdOf(c.cardId);
  const attributes = [
    A('Kind', c.kind), A('World', world.name), A('Owner', c.owner), A('Umbrella', c.umbrella),
    A('Parent', c.parentCardId ?? 'root'),
    A('Volum centre', c.volum.center.join(',')), A('Volum half-extents', c.volum.halfExtents.join(',')),
    ...RIGHTS.map((r) => A(cap(r), r === 'operate' ? (c.permissions.operate ?? []).join(', ') : holders(c.permissions[r]))),
    A('Minted', `no; minting is ${HELD}`),
    A('Reserved for humans', c.reserved_for_humans.length, 'number'),
  ];
  if (c.kind === 'world') attributes.push(A('Status', c.status), A('Management', c.management_style), A('RP1 anchor', c.anchor?.lat != null ? 'set' : 'not yet'), A('Omega Steward', c.omega_steward?.status ?? 'none'));
  if (c.kind === 'coordinator' || c.kind === 'agent') attributes.push(A('Swarm', c.binding?.swarm ?? 'none'));
  if (c.kind === 'advisor') attributes.push(A('Guide', c.scripted === true ? 'scripted, not AI' : 'unknown'));
  if (c.kind === 'seat') attributes.push(A('Seat', `${c.seat_type}, ${c.seated === null ? 'empty' : 'seated'}`));
  if (c.kind === 'omega') {
    const lines = c.voice?.lines ?? [];
    attributes.push(A('Status', c.status), A('Seated agent', c.seated_agent ?? 'none'), A('Voice', !c.voice ? 'none' : lines.some((l) => /synthetic/i.test(l.text)) ? 'synthetic; its greeting says so' : 'synthetic'));
  }
  if (c.avatar) attributes.push(A('Avatar role', c.avatar.role));
  if (c.kind === 'zone' || c.kind === 'council') attributes.push(A('Building', c.building?.kind ?? 'none'));

  const properties = {
    token_id: id, cardId: c.cardId, kind: c.kind, world: slug, parentCardId: c.parentCardId,
    source: c.source, reserved_for_humans: reservedOf(c), permissions: c.permissions, volum: c.volum,
    card_file: `worldforge/out/${slug}/cards.json`, card_schema: doc.schemaVersion, minted: false,
  };
  if (c.may_never) properties.may_never = c.may_never;
  if (c.binding) properties.binding = c.binding;
  if (c.avatar) properties.avatar_model = c.avatar.model_ref;
  if ('scripted' in c) properties.scripted = c.scripted;
  if (c.kind === 'world' || c.kind === 'omega') properties.status = c.status;
  if (c.kind === 'omega') Object.assign(properties, { omega_id: c.omega_id, seated_agent: c.seated_agent });
  if (c.kind === 'seat') Object.assign(properties, { seat_type: c.seat_type, seated: c.seated });

  const tail = `${world.name} Master Card, owned by ${c.owner} (${c.umbrella}). Draft metadata: not minted, not deployed.`;
  return {
    name: tokenName(c, world),
    description: [bodyOf(c, byId.get(c.parentCardId)), tail].filter(Boolean).join(' '),
    external_url: null, image: null, image_note: IMAGE_NOTE, attributes, properties,
  };
}

function tokensFor(slug, doc) {
  const world = doc.cards.find((c) => c.kind === 'world');
  if (!world) throw new Error(`${slug}: cards.json has no world card`);
  const byId = new Map(doc.cards.map((c) => [c.cardId, c]));
  return doc.cards.map((c) => ({ id: tokenIdOf(c.cardId), meta: tokenMeta(c, { slug, doc, world, byId }) }));
}

// ------------------------------------------------------------------------------------------- assemble ----
/** One world's files (paths relative to worldforge/out/onchain/) from its token metadata. */
function assemble({ slug, doc, bytes, metas }) {
  const sorted = [...metas].sort((a, b) => byStr(a.id, b.id));
  const leaves = sorted.map((t) => sha256(canonical(t.meta)));
  const levels = merkleLevels(leaves);
  const root = levels.at(-1)[0];
  const world = doc.cards.find((c) => c.kind === 'world');
  const seats = doc.cards.filter((c) => c.kind === 'seat');
  const omega = doc.cards.find((c) => c.kind === 'omega');
  const reserved = reservedOf(world);
  const held = reserved.held_for ?? {};
  const texts = new Map();
  sorted.forEach((t) => texts.set(`${slug}/tokens/${t.id}.json`, canonical(t.meta)));
  texts.set(`${slug}/proofs.json`, canonical({
    schema: 'smartcitix-onchain-proofs/0.1', world: slug, merkle_root: root, rules: MERKLE_RULES,
    leaves: Object.fromEntries(sorted.map((t, i) => [t.id, leaves[i]])),
    proofs: Object.fromEntries(sorted.map((t, i) => [t.id, proofOf(levels, i)])),
  }));
  texts.set(`${slug}/collection.json`, canonical({
    schema: 'smartcitix-onchain-collection/0.1',
    name: `${world.name} Master Cards`, description: world.tagline, image: null, external_link: null, image_note: IMAGE_NOTE,
    umbrella: doc.umbrella, owner: doc.owner, standard: STANDARD, world: slug, status: world.status,
    card_count: doc.cards.length, token_count: sorted.length, merkle_root: root, merkle: MERKLE_RULES, token_id_rule: TOKEN_ID_RULE,
    tokens: 'tokens/<tokenId>.json', proofs: 'proofs.json',
    governance: {
      note: `Transfers and governance are reserved for the ${held.quorum} ${held.holder}; minting or transferring any Master Card is a human-reserved action. No agent holds these rights.`,
      principle: doc.principle, transfer: holders(world.permissions.transfer), govern: holders(world.permissions.govern), mint: MINT_HELD,
      reserved_for_humans: reserved,
      steward_seats: { defined: seats.length, seated: seats.filter((s) => s.seated !== null).length },
      omega_steward: omega?.status ?? null,
    },
    deployment: { status: 'not deployed', chain: null, contract: null, minted: 0, transactions: 0, note: NOT_DEPLOYED },
    source: { cards: `worldforge/out/${slug}/cards.json`, cards_schema: doc.schemaVersion, cards_sha256: sha256(bytes) },
  }));
  return { slug, doc, cards: doc.cards, cardsBytes: bytes, texts, root, name: world.name };
}

/** The network: index.json over the world roots (sorted by slug), and the README that reports it. */
function assembleNetwork(worlds, again) {
  const ws = [...worlds].sort((a, b) => byStr(a.slug, b.slug));
  const roots = ws.map((w) => JSON.parse(w.texts.get(`${w.slug}/collection.json`)).merkle_root);
  const levels = merkleLevels(roots);
  const networkRoot = levels.at(-1)[0];
  const tokenCount = (w) => [...w.texts.keys()].filter((k) => k.includes('/tokens/')).length;
  const kinds = {};
  for (const w of ws) for (const c of w.cards) kinds[c.kind] = (kinds[c.kind] ?? 0) + 1;
  const indexDoc = {
    schema: 'smartcitix-onchain-index/0.1', umbrella: PBC.umbrella, owner: PBC.name, standard: STANDARD,
    status: 'not deployed, not minted', deployment: { chain: null, contract: null, minted: 0, transactions: 0, note: NOT_DEPLOYED },
    token_id_rule: TOKEN_ID_RULE, merkle: MERKLE_RULES,
    network: { root: networkRoot, leaves: 'world merkle roots, ordered by slug', worlds: ws.length },
    network_root: networkRoot,
    totals: { worlds: ws.length, cards: ws.reduce((a, w) => a + w.cards.length, 0), tokens: ws.reduce((a, w) => a + tokenCount(w), 0), by_kind: kinds },
    governance: `Transfers and governance are reserved for the ${QUORUM} ${COUNCIL}; minting or transferring any Master Card is a human-reserved action. No agent holds these rights.`,
    source: 'worldforge/out/<slug>/cards.json (worldforge/build.mjs), worlds/PBC.json',
    worlds: ws.map((w, i) => ({ slug: w.slug, name: w.name, cards: w.cards.length, tokens: tokenCount(w), merkle_root: roots[i], network_proof: proofOf(levels, i), collection: `${w.slug}/collection.json` })),
  };
  const all = ws.flatMap((w) => w.cards);
  const facts = {
    seats: all.filter((c) => c.kind === 'seat').length, seated: all.filter((c) => c.kind === 'seat' && c.seated !== null).length,
    omegas: all.filter((c) => c.kind === 'omega').length, omegasUnseated: all.filter((c) => c.kind === 'omega' && c.status === 'defined, not seated' && c.seated_agent === null).length,
    omegaGreetings: all.filter((c) => c.kind === 'omega' && (c.voice?.lines ?? []).some((l) => /synthetic/i.test(l.text))).length,
    advisors: all.filter((c) => c.kind === 'advisor').length, advisorsScripted: all.filter((c) => c.kind === 'advisor' && c.scripted === true).length,
  };
  const indexText = canonical(indexDoc);
  const readme = readmeText(indexDoc, facts);
  const texts = new Map();
  for (const w of ws) for (const [rel, t] of w.texts) texts.set(`${OUT_REL}/${rel}`, t);
  texts.set(`${OUT_REL}/index.json`, indexText);
  texts.set(README_REL, readme);
  return { worlds: ws, indexDoc, indexText, readme, networkRoot, texts, again: again ?? texts };
}

function loadInputs() {
  const wf = readJson('worldforge/out/index.json');
  return wf.worlds.map((w) => w.slug).sort(byStr).map((slug) => {
    const rel = `worldforge/out/${slug}/cards.json`;
    if (!fs.existsSync(path.join(ROOT, rel))) throw new Error(`${rel} missing: run node worldforge/build.mjs first`);
    const bytes = readRel(rel);
    return { slug, doc: JSON.parse(bytes.toString('utf8')), bytes };
  });
}
const buildWorld = (x) => assemble({ ...x, metas: tokensFor(x.slug, x.doc) });
const buildExport = (inputs, again) => assembleNetwork(inputs.map(buildWorld), again);

// ---------------------------------------------------------------------------------------------- evals ----
const cache = new WeakMap();
/** Parsed view of one world's texts, so the evals check exactly what would be written. */
function view(ctx) {
  if (cache.has(ctx)) return cache.get(ctx);
  const v = { tokens: [] };
  for (const [rel, text] of ctx.texts) {
    const j = JSON.parse(text);
    if (rel === `${ctx.slug}/collection.json`) v.collection = j;
    else if (rel === `${ctx.slug}/proofs.json`) v.proofs = j;
    else v.tokens.push({ file: rel.slice(`${ctx.slug}/tokens/`.length, -'.json'.length), meta: j });
  }
  v.tokens.sort((a, b) => byStr(a.file, b.file));
  v.leaves = v.tokens.map((t) => sha256(canonical(t.meta)));
  v.levels = v.tokens.length ? merkleLevels(v.leaves) : [[]];
  cache.set(ctx, v);
  return v;
}
const attrMap = (meta) => new Map(meta.attributes.map((x) => [x.trait_type, x.value]));

const ADDRESS_RE = /0x[0-9a-fA-F]{40}(?![0-9a-fA-F])/;
const KEY_PATTERNS = [
  /-----BEGIN [A-Z ]*PRIVATE KEY-----/,               // PEM private key
  /\b[xtyz]prv[1-9A-HJ-NP-Za-km-z]{100,}/,            // BIP32 extended private key
  /\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b/,             // WIF private key
  /\bsk-[A-Za-z0-9_-]{20,}/, /\bsk_live_[A-Za-z0-9]{10,}/, /\bAKIA[0-9A-Z]{16}\b/, /\bgh[pousr]_[A-Za-z0-9]{30,}/, /\bxox[abprs]-[A-Za-z0-9-]{10,}/,
];
const EMAIL_RE = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/;
export const addressShaped = (text) => ADDRESS_RE.test(text);
/** Key-shaped: a known secret pattern, or any run of 32+ hex characters that is not one of the export's own derived sha256 hashes. */
export function keyShaped(text, derived) {
  if (KEY_PATTERNS.some((re) => re.test(text))) return true;
  for (const m of text.matchAll(/[0-9a-fA-F]{32,}/g)) {
    const pre = text.slice(Math.max(0, m.index - 2), m.index);
    if (pre === '0x' && m[0].length === 40) continue;  // address-shaped: reported by no_address_shapes, not twice
    if (pre === '0x' || m[0].length !== 64 || !derived.has(m[0])) return true;
  }
  return false;
}
const worldDerived = (ctx) => new Set([...view(ctx).levels.flat(), sha256(ctx.cardsBytes)]);
const isCanonical = (text) => { try { return text === canonical(JSON.parse(text)); } catch { return false; } };

export const WORLD_EVALS = {
  one_token_per_card: (ctx) => {
    const { tokens, collection } = view(ctx);
    const want = new Map(ctx.cards.map((c) => [tokenIdOf(c.cardId), c.cardId]));
    return want.size === ctx.cards.length && tokens.length === ctx.cards.length && new Set(tokens.map((t) => t.file)).size === tokens.length
      && tokens.every((t) => /^[0-9a-f]{16}$/.test(t.file) && want.get(t.file) === t.meta.properties.cardId && t.meta.properties.token_id === t.file)
      && collection.card_count === ctx.cards.length && collection.token_count === tokens.length;
  },
  proofs_verify: (ctx) => {
    const { tokens, collection, proofs, leaves, levels } = view(ctx);
    const root = levels.at(-1)[0];
    return collection.merkle_root === root && proofs.merkle_root === root && Object.keys(proofs.proofs).length === tokens.length && Object.keys(proofs.leaves).length === tokens.length
      && tokens.every((t, i) => proofs.leaves[t.file] === leaves[i] && verifyProof(leaves[i], proofs.proofs[t.file], root));
  },
  no_agent_holds_reserved_right: (ctx) => view(ctx).tokens.every(({ meta }) => {
    const a = attrMap(meta), p = meta.properties;
    if ([...HUMAN_ONLY_RIGHTS.map(cap), 'Minted'].some((t) => typeof a.get(t) !== 'string' || /agent/i.test(a.get(t)))) return false;
    if (HUMAN_ONLY_RIGHTS.some((r) => (p.permissions?.[r] ?? []).some((h) => /^agent/i.test(h)))) return false;
    if (meta.attributes.some((x) => PBC.reserved_for_humans.some((act) => String(x.trait_type).toLowerCase().includes(act)))) return false;
    return !p.may_never || PBC.reserved_for_humans.every((act) => p.may_never.includes(act));
  }),
  reserved_actions_verbatim: (ctx) => {
    const ok = (r) => r?.actions?.join() === PBC.reserved_for_humans.join() && r.held_for?.holder === COUNCIL && r.held_for?.quorum === QUORUM && r.held_for?.seats === PBC.steward_seats;
    const { tokens, collection } = view(ctx);
    return ok(collection.governance?.reserved_for_humans) && tokens.every((t) => ok(t.meta.properties.reserved_for_humans));
  },
  transfer_held_for_quorum: (ctx) => {
    const { tokens, collection } = view(ctx);
    const g = collection.governance ?? {};
    return g.transfer === HELD && g.govern === HELD && g.mint === MINT_HELD && g.note?.includes(`${QUORUM} ${COUNCIL}`) && g.note.includes('human-reserved')
      && tokens.every((t) => { const a = attrMap(t.meta); return a.get('Transfer') === HELD && a.get('Govern') === HELD; });
  },
  faithful_to_cards: (ctx) => {
    const { tokens, collection } = view(ctx);
    const byId = new Map(ctx.cards.map((c) => [c.cardId, c]));
    return collection.source?.cards_sha256 === sha256(ctx.cardsBytes) && tokens.every(({ meta }) => {
      const c = byId.get(meta.properties.cardId);
      if (!c) return true;                                   // missing or extra tokens are one_token_per_card's finding
      const a = attrMap(meta), p = meta.properties;
      return a.get('Kind') === c.kind && p.kind === c.kind && a.get('Owner') === c.owner && a.get('Parent') === (c.parentCardId ?? 'root') && p.parentCardId === c.parentCardId
        && a.get('Volum centre') === c.volum.center.join(',') && a.get('Volum half-extents') === c.volum.halfExtents.join(',') && a.get('Operate') === c.permissions.operate.join(', ')
        && typeof c.source === 'string' && c.source.length > 4 && p.source === c.source && canonical(p.permissions) === canonical(c.permissions) && canonical(p.volum) === canonical(c.volum);
    });
  },
  metadata_shape: (ctx) => {
    const { tokens, collection } = view(ctx);
    const world = ctx.cards.find((c) => c.kind === 'world');
    const KEYS = 'attributes,description,external_url,image,image_note,name,properties';
    const REQUIRED = ['Kind', 'World', 'Owner', 'Umbrella', 'Parent', 'Volum centre', 'Volum half-extents', ...RIGHT_TRAITS, 'Minted', 'Reserved for humans'];
    return collection.name === `${world.name} Master Cards` && collection.description === world.tagline && collection.owner === PBC.name && collection.umbrella === PBC.umbrella
      && collection.standard === STANDARD && collection.image === null && collection.external_link === null
      && tokens.every(({ meta }) => Object.keys(meta).sort().join() === KEYS && typeof meta.name === 'string' && meta.name.length > 0 && !meta.name.includes('…') && !meta.name.includes(PBC.umbrella)
        && typeof meta.description === 'string' && meta.description.length > 20 && meta.external_url === null && meta.image === null && /no hosted image/i.test(meta.image_note)
        && Array.isArray(meta.attributes) && new Set(meta.attributes.map((x) => x.trait_type)).size === meta.attributes.length && REQUIRED.every((t) => meta.attributes.some((x) => x.trait_type === t))
        && meta.attributes.every((x) => Object.keys(x).every((k) => ['display_type', 'trait_type', 'value'].includes(k)) && typeof x.trait_type === 'string' && (typeof x.value === 'string' ? x.value.length > 0 : Number.isFinite(x.value))));
  },
  not_deployed_not_minted: (ctx) => {
    const { tokens, collection } = view(ctx);
    const d = collection.deployment ?? {};
    return d.status === 'not deployed' && d.chain === null && d.contract === null && d.minted === 0 && d.transactions === 0 && d.note === NOT_DEPLOYED
      && tokens.every((t) => t.meta.properties.minted === false && /^no;/.test(attrMap(t.meta).get('Minted') ?? ''));
  },
  honest_status: (ctx) => view(ctx).tokens.every(({ meta }) => {
    const a = attrMap(meta), p = meta.properties;
    if (p.kind === 'omega') return p.status === 'defined, not seated' && a.get('Status') === p.status && p.seated_agent === null && a.get('Seated agent') === 'none' && /^(synthetic|none)/.test(a.get('Voice') ?? '');
    if (p.kind === 'seat') return p.seat_type === 'human' && p.seated === null && a.get('Seat') === 'human, empty';
    if (p.kind === 'advisor') return p.scripted === true && a.get('Guide') === 'scripted, not AI';
    if (p.kind === 'world') return ['defined, not seated', 'none'].includes(a.get('Omega Steward'));
    return true;
  }),
  no_address_shapes: (ctx) => [...ctx.texts.values()].every((t) => !addressShaped(t)),
  no_key_shapes: (ctx) => { const derived = worldDerived(ctx); return [...ctx.texts.values()].every((t) => !keyShaped(t, derived)); },
  no_email_shapes: (ctx) => [...ctx.texts.values()].every((t) => !EMAIL_RE.test(t)),
  canonical_json: (ctx) => [...ctx.texts.values()].every(isCanonical),
};

export const NETWORK_EVALS = {
  token_ids_unique_network: (net) => {
    const ids = net.worlds.flatMap((w) => [...w.texts.keys()].filter((k) => k.includes('/tokens/')).map((k) => k.slice(k.lastIndexOf('/') + 1)));
    return ids.length > 0 && new Set(ids).size === ids.length;
  },
  network_root_verifies: (net) => {
    const index = JSON.parse(net.indexText);
    const roots = net.worlds.map((w) => JSON.parse(w.texts.get(`${w.slug}/collection.json`)).merkle_root);
    const root = merkleLevels(roots).at(-1)[0];
    const tokens = net.worlds.reduce((a, w) => a + [...w.texts.keys()].filter((k) => k.includes('/tokens/')).length, 0);
    return index.network_root === root && index.network?.root === root && index.worlds.length === net.worlds.length && index.totals?.tokens === tokens
      && index.worlds.every((row, i) => row.slug === net.worlds[i].slug && row.merkle_root === roots[i] && verifyProof(roots[i], row.network_proof, root));
  },
  index_and_readme_clean: (net) => {
    const roots = net.worlds.map((w) => JSON.parse(w.texts.get(`${w.slug}/collection.json`)).merkle_root);
    const derived = new Set(merkleLevels(roots).flat());
    return isCanonical(net.indexText) && [net.indexText, net.readme].every((t) => !addressShaped(t) && !keyShaped(t, derived) && !EMAIL_RE.test(t));
  },
  deterministic: (net) => {
    const a = [...net.texts.keys()].sort(byStr), b = [...net.again.keys()].sort(byStr);
    return a.join('\n') === b.join('\n') && a.every((k) => net.texts.get(k) === net.again.get(k));
  },
};

function runEvals(evals, ctx) {
  const results = Object.fromEntries(Object.entries(evals).map(([k, f]) => { let ok; try { ok = !!f(ctx); } catch { ok = false; } return [k, ok]; }));
  return { results, failed: Object.keys(results).filter((k) => !results[k]) };
}

// ------------------------------------------------------------------------------------- broken fixtures ----
// Each fixture breaks one thing; it must fail exactly its own check, or the suite is strict, not discriminating.
const metasOf = (w) => view(w).tokens.map((t) => ({ id: t.file, meta: structuredClone(t.meta) }));
const reassemble = (w, metas) => assemble({ slug: w.slug, doc: w.doc, bytes: w.cardsBytes, metas });
/** Rebuild a world from a mutated copy of its source cards (the export must refuse what a bad card would carry). */
function fromCards(w, mut) { const doc = structuredClone(w.doc); mut(doc.cards); return buildWorld({ slug: w.slug, doc, bytes: w.cardsBytes }); }
function withText(w, rel, edit) { const texts = new Map(w.texts); texts.set(`${w.slug}/${rel}`, edit(texts.get(`${w.slug}/${rel}`))); return { ...w, texts }; }
const editJson = (mut) => (text) => { const j = JSON.parse(text); mut(j); return canonical(j); };

export function worldFixtures(w) {
  const agent = (cards) => cards.find((c) => c.kind === 'agent');
  const firstAgentId = tokenIdOf(agent(w.cards).cardId);
  const notAKey = sha256('fixture: a 64-hex string that is not one of the export hashes');
  return {
    one_token_per_card: reassemble(w, metasOf(w).filter((t) => t.id !== firstAgentId)),
    proofs_verify: withText(w, 'proofs.json', editJson((j) => { const id = Object.keys(j.proofs)[0]; j.proofs[id][0] = j.leaves[id]; })),
    no_agent_holds_reserved_right: fromCards(w, (cards) => { agent(cards).permissions.delegate.push('agents:zone'); }),
    reserved_actions_verbatim: fromCards(w, (cards) => { agent(cards).reserved_for_humans.pop(); }),
    transfer_held_for_quorum: fromCards(w, (cards) => { agent(cards).permissions.transfer = ['stewards']; }),
    faithful_to_cards: reassemble(w, metasOf(w).map((t) => { if (t.id === firstAgentId) t.meta.attributes.find((x) => x.trait_type === 'Volum centre').value = '0,0,0'; return t; })),
    metadata_shape: reassemble(w, metasOf(w).map((t) => { if (t.id === firstAgentId) t.meta.image = 'https://example.invalid/card.png'; return t; })),
    not_deployed_not_minted: withText(w, 'collection.json', editJson((j) => { j.deployment.minted = 1; })),
    honest_status: fromCards(w, (cards) => { const o = cards.find((c) => c.kind === 'omega'); o.status = 'seated'; }),
    no_address_shapes: fromCards(w, (cards) => { agent(cards).role += ` Settles to 0x${'ab'.repeat(20)}.`; }),
    no_key_shapes: fromCards(w, (cards) => { agent(cards).role += ` Key ${notAKey}.`; }),
    no_email_shapes: fromCards(w, (cards) => { agent(cards).role += ` Contact steward${'@'}example.org.`; }),
    canonical_json: withText(w, `tokens/${firstAgentId}.json`, (text) => JSON.stringify(JSON.parse(text), null, 2)),
  };
}

export function networkFixtures(net) {
  const [a, b] = net.worlds;
  const dup = view(a).tokens[0];
  const again = new Map(net.texts);
  const k = [...again.keys()].find((x) => x.includes('/tokens/'));
  again.set(k, `${again.get(k)} `);
  const badRoot = { ...net, indexText: editJson((j) => { j.network_root = JSON.parse(a.texts.get(`${a.slug}/collection.json`)).merkle_root; })(net.indexText) };
  return {
    token_ids_unique_network: assembleNetwork(net.worlds.map((w) => (w === b ? reassemble(b, [...metasOf(b), { id: dup.file, meta: structuredClone(dup.meta) }]) : w))),
    network_root_verifies: { ...badRoot, texts: net.texts, again: net.texts },
    index_and_readme_clean: { ...net, readme: `${net.readme}\nSettlement: 0x${'cd'.repeat(20)}\n` },
    deterministic: { ...net, again },
  };
}

// ---------------------------------------------------------------------------------------------- README ----
function readmeText(index, f) {
  const t = index.totals;
  const of = (n, m) => (n === m ? `all ${m}` : `${n} of ${m}`);
  const perWorld = Object.keys(WORLD_EVALS).length, network = Object.keys(NETWORK_EVALS).length;
  const fixtures = perWorld + network;
  const kinds = Object.entries(t.by_kind).sort((x, y) => y[1] - x[1] || byStr(x[0], y[0])).map(([k, n]) => `${n} ${k}`).join(', ');
  return `# Onchain-ready export of the GLEWME Master Cards

<!-- Generated by worldforge/onchain.mjs (edit the template there); --check fails if this file is out of date. -->

**Nothing is deployed or minted.** This is an export, not a launch. No chain has been chosen for these cards and
no smart contract has been written or deployed for them. No wallet, key, address or transaction exists for this
export. Nothing is offered for sale: there is no price, royalty or fee recipient. Every collection says so in its \`deployment\` block
(\`status: "not deployed"\`, \`chain: null\`, \`contract: null\`, \`minted: 0\`, \`transactions: 0\`).

\`worldforge/onchain.mjs\` turns every GLEWME Master Card in \`worldforge/out/<slug>/cards.json\` into ERC-721
metadata JSON, the shape OpenSea-style marketplaces read. It then commits to that metadata with sha256 Merkle
roots: one root per world, plus one network root over the ${t.worlds} world roots.

\`\`\`bash
node worldforge/onchain.mjs           # writes worldforge/out/onchain/ and this README, exit 1 on any failing eval
node worldforge/onchain.mjs --check   # rebuilds in memory; exit 1 if disk differs or any eval fails
\`\`\`

The export is built from \`cards.json\`, which \`node worldforge/build.mjs\` writes. Whenever a card changes,
the export is stale until this script is re-run, and \`--check\` reports it.

## Who decides

Agents operate; people govern. Minting a Master Card would itself be a human-reserved decision for the
${QUORUM} ${COUNCIL}, and so would transferring one. No agent holds either right:

- every token's \`Transfer\` and \`Govern\` traits read \`${HELD}\`, and \`Delegate\` belongs to stewards;
- every token's \`Minted\` trait reads \`no; minting is ${HELD}\`;
- the PBC's six reserved actions (${PBC.reserved_for_humans.map((x) => `\`${x}\``).join(', ')}) are copied verbatim
  from \`worlds/PBC.json\` into each token's \`properties.reserved_for_humans\`, held for the ${COUNCIL} at a ${QUORUM} quorum;
- an eval fails if any trait or permission gives an agent one of these rights.

${f.seated === 0
    ? `Each council has ${PBC.steward_seats} seats, and ${of(f.seats, f.seats)} seat cards are empty today (each seat token says \`human, empty\`). So the human quorum that a mint would need does not exist yet.`
    : `${f.seated} of ${f.seats} steward seats are seated; the rest are empty.`}
${cap(of(f.omegasUnseated, f.omegas))} Omega Steward tokens say they are *defined, not seated*. Their \`Voice\` trait says the voice is synthetic, and in
${of(f.omegaGreetings, f.omegas)} the omega's own greeting says so too. ${cap(of(f.advisorsScripted, f.advisors))} advisor tokens say they are scripted guides, not AI.

## What is in \`worldforge/out/onchain/\`

| Path | What it is |
|---|---|
| \`index.json\` | The network root over the world roots. For each world: its root, its proof up to the network root, and counts. Also the eval results and the broken-fixture results. |
| \`<slug>/collection.json\` | \`<World> Master Cards\`, with the description taken from the world's tagline. Also: the umbrella (${PBC.umbrella}), the owner (${PBC.name}), the standard \`${STANDARD}\`, card and token counts, the world's \`merkle_root\`, the governance note, the not-deployed block, and the sha256 of the \`cards.json\` it was built from. |
| \`<slug>/tokens/<tokenId>.json\` | One ERC-721 metadata document per card. |
| \`<slug>/proofs.json\` | For every token, its leaf hash and the sibling hashes up to the world root. |

**Token metadata.** Each token has a \`name\` and a \`description\`, both built only from fields already in \`cards.json\`,
plus \`external_url: null\` and \`image: null\`. An \`image_note\` explains the null: no card image has been
rendered or hosted yet, so there is nothing to point at.

\`attributes\` holds the traits below:

- Kind, World, Owner, Umbrella;
- Parent (the parent card's id, or \`root\`);
- Volum centre and Volum half-extents, as \`x,y,z\` in metres;
- one trait for each right: View, Enter, Build, Operate (the card's \`permissions.operate\`, joined), Delegate,
  Transfer, Govern;
- Minted, and Reserved for humans (a count);
- per-kind traits: status, swarm, avatar role, seat, guide, voice, building.

\`properties\` holds:

- the \`cardId\`, kind, world and \`parentCardId\`;
- the card's \`source\` citation;
- the reserved actions and who holds them;
- the full permission matrix and the Volum;
- \`may_never\`, the binding and the avatar model path, where the card has them.

**Token IDs.** \`tokenId\` = the ${TOKEN_ID_RULE}. A future contract would read it as a uint256. A token ID depends
only on its card ID, so it stays the same when the card's contents change. What changes is the leaf hash, and
so the root.

## Merkle commitments

- **Hash:** sha256 throughout (keccak-free).
- **Leaf:** the sha256 of the token's canonical JSON (keys sorted, no whitespace, no trailing newline). Each
  token file is written in exactly that form, so \`shasum -a 256 tokens/<tokenId>.json\` prints its leaf.
- **Order:** leaves are sorted by tokenId, ascending.
- **Node:** \`sha256(min(a, b) || max(a, b))\` over the raw 32-byte values. Because pairs are sorted, a proof
  needs no left/right flags. A node without a partner moves up a level unchanged.
- **Roots:** each world root is in that world's \`collection.json\` and \`proofs.json\`. The network root is in
  \`index.json\`. It uses the same tree, built over the world roots ordered by slug, and each world carries its
  \`network_proof\`.

To check one token by hand:

1. Hash its file.
2. Fold in each sibling from \`proofs.json\` in turn, using the sorted-pair rule.
3. Compare the result with the world's \`merkle_root\`.
4. Fold the world's \`network_proof\` into that root and compare with \`network_root\`.

The roots are **commitments**. A future contract could anchor a world root or the network root, then check any
token's metadata against it with its proof. Nothing anchors them today.

A contract author would still have to deal with the following (none of it is done here):

- Leaves are not domain-separated from internal nodes. A verifier must hash the full metadata itself and never
  accept a bare 32-byte leaf.
- The EVM's native hash is keccak256. Checking these proofs on chain needs the sha256 precompile and a sorted-pair
  sha256 verifier.
- Token IDs are 64-bit. The current ${t.tokens} IDs are unique, and an eval checks this on every build.

## Numbers

| | |
|---|---|
| Worlds | ${t.worlds} |
| Tokens (one per card) | ${t.tokens} (${kinds}) |
| Network root | \`${index.network_root}\` |
| Evals | ${perWorld} per world (${perWorld * t.worlds}) + ${network} network-wide = ${perWorld * t.worlds + network} |
| Broken fixtures | ${fixtures}, each of which must fail exactly its own check |

## Evals

Per world:

- \`one_token_per_card\`: exactly one token per card, with tokenId derived from cardId.
- \`proofs_verify\`: every proof verifies against its root.
- \`no_agent_holds_reserved_right\`: no trait or permission gives an agent Delegate, Transfer, Govern, minting or a
  reserved action.
- \`reserved_actions_verbatim\`: the six reserved actions are copied verbatim and held for the ${QUORUM} ${COUNCIL}.
- \`transfer_held_for_quorum\`: Transfer and Govern are held for the quorum, and the collection's governance note
  says so.
- \`faithful_to_cards\`: kind, owner, parent, Volum, operate, permissions and source citation match the card.
- \`metadata_shape\`: the OpenSea-compatible ERC-721 shape, with null image and URL explained.
- \`not_deployed_not_minted\`: the not-deployed block and \`minted: false\` on every token.
- \`honest_status\`: omegas are defined, not seated, with a synthetic voice; seats are human and empty; advisors are
  scripted.
- \`no_address_shapes\`: no \`0x\` + 40 hex anywhere.
- \`no_key_shapes\`: no PEM, extended, WIF or API-key patterns, and every run of 32+ hex characters is one of the
  export's own sha256 hashes.
- \`no_email_shapes\`: no email addresses.
- \`canonical_json\`: every file is byte-identical to its canonical form.

Network-wide:

- \`token_ids_unique_network\`: token IDs are unique across the network.
- \`network_root_verifies\`: the network root and every world's network proof verify.
- \`index_and_readme_clean\`: \`index.json\` and this README are clean, by the same address, key and email checks.
- \`deterministic\`: a second in-memory build is byte-identical.

Each eval has a broken fixture that must fail exactly that check and no other. If one doesn't, the suite isn't
discriminating, and the run fails.

## Not done

- No contract has been written, compiled, audited or deployed, and no chain has been chosen.
- Nothing is minted. No wallet, key, address or transaction exists.
- No images and no external URLs exist. Nothing is pinned to IPFS or any other host.
- No price, sale, royalty or fee recipient exists.
- No legal review has been done of what a token would represent.
- The ${COUNCIL}'s seats are empty, so the human quorum that minting would need has not been seated.
- Owner is a label naming ${PBC.name}. There is no owner address, and \`ownerOf\` has no meaning until a mint
  the stewards approve.
`;
}

// ------------------------------------------------------------------------------------------------ main ----
function listFiles(rel) {
  const abs = path.join(ROOT, rel);
  if (!fs.existsSync(abs)) return [];
  return fs.readdirSync(abs, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? listFiles(`${rel}/${e.name}`) : [`${rel}/${e.name}`]));
}

function main() {
  const inputs = loadInputs();
  const net = buildExport(inputs, buildExport(inputs).texts);

  const rows = net.worlds.map((w) => ({ slug: w.slug, ...runEvals(WORLD_EVALS, w) }));
  const netEv = runEvals(NETWORK_EVALS, net);
  const base = net.worlds.find((w) => w.slug === BASE_WORLD) ?? net.worlds[0];
  const broken = [
    ...Object.entries(worldFixtures(base)).map(([want, ctx]) => ({ want, failed: runEvals(WORLD_EVALS, ctx).failed })),
    ...Object.entries(networkFixtures(net)).map(([want, ctx]) => ({ want, failed: runEvals(NETWORK_EVALS, ctx).failed })),
  ].map((b) => ({ ...b, ok: b.failed.length === 1 && b.failed[0] === b.want }));
  const missingFixture = [...Object.keys(WORLD_EVALS), ...Object.keys(NETWORK_EVALS)].filter((k) => !broken.some((b) => b.want === k));

  const evalCount = rows.length * Object.keys(WORLD_EVALS).length + Object.keys(NETWORK_EVALS).length;
  const failedEvals = rows.reduce((a, r) => a + r.failed.length, 0) + netEv.failed.length;
  const index = {
    ...net.indexDoc,
    evals: {
      per_world: Object.keys(WORLD_EVALS), network: Object.keys(NETWORK_EVALS), total: evalCount, failed: failedEvals,
      failing: [...rows.flatMap((r) => r.failed.map((f) => `${r.slug}:${f}`)), ...netEv.failed.map((f) => `network:${f}`)],
    },
    broken: { base_world: base.slug, cases: broken, discriminated: broken.filter((b) => b.ok).length },
  };
  const indexText = canonical(index);
  const outputs = new Map(net.texts);
  outputs.set(`${OUT_REL}/index.json`, indexText);
  // The final index adds only eval names, counts and booleans to the one the network evals checked; re-check it anyway.
  const finalClean = NETWORK_EVALS.index_and_readme_clean({ ...net, indexText });
  const failures = failedEvals + broken.filter((b) => !b.ok).length + missingFixture.length + (finalClean ? 0 : 1);

  const strays = listFiles(OUT_REL).filter((rel) => !outputs.has(rel));
  const t = index.totals;
  const root12 = net.networkRoot.slice(0, 12);
  if (CHECK) {
    const stale = [...outputs].filter(([rel, text]) => { const p = path.join(ROOT, rel); return !fs.existsSync(p) || fs.readFileSync(p, 'utf8') !== text; }).map(([rel]) => rel);
    const behind = [...stale, ...strays];
    console.log(behind.length
      ? `onchain export STALE: ${behind.length} files differ from a fresh build (first: ${behind[0]}), ${failures} failing`
      : `onchain export current: ${t.worlds} worlds, ${t.tokens} tokens, network root ${root12}, ${failures} failing`);
    process.exit(behind.length || failures ? 1 : 0);
  }
  let wrote = 0;
  for (const [rel, text] of outputs) {
    const p = path.join(ROOT, rel);
    if (fs.existsSync(p) && fs.readFileSync(p, 'utf8') === text) continue;
    fs.mkdirSync(path.dirname(p), { recursive: true });
    fs.writeFileSync(p, text);
    wrote++;
  }
  for (const rel of strays) fs.rmSync(path.join(ROOT, rel));   // only ever inside worldforge/out/onchain/
  console.log(`ONCHAIN ${failures ? 'RED' : 'GREEN'}: ${t.worlds} worlds, ${t.tokens} tokens, network root ${root12}, ${evalCount} evals (${failedEvals} failed), broken fixtures ${index.broken.discriminated}/${broken.length} discriminated, ${wrote} files written, ${strays.length} stray files removed; nothing deployed or minted`);
  for (const r of rows.filter((r) => r.failed.length)) console.log(`  ${r.slug}: ${r.failed.join(', ')}`);
  if (netEv.failed.length) console.log(`  network: ${netEv.failed.join(', ')}`);
  for (const b of broken.filter((b) => !b.ok)) console.log(`  broken fixture ${b.want} failed [${b.failed.join(', ')}]`);
  for (const k of missingFixture) console.log(`  eval ${k} has no broken fixture`);
  if (!finalClean) console.log('  final index.json failed index_and_readme_clean');
  process.exit(failures ? 1 : 0);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
