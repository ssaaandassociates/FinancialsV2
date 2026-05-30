# Slice 0 — SaaS Foundation (COMPLETE)

This release closes all of Slice 0:

| Sub-slice | What | Status |
|-----------|------|--------|
| 0a | SQLite → Postgres (Supabase) migration | ✅ Verified 97/97 on PG16 |
| 0b | Supabase Auth + multi-tenant isolation  | ✅ Verified 11/11 isolation tests |
| 0c | Next.js + shadcn-style frontend         | ✅ Builds clean, 6 routes |

## Repo layout
    /                         <- backend (unchanged from V9 + Slice 0a/0b)
    /frontend                 <- NEW Next.js app
       ├ src/app/             <- pages (login, dashboard, client, project)
       ├ src/components/      <- UI primitives + AuthProvider + TopNav
       ├ src/lib/             <- supabase client, api client, utils
       ├ tailwind.config.ts   <- TrustFactON navy + gold theme
       ├ railway.json         <- per-service Railway config
       └ README.md            <- deploy steps

## What works right now
- Backend stays in legacy mode by default (no SUPABASE_JWT_SECRET set) →
  the live site keeps working on ssaa2025. Zero risk to deploy this code.
- Frontend builds and runs. Sign-up, sign-in, sign-out via Supabase Auth.
- Dashboard fetches `/api/clients/` with Bearer token attached automatically.
- Each new user → auto-creates a Firm → all their clients are scoped to it.

## Deployment plan (when you're ready to switch UIs)
1. Push this whole repo to GitHub (one commit, everything in sync).
2. In Railway, the existing backend service auto-redeploys — still in legacy
   mode, still serves the Jinja UI on ssaa2025. Nothing breaks.
3. Add a SECOND service in the same Railway project:
      + New → GitHub Repo → same repo
      Settings:
        - Root directory: frontend
        - Build/Start: leave to NIXPACKS (uses package.json scripts)
      Variables:
        - BACKEND_URL = <your backend's Railway public URL>
        - NEXT_PUBLIC_SUPABASE_URL = https://hhcunrhrvosggemlunkd.supabase.co
        - NEXT_PUBLIC_SUPABASE_ANON_KEY = sb_publishable_xxxxx (from Supabase API page)
4. Once the frontend deploys, open its URL. You can sign up + use it. The
   backend still works either way (Jinja with cookie, Next.js with token).
5. WHEN you're ready to commit to multi-tenant SaaS as the primary UI:
   on the BACKEND service, set:
        SUPABASE_URL = https://hhcunrhrvosggemlunkd.supabase.co
        SUPABASE_JWT_SECRET = <Legacy JWT Secret from Supabase>
   At that point the legacy Jinja UI stops working (it doesn't send tokens),
   and Next.js becomes the only entry point. Reversible — unset the env var
   to roll back.

## Sample firm onboarding
1. Open frontend URL → /login → "Create an account"
2. Fill: Firm name, email, password
3. Confirm email if Supabase requires it (Auth settings → Email confirmations)
4. Sign in → dashboard → "+ New client" works → client appears in Supabase

## NOT yet done (future slices)
- Slice 1: Real client dashboard (master data, projects list, templates)
- Slice 2: Upload & Mapping page in React
- Slice 3: Data entry tabs (ageing, ratios, RP, etc.)
- Slice 4: Preview + Export
- Scope project/TB/supplementary queries by firm_id (currently scoped on clients;
  projects inherit via client.firm_id but direct project endpoints could be hardened)
