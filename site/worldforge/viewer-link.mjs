// viewer-link.mjs — Phase A: one viewer-link reader for the WorldForge slugs
// (STAGED). Pure function: no DOM, no fetch, no window, no localStorage.
// It takes a query string (or a full URL) and the generated WorldForge index
// (worldforge-index.json, 544 slugs) plus an OPTIONAL per-world card list,
// and returns a resolved target — or a clean "not found" result. It never
// crashes and never guesses a fallback.
//
// Contract (see VIEWER_LINK_CONTRACT.md, v1):
//   viewer.html?world=<worldforge-slug>[&card=<card-id>]
// Canonical param names: `world` and `card`. This is a SEPARATE namespace
// from the flagship world ids (M2's deep-link.mjs): a flagship id such as
// `smartciti-holodeck` or `agi-corp-hub` is NOT a valid viewer slug, and
// this reader does not validate flagship ids.
//
// Card resolution: a card id is verified ONLY against a per-world card list
// supplied by the caller (`cardsByWorld`, from worldforge/out/<slug>/cards.json).
//   - Card list supplied for this world + card present + card in the list
//     -> kind 'card', resolved.
//   - Card list supplied for this world + card present + card NOT in the list
//     -> error 'card_not_found' (checked and absent).
//   - NO card list supplied for this world + card present
//     -> error 'card_unverified' (could not check; NOT the same as not found).
//     No card list is staged for any world except the two slugs in
//     viewer-cards-sample.json, so `card_unverified` is the normal outcome
//     for real card links until a cards.json is supplied. The reader never
//     treats an unverified card as found.
//
// How the live viewer differs (viewer.html:445-447, 1582-1583): today it
// silently falls back — an unknown card shows the world card, an unknown
// slug opens index.worlds[0], and no `world` param opens `locator-x`. This
// reader reports the failure precisely instead; the CALLER (viewer wiring)
// decides what to show. The reader itself never substitutes a target.
//
// Slug format (contract v1, verified: all 544 slugs satisfy it):
// /^[a-z0-9][a-z0-9-]*$/. Card format (contract v1, from the card ids the
// viewer itself constructs/looks up — `landmark:<slug>`, `gate:<slug>`,
// `plaza:<slug>`, `coordinator:<slug>`, `<kind>:<slug>/...`):
// /^[a-z0-9][a-z0-9:.\/-]*$/. A value that fails the format is `malformed`.
// An empty value is treated as absent.

export const CANONICAL_PARAMS = ['world', 'card'];
// Other params the viewer itself reads (viewer.html:188-200, 449-450).
// They are viewer state, not link targets: recorded in `ignored`, never
// resolved by this reader. NOTE: viewer `tour=1` is a recording-tour flag,
// NOT a quest id — it is unrelated to M2's `tour=<quest-id>`.
export const VIEWER_STATE_PARAMS = {
  hud: 'viewer state param (hud=0 hides the HUD) — not resolved by this reader',
  tour: 'viewer state param (tour=1 recording tour) — not a quest id, not resolved by this reader',
  labels: 'viewer state param — not resolved by this reader',
  access: 'viewer access param (teleports to an access point) — not resolved by this reader; use card= for a card target',
  inside: 'viewer state param (inside=1 enters a card room) — not resolved by this reader',
};
export const SLUG_PATTERN = /^[a-z0-9][a-z0-9-]*$/;
export const CARD_PATTERN = /^[a-z0-9][a-z0-9:.\/-]*$/;

function isPlainObject(v) {
  return v !== null && typeof v === 'object' && !Array.isArray(v);
}

function extractQuery(input) {
  if (typeof input !== 'string') return '';
  const s = input.trim();
  if (!s) return '';
  // Full URL (has a scheme) -> take its query part.
  if (/^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//.test(s)) {
    try {
      return new URL(s).search.slice(1);
    } catch (e) {
      return s;
    }
  }
  const q = s.indexOf('?');
  return (q >= 0 ? s.slice(q + 1) : s).replace(/^\?/, '');
}

// Normalise the index into a Map<slug, world>. Accepts either the staged
// index object ({ worlds: [...] }) or a bare array of world objects.
function buildIndex(index) {
  const list = Array.isArray(index) ? index : (isPlainObject(index) ? index.worlds : null);
  if (!Array.isArray(list)) return null;
  const worlds = new Map();
  for (const w of list) {
    if (isPlainObject(w) && typeof w.slug === 'string') worlds.set(w.slug, w);
  }
  return worlds;
}

// Normalise the optional per-world card data into Map<slug, Map<cardId, card>>.
// Accepts: null/undefined (no card data), a plain object { slug: [...] },
// or a Map. Each world's list holds card objects ({ cardId, ... }) or bare
// card-id strings. A world absent from the map has NO card data (unverified),
// which is different from a world present with an empty list (every card
// is card_not_found).
function buildCards(cardsByWorld) {
  if (cardsByWorld === null || cardsByWorld === undefined) return new Map();
  const entries = cardsByWorld instanceof Map
    ? [...cardsByWorld.entries()]
    : (isPlainObject(cardsByWorld) ? Object.entries(cardsByWorld) : null);
  if (entries === null) return null;
  const out = new Map();
  for (const [slug, list] of entries) {
    if (!Array.isArray(list)) return null;
    const m = new Map();
    for (const c of list) {
      if (typeof c === 'string') m.set(c, { cardId: c });
      else if (isPlainObject(c) && typeof c.cardId === 'string') m.set(c.cardId, c);
      else return null;
    }
    out.set(slug, m);
  }
  return out;
}

function canonicalUrls(worldSlug, cardId) {
  const base = 'viewer.html?world=' + encodeURIComponent(worldSlug);
  return { viewer: cardId ? base + '&card=' + encodeURIComponent(cardId) : base };
}

// Resolve a viewer link. `input` is a query string ("?world=...&card=...")
// or a full URL; `index` is the parsed worldforge-index.json object (or a
// bare array of world objects); `cardsByWorld` is optional per-world card
// data (see above).
// Returns { ok, kind, world, card, ignored, urls } on success, or
// { ok:false, error, param, requested, world, ignored } on failure. Never
// throws on bad input (a malformed index/cards argument is the only
// programmer error, reported as ok:false, error:'bad_index' / 'bad_cards').
export function resolveViewerLink(input, index, cardsByWorld) {
  const ignored = [];
  const requested = { world: null, card: null };

  const worlds = buildIndex(index);
  if (!worlds) {
    return { ok: false, error: 'bad_index', param: null, requested, world: null, ignored };
  }
  const cards = buildCards(cardsByWorld);
  if (cards === null) {
    return { ok: false, error: 'bad_cards', param: null, requested, world: null, ignored };
  }

  const params = new URLSearchParams(extractQuery(input));

  // Record unknown params and viewer state params as ignored.
  for (const key of new Set(params.keys())) {
    if (CANONICAL_PARAMS.includes(key)) continue;
    const value = params.get(key);
    ignored.push({
      param: key,
      value,
      reason: key in VIEWER_STATE_PARAMS ? VIEWER_STATE_PARAMS[key] : 'unknown parameter — ignored',
    });
  }

  for (const p of CANONICAL_PARAMS) {
    const v = params.get(p);
    if (v !== null && v !== '') requested[p] = v;
  }

  // World is required.
  if (requested.world === null) {
    return { ok: false, error: 'missing_world', param: 'world', requested, world: null, ignored };
  }
  if (!SLUG_PATTERN.test(requested.world)) {
    return { ok: false, error: 'malformed', param: 'world', requested, world: null, ignored };
  }
  const world = worlds.get(requested.world) || null;
  if (!world) {
    return {
      ok: false,
      error: 'world_not_found',
      param: 'world',
      requested,
      world: null,
      ignored,
      known_world_count: worlds.size,
    };
  }

  // Optional card, scoped to this world.
  if (requested.card !== null) {
    if (!CARD_PATTERN.test(requested.card)) {
      return { ok: false, error: 'malformed', param: 'card', requested, world, ignored };
    }
    const worldCards = cards.get(world.slug);
    if (worldCards === undefined) {
      // No card list was supplied for this world: the card could not be
      // checked. This is NOT a not-found — say so explicitly.
      return { ok: false, error: 'card_unverified', param: 'card', requested, world, ignored };
    }
    const card = worldCards.get(requested.card) || null;
    if (!card) {
      return { ok: false, error: 'card_not_found', param: 'card', requested, world, ignored };
    }
    return {
      ok: true,
      kind: 'card',
      world,
      card,
      ignored,
      urls: canonicalUrls(world.slug, card.cardId),
    };
  }

  return {
    ok: true,
    kind: 'world',
    world,
    card: null,
    ignored,
    urls: canonicalUrls(world.slug, null),
  };
}
