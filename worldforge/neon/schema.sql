-- worldforge/neon/schema.sql: the WorldForge build (worldforge/out/) as Postgres 16 DDL for Neon.
--
-- Everything lives in its own schema, `worldforge`, so it never collides with the family tables in neon/schema.sql
-- (public.worlds, public.agents, ...). The two can share one Neon database or live apart; nothing here references
-- the public schema, and worldforge.worlds_ref.family_slug is a plain text link, not a foreign key.
--
-- Apply order: worldforge/neon/schema.sql, then worldforge/neon/seed.sql (see worldforge/neon/LOAD.md).
-- Idempotent: CREATE ... IF NOT EXISTS everywhere and COMMENT ON overwrites in place, so a second run changes
-- nothing. IF NOT EXISTS never alters an existing table: a changed column or constraint needs a migration, tried on
-- a Neon branch first.
--
-- Never stored here, by design: credentials, keys, tokens, connection strings, tax identifiers, private
-- repositories. worldforge/neon/build_seed.py fails its evals if one reaches seed.sql.
--
-- Agents operate; people govern. Every Master Card holds transfer and govern for the steward quorum, every
-- human-reserved action is held for the 2-of-3 Steward Council, and the on-chain tables can only describe a
-- collection that is NOT deployed and NOT minted. The CHECKs below hold those lines inside the database too.

BEGIN;

CREATE SCHEMA IF NOT EXISTS worldforge;
COMMENT ON SCHEMA worldforge IS 'WorldForge SmartCiti.X Master Cards, avatars, persona prompts, landmarks, mount plans and draft (undeployed) on-chain metadata, seeded from worldforge/out by worldforge/neon/build_seed.py. Powered by AGI Corp.';

-- -------------------------------------------------------------------------------------------- worlds_ref ----
-- One row per world WorldForge builds (worldforge/out/index.json "worlds"). family_slug names the same world in the
-- family schema (public.worlds) when agents/corporations/index.json lists it as a series cell; else NULL.
-- rp1_lat/rp1_lon come from the world card's anchor and stay NULL until a steward writes a location.
CREATE TABLE IF NOT EXISTS worldforge.worlds_ref (
  slug            text PRIMARY KEY CHECK (slug ~ '^[a-z0-9][a-z0-9-]*$'),
  name            text NOT NULL,
  status          text NOT NULL,
  family_slug     text,
  anchored        boolean NOT NULL,
  rp1_lat         double precision CHECK (rp1_lat BETWEEN -90 AND 90),
  rp1_lon         double precision CHECK (rp1_lon BETWEEN -180 AND 180),
  omega           boolean NOT NULL,
  cards           integer NOT NULL CHECK (cards >= 0),
  zones           integer NOT NULL CHECK (zones >= 0),
  agents          integer NOT NULL CHECK (agents >= 0),
  primitives      integer NOT NULL CHECK (primitives >= 0),
  roads           integer NOT NULL CHECK (roads >= 0),
  plan_nodes      integer NOT NULL CHECK (plan_nodes >= 0),
  resource_nodes  integer NOT NULL CHECK (resource_nodes >= 0),
  glb_path        text NOT NULL,
  glb_bytes       integer NOT NULL CHECK (glb_bytes > 0),
  glb_sha256      char(64) NOT NULL CHECK (glb_sha256 ~ '^[0-9a-f]{64}$'),
  cards_sha256    char(64) NOT NULL CHECK (cards_sha256 ~ '^[0-9a-f]{64}$'),
  gaps            text[] NOT NULL,
  gates           jsonb NOT NULL,
  CONSTRAINT worlds_ref_rp1_pair CHECK ((rp1_lat IS NULL) = (rp1_lon IS NULL)),
  CONSTRAINT worlds_ref_anchored_means_located CHECK (anchored = (rp1_lat IS NOT NULL))
);

-- ------------------------------------------------------------------------------------------------- cards ----
-- One row per SmartCiti.X Master Card (worldforge/out/<slug>/cards.json). volum is the bounded 3-D region, permissions the
-- seven-right matrix. attrs holds every other key of the card verbatim (avatar, binding, building, persona, voice,
-- may_never, anchor, ...) so the card can be rebuilt exactly; its reserved_for_humans list is in card_reserved_actions.
-- parent_card_id is deferred so a re-seed is checked at COMMIT.
CREATE TABLE IF NOT EXISTS worldforge.cards (
  card_id         text PRIMARY KEY,
  world           text NOT NULL REFERENCES worldforge.worlds_ref (slug),
  kind            text NOT NULL CHECK (kind IN ('world', 'plaza', 'coordinator', 'advisor', 'gate', 'council', 'seat', 'omega', 'zone', 'agent')),
  parent_card_id  text,
  name            text,
  display_name    text NOT NULL,
  owner           text NOT NULL,
  umbrella        text NOT NULL CHECK (umbrella = 'Powered by AGI Corp'),
  volum           jsonb NOT NULL,
  permissions     jsonb NOT NULL,
  source          text NOT NULL,
  attrs           jsonb NOT NULL,
  CONSTRAINT cards_parent_fk FOREIGN KEY (parent_card_id) REFERENCES worldforge.cards (card_id) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT cards_root_is_world CHECK ((parent_card_id IS NULL) = (kind = 'world')),
  CONSTRAINT cards_quorum_holds_transfer_and_govern CHECK (
    permissions -> 'transfer' = '["steward-quorum"]'::jsonb AND permissions -> 'govern' = '["steward-quorum"]'::jsonb),
  CONSTRAINT cards_volum_is_box CHECK (volum ->> 'shape' = 'box' AND jsonb_typeof(volum -> 'center') = 'array' AND jsonb_typeof(volum -> 'halfExtents') = 'array')
);
CREATE INDEX IF NOT EXISTS cards_world_kind ON worldforge.cards (world, kind);
CREATE INDEX IF NOT EXISTS cards_parent ON worldforge.cards (parent_card_id);

-- --------------------------------------------------------------------------------- card_reserved_actions ----
-- The six PBC actions every card reserves for people (worlds/PBC.json, verbatim), each held for the Steward Council by
-- a 2-of-3 quorum of 3 seats. ord keeps the card's own order.
CREATE TABLE IF NOT EXISTS worldforge.card_reserved_actions (
  card_id  text NOT NULL REFERENCES worldforge.cards (card_id),
  action   text NOT NULL CHECK (action IN ('governance.final_vote', 'charter.amend', 'treasury.transfer', 'proposal.enact', 'windfall.distribute', 'steward.appoint')),
  ord      integer NOT NULL CHECK (ord >= 0),
  holder   text NOT NULL CHECK (holder = 'Steward Council'),
  quorum   text NOT NULL CHECK (quorum = '2-of-3'),
  seats    integer NOT NULL CHECK (seats = 3),
  PRIMARY KEY (card_id, action)
);

-- ------------------------------------------------------------------------------------------------ buildings ----
-- The building shell, interior and room the spaces build made for a zone or council card (cards.json "building").
-- Paths are repository paths (my-fabric/worlds/models/...); the GLBs themselves are not stored in the database.
CREATE TABLE IF NOT EXISTS worldforge.buildings (
  card_id     text PRIMARY KEY REFERENCES worldforge.cards (card_id),
  world       text NOT NULL REFERENCES worldforge.worlds_ref (slug),
  kind        text NOT NULL,
  sign        text,
  exterior    text NOT NULL,
  interior    text,
  room        text,
  door        jsonb,
  resolution  jsonb,
  triangles   jsonb,
  source      text NOT NULL
);

-- -------------------------------------------------------------------------------------------------- avatars ----
-- One row per avatar (worldforge/out/avatars/index.json "rows"). card_id links the avatar's Master Card and is NULL
-- for an avatar with none. audio_path is the EXPECTED path of the recorded synthetic line only: whether the file exists
-- is never stored (viewers HEAD-check it). attrs keeps every other key of the row verbatim.
CREATE TABLE IF NOT EXISTS worldforge.avatars (
  avatar_id          text PRIMARY KEY,
  card_id            text REFERENCES worldforge.cards (card_id),
  world              text NOT NULL REFERENCES worldforge.worlds_ref (slug),
  kind               text NOT NULL CHECK (kind IN ('specialist', 'coordinator', 'advisor', 'omega')),
  role               text NOT NULL,
  name               text NOT NULL,
  binding            jsonb NOT NULL,
  intro              text NOT NULL,
  audio_path         text,
  model_ref          text NOT NULL,
  persona_prompt_id  text,
  source             text NOT NULL,
  attrs              jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS avatars_world ON worldforge.avatars (world);

-- ----------------------------------------------------------------------------------------- persona_prompts ----
-- The persona layer plus the unchanged house metaprompt for each prompted avatar (worldforge/out/avatars/prompts/
-- <slug>.json). No model has run these. gates_* are the prompt gates worldforge/avatars.mjs ran on the text.
-- Advisors have no row: by the advisor contract they are scripted guides and get no prompt.
CREATE TABLE IF NOT EXISTS worldforge.persona_prompts (
  id            text PRIMARY KEY,
  avatar_id     text NOT NULL REFERENCES worldforge.avatars (avatar_id),
  world         text NOT NULL REFERENCES worldforge.worlds_ref (slug),
  kind          text NOT NULL,
  role          text NOT NULL,
  name          text NOT NULL,
  chars         integer NOT NULL CHECK (chars > 0),
  text          text NOT NULL,
  gates_passed  integer NOT NULL CHECK (gates_passed >= 0),
  gates_of      integer NOT NULL CHECK (gates_of >= 0),
  gates_failed  text[] NOT NULL,
  CONSTRAINT persona_prompts_gates_le CHECK (gates_passed <= gates_of)
);

-- ---------------------------------------------------------------------------------------- training_lessons ----
-- Draft lessons from worldforge/out/training/<slug>.json (the worlds worldforge/out/training/index.json lists), when that
-- build exists. No lesson is certified. The record is kept verbatim in jsonb;
-- world and title are lifted out when the record names them, else NULL.
CREATE TABLE IF NOT EXISTS worldforge.training_lessons (
  lesson_id  text PRIMARY KEY,
  world      text,
  title      text,
  source     text NOT NULL,
  record     jsonb NOT NULL
);

-- ------------------------------------------------------------------------------------- onchain_collections ----
-- Draft ERC-721 metadata per world (worldforge/out/onchain/<slug>/collection.json): NOT deployed, NOT minted. There is
-- no chain, contract, wallet, address or transaction, and the CHECK keeps it that way: a deployment is a human-reserved
-- action and gets its own reviewed migration, never a seed upsert. merkle_root is over the token metadata files;
-- network_proof proves that root under network_root (worldforge/out/onchain/index.json).
CREATE TABLE IF NOT EXISTS worldforge.onchain_collections (
  world          text PRIMARY KEY REFERENCES worldforge.worlds_ref (slug),
  name           text NOT NULL,
  standard       text NOT NULL,
  status         text NOT NULL,
  token_count    integer NOT NULL CHECK (token_count >= 0),
  card_count     integer NOT NULL CHECK (card_count >= 0),
  merkle_root    char(64) NOT NULL CHECK (merkle_root ~ '^[0-9a-f]{64}$'),
  network_root   char(64) NOT NULL CHECK (network_root ~ '^[0-9a-f]{64}$'),
  network_proof  text[] NOT NULL,
  cards_sha256   char(64) NOT NULL CHECK (cards_sha256 ~ '^[0-9a-f]{64}$'),
  token_id_rule  text NOT NULL,
  chain          text,
  contract       text,
  minted         integer NOT NULL,
  transactions   integer NOT NULL,
  CONSTRAINT onchain_collections_not_deployed CHECK (chain IS NULL AND contract IS NULL AND minted = 0 AND transactions = 0),
  CONSTRAINT onchain_collections_tokens_match_cards CHECK (token_count = card_count)
);

-- ------------------------------------------------------------------------------------------ onchain_tokens ----
-- One draft token per Master Card. token_id is the first 16 hex characters of sha256(cardId); leaf_sha256 is sha256 of
-- the canonical metadata file; proof is the sorted-pair Merkle path to the collection root. minted is always false.
CREATE TABLE IF NOT EXISTS worldforge.onchain_tokens (
  token_id       char(16) PRIMARY KEY CHECK (token_id ~ '^[0-9a-f]{16}$'),
  world          text NOT NULL REFERENCES worldforge.onchain_collections (world),
  card_id        text NOT NULL REFERENCES worldforge.cards (card_id),
  name           text NOT NULL,
  kind           text NOT NULL,
  metadata_path  text NOT NULL,
  leaf_sha256    char(64) NOT NULL CHECK (leaf_sha256 ~ '^[0-9a-f]{64}$'),
  proof          text[] NOT NULL,
  minted         boolean NOT NULL CHECK (minted = false),
  CONSTRAINT onchain_tokens_one_per_card UNIQUE (card_id)
);

-- ----------------------------------------------------------------------------------------------- landmarks ----
-- The synthetic procedural civic landmark per world (worldforge/out/assets/landmarks/index.json): not a real building
-- and not modelled on one. sha256 is the GLB's own hash; placement is where the viewer puts it.
CREATE TABLE IF NOT EXISTS worldforge.landmarks (
  world      text PRIMARY KEY REFERENCES worldforge.worlds_ref (slug),
  file       text NOT NULL,
  bytes      integer NOT NULL CHECK (bytes > 0),
  sha256     char(64) NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
  triangles  integer NOT NULL CHECK (triangles >= 0),
  vertices   integer NOT NULL CHECK (vertices >= 0),
  height_m   double precision NOT NULL CHECK (height_m > 0),
  style      text NOT NULL,
  hue        integer NOT NULL CHECK (hue BETWEEN 0 AND 360),
  mark       text NOT NULL,
  node       text NOT NULL,
  placement  jsonb NOT NULL,
  bounds     jsonb NOT NULL,
  materials  text[] NOT NULL,
  synthetic  boolean NOT NULL CHECK (synthetic = true)
);

-- --------------------------------------------------------------------------------------------- mount_plans ----
-- A summary of each world's Sneeze SOM mount plan (worldforge/out/<slug>/sneeze-mount-plan.json). The plan is prepared,
-- not mounted; the node list itself stays in the file.
CREATE TABLE IF NOT EXISTS worldforge.mount_plans (
  world                    text PRIMARY KEY REFERENCES worldforge.worlds_ref (slug),
  schema_version           text NOT NULL,
  engine                   text NOT NULL,
  binding_status           text NOT NULL,
  root_card_id             text NOT NULL REFERENCES worldforge.cards (card_id),
  mount_parent             text NOT NULL,
  nodes                    integer NOT NULL CHECK (nodes >= 0),
  resource_nodes           integer NOT NULL CHECK (resource_nodes >= 0),
  preview_glb_path         text NOT NULL,
  preview_glb_sha256       char(64) NOT NULL CHECK (preview_glb_sha256 ~ '^[0-9a-f]{64}$'),
  assets                   jsonb NOT NULL,
  acceptance_requirements  text[] NOT NULL
);

-- --------------------------------------------------------------------------------------------------- evals ----
-- The eval results the WorldForge builders recorded: per-world card evals (worldforge/out/<slug>/manifest.json),
-- avatar checks (worldforge/out/avatars/index.json) and on-chain evals (worldforge/out/onchain/index.json). scope is
-- 'world:<slug>' or 'network'. These mirror the builders' own reports; this table never decides a gate.
CREATE TABLE IF NOT EXISTS worldforge.evals (
  source  text NOT NULL,
  scope   text NOT NULL CHECK (scope = 'network' OR scope ~ '^world:[a-z0-9][a-z0-9-]*$'),
  name    text NOT NULL,
  ok      boolean NOT NULL,
  PRIMARY KEY (source, scope, name)
);

COMMIT;
