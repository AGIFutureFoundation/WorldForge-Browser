# Loading WorldForge into Neon (founder steps)

`worldforge/neon/` holds the WorldForge build as Postgres 16 SQL, in its own schema `worldforge` so it never touches
the family tables from `neon/` (`public.worlds`, `public.agents`, ...). Nothing here has been applied to any database:
no Neon project, role or connection string exists yet. These steps are the founder's.

| File | What it is |
|---|---|
| `schema.sql` | `CREATE SCHEMA worldforge` and 12 tables: `worlds_ref`, `cards`, `card_reserved_actions`, `buildings`, `avatars`, `persona_prompts`, `training_lessons`, `onchain_collections`, `onchain_tokens`, `landmarks`, `mount_plans`, `evals`. Idempotent, one transaction. |
| `seed.sql` | Every row, generated from `worldforge/out`. Deterministic, stamped (`-- worldforge-neon-source-stamp:`), one transaction, upserts only. |
| `manifest.json` | Stamp, row counts per table, source files, eval results. |
| `build_seed.py` | Python 3 stdlib builder; writes nothing unless every eval passes. |

```bash
python3 worldforge/neon/build_seed.py           # rebuild; last line: ---- worldforge neon: <T> tables, <R> rows, <F> failing evals
python3 worldforge/neon/build_seed.py --check   # "worldforge neon current (<stamp>)", or "... STALE ..." and exit 1
```

## 1. Create the project (Neon console)

1. Sign in at console.neon.tech yourself and create a project (Postgres 16). If it will also hold the family
   tables from `neon/`, use the same project; the `worldforge` schema keeps them apart. To try it safely first,
   create a branch (for example `worldforge-trial`) and load there.
2. In the project's **Connection details**, pick the branch, the database and the owner role, and turn **off**
   connection pooling: the files use explicit transactions and `SET`, so use the direct (unpooled) string.
3. Copy that connection string. Do not paste it into chat, a file, a commit, a console page or a log.

## 2. Put the connection string in the shell environment only

In the terminal you will load from:

```bash
read -rs NEON_DATABASE_URL && export NEON_DATABASE_URL   # paste, press Enter; nothing is echoed or saved to history
```

It lives only in that shell session. Never write it into `.env` committed files, this folder or any script here
(`.env*` is gitignored; keep it that way). `unset NEON_DATABASE_URL` when you are done.

## 3. Load

Install the Postgres client if needed (`brew install libpq && brew link --force libpq`), rebuild and check, then load:

```bash
python3 worldforge/neon/build_seed.py --check
psql "$NEON_DATABASE_URL" -v ON_ERROR_STOP=1 -f worldforge/neon/schema.sql -f worldforge/neon/seed.sql
```

`seed.sql` is about 6 MB in one transaction; it either loads completely or not at all. Re-running both files is
safe: the schema is `IF NOT EXISTS` and every row is an upsert. Nothing is ever deleted, so a card removed from
`worldforge/out` stays until a person removes it.

## 4. Verify (read-only)

Each query below only reads. Run them with `psql "$NEON_DATABASE_URL" -v ON_ERROR_STOP=1 -c "<query>"`, or open
`psql "$NEON_DATABASE_URL"` and paste them after `SET default_transaction_read_only = on;`.

```sql
-- row counts; compare with worldforge/neon/manifest.json "tables"
SELECT 'worlds_ref' t, count(*) FROM worldforge.worlds_ref UNION ALL SELECT 'cards', count(*) FROM worldforge.cards
UNION ALL SELECT 'card_reserved_actions', count(*) FROM worldforge.card_reserved_actions UNION ALL SELECT 'buildings', count(*) FROM worldforge.buildings
UNION ALL SELECT 'avatars', count(*) FROM worldforge.avatars UNION ALL SELECT 'persona_prompts', count(*) FROM worldforge.persona_prompts
UNION ALL SELECT 'training_lessons', count(*) FROM worldforge.training_lessons UNION ALL SELECT 'onchain_collections', count(*) FROM worldforge.onchain_collections
UNION ALL SELECT 'onchain_tokens', count(*) FROM worldforge.onchain_tokens UNION ALL SELECT 'landmarks', count(*) FROM worldforge.landmarks
UNION ALL SELECT 'mount_plans', count(*) FROM worldforge.mount_plans UNION ALL SELECT 'evals', count(*) FROM worldforge.evals;

-- cards per kind (expect 41 each of world, plaza, coordinator, gate, council, omega; 123 seats; 123 advisors)
SELECT kind, count(*) FROM worldforge.cards GROUP BY kind ORDER BY kind;

-- people govern: must return 0 rows (an agent-kind card holding a steward right, or a card missing a reserved action)
SELECT card_id FROM worldforge.cards
 WHERE kind IN ('agent','coordinator','advisor','omega')
   AND (permissions->'build' ?| array['agents','agents:zone'] OR permissions->'delegate' ?| array['agents','agents:zone'])
UNION ALL
SELECT c.card_id FROM worldforge.cards c LEFT JOIN worldforge.card_reserved_actions r USING (card_id)
 GROUP BY c.card_id HAVING count(r.action) <> 6;

-- every steward seat empty and every Omega Steward defined, not seated: must return 0 rows
SELECT card_id FROM worldforge.cards
 WHERE (kind = 'seat' AND attrs->>'seated' IS NOT NULL) OR (kind = 'omega' AND attrs->>'status' <> 'defined, not seated');

-- on-chain is draft only: must return 0 rows
SELECT world FROM worldforge.onchain_collections WHERE chain IS NOT NULL OR contract IS NOT NULL OR minted <> 0
UNION ALL SELECT world FROM worldforge.onchain_tokens WHERE minted;

-- one token per card, and every card has one: both must be 0
SELECT (SELECT count(*) FROM worldforge.cards c WHERE NOT EXISTS (SELECT 1 FROM worldforge.onchain_tokens t WHERE t.card_id = c.card_id)) AS cards_without_token,
       (SELECT count(*) - count(DISTINCT card_id) FROM worldforge.onchain_tokens) AS duplicate_tokens;

-- the builders' recorded evals: must return 0 rows
SELECT source, scope, name FROM worldforge.evals WHERE NOT ok;

-- a world at a glance
SELECT w.slug, w.name, w.anchored, w.cards, l.style, l.height_m, c.merkle_root
  FROM worldforge.worlds_ref w JOIN worldforge.landmarks l ON l.world = w.slug JOIN worldforge.onchain_collections c ON c.world = w.slug
 ORDER BY w.slug LIMIT 10;
```

## 5. Read access later

Pages stay static and never hold a connection string. If a console or the viewer should read from Neon, create a
separate read-only role (`GRANT USAGE ON SCHEMA worldforge`, `GRANT SELECT ON ALL TABLES IN SCHEMA worldforge`) and
keep its connection string server-side (a build step or a small read endpoint), as `neon/README.md` describes for the
family tables. A deployment or mint of the on-chain collection is a human-reserved action: it gets its own reviewed
migration, never a seed upsert (the `onchain_collections_not_deployed` CHECK refuses one).
