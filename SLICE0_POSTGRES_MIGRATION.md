# Slice 0a — SQLite → Postgres Migration (COMPLETE)

## What changed
- `app/config.py` — reads DATABASE_URL from env (Postgres in prod), SQLite fallback locally.
  Normalises `postgres://` → `postgresql://`. Adds ACCESS_CODE env override.
- `app/database.py` — Postgres-safe engine (pool_pre_ping, pool_recycle); SQLite-only
  check_same_thread; registers new tenancy models.
- `app/models/tenancy.py` — NEW. Firm + User tables (one firm per user, no roles yet).
- `app/models/client.py` — added `firm_id` column (nullable, indexed, FK to firms).
- `requirements.txt` — added psycopg2-binary.

## Verified
- 97/97 tests pass on SQLite (local dev, no env var needed)
- 97/97 tests pass on PostgreSQL 16 (same major version as Supabase)
- All 25 tables create cleanly in Postgres incl. firms, users, clients.firm_id
- 248 CoA + 31 mapping rules seed correctly into Postgres

## Railway deployment steps
1. In Railway → your service → Variables, add:
     DATABASE_URL = <your Supabase connection string URI>
     ACCESS_CODE  = <optional, defaults to ssaa2025>
2. Get the Supabase URI from: Supabase → Project Settings → Database →
   Connection string → URI. Use the "Connection pooling" (port 6543) string
   for serverless-style hosts, or the direct (5432) string for Railway.
   IMPORTANT: replace [YOUR-PASSWORD] in the URI with your real DB password.
3. Redeploy. On first boot, init_db() creates all tables and seeds CoA in Supabase.
4. Data now persists across deploys (Supabase is external & permanent) — this also
   fixes the earlier "SQLite wipes on redeploy" problem.

## NOT yet done (next slices)
- Auth wiring (Supabase Auth → User records)
- firm_id scoping enforced on all client/project queries
- Next.js frontend
