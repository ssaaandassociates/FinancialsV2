# Slice 0b — Supabase Auth + Multi-Tenant Isolation (COMPLETE)

## What changed
- `app/config.py`     — SUPABASE_URL, SUPABASE_JWT_SECRET, AUTH_ENABLED flag.
- `app/auth.py`       — NEW. Verifies Supabase JWT (HS256 legacy secret),
                        auto-creates User+Firm on first login, resolves firm_id.
- `app/main.py`       — AuthMiddleware now accepts a Bearer token (when AUTH_ENABLED)
                        as an alternative to the legacy cookie.
- `app/routes/projects.py` — client create/list/get/update scoped by firm_id.
- `app/services/project_service.py` — firm_id filtering on client queries.
- `requirements.txt`  — added pyjwt.
- `test_tenancy.py`   — NEW. 11 isolation checks.

## Safety design — gradual rollout
AUTH_ENABLED is True ONLY when SUPABASE_JWT_SECRET is set.
  - Secret NOT set  → legacy single-tenant mode, ssaa2025 cookie gate, unscoped queries.
                      Current live deploy keeps working unchanged.
  - Secret SET      → multi-tenant. Bearer token required on /api. Every firm sees
                      only its own data.

## Verified
- 97/97 legacy tests pass on SQLite (auth off)
- 97/97 legacy tests pass on PostgreSQL 16 (auth off)
- 11/11 multi-tenant isolation tests pass (auth on):
    * no token / bad token rejected
    * each firm sees only its own clients
    * cannot fetch another firm's client by guessing ID (404)
    * cannot update another firm's client

## Railway env vars to enable multi-tenant (when frontend is ready)
    SUPABASE_URL         = https://hhcunrhrvosggemlunkd.supabase.co
    SUPABASE_JWT_SECRET  = <Legacy JWT Secret from Supabase → JWT Keys → Legacy tab>
DO NOT set SUPABASE_JWT_SECRET yet if the current Jinja UI must keep working with
the ssaa2025 login — the Jinja pages don't send Bearer tokens. Set it only when the
Next.js frontend (which sends tokens) is the primary UI. Until then it stays in
legacy mode and nothing breaks.

## NOT yet done
- Project/TB/supplementary queries still need firm_id scoping (clients done; projects
  inherit via client ownership but direct project endpoints to be hardened next).
- Next.js frontend + Supabase login UI (Slice 0c).
