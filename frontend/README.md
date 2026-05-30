# SSAA Financials — Frontend (Next.js)

Modern React/Next.js UI for the SSAA Financials Tool. The Python FastAPI backend
(in the parent folder) stays as-is; this frontend calls it via `/api/*` rewrites.

## Local dev

```bash
cp .env.local.example .env.local      # fill values
npm install
npm run dev                            # http://localhost:3000
```

The backend should be running at the URL set in `BACKEND_URL`
(default `http://localhost:8000` for local dev).

## Required env vars

| Variable                       | Where it goes        | Notes                            |
|--------------------------------|----------------------|----------------------------------|
| `BACKEND_URL`                  | Railway frontend svc | Internal URL of backend service. |
| `NEXT_PUBLIC_SUPABASE_URL`     | Railway frontend svc | Public — sent to browser.        |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY`| Railway frontend svc | Public — sent to browser.        |

The **backend** (separate Railway service) needs:

| Variable                | Notes                                              |
|-------------------------|----------------------------------------------------|
| `DATABASE_URL`          | Supabase pooler URI (already set)                  |
| `SUPABASE_URL`          | Same Supabase project URL                          |
| `SUPABASE_JWT_SECRET`   | Supabase → JWT Keys → Legacy → reveal              |

Setting `SUPABASE_JWT_SECRET` on the backend is the switch that turns the system
multi-tenant. Don't set it until this Next.js frontend is the primary UI;
without it, the backend stays in legacy mode (cookie + ssaa2025).

## Deploy on Railway (two services, one repo)

1. In your existing Railway project, click **+ New** → **GitHub Repo** → pick
   the same repo (`FinancialsV2`).
2. After it imports, open the new service → **Settings**:
   - **Root Directory**: `frontend`
   - **Build / Start commands**: leave to NIXPACKS auto-detect (uses `npm run start`).
3. Add the three env vars above (`BACKEND_URL`, `NEXT_PUBLIC_SUPABASE_URL`,
   `NEXT_PUBLIC_SUPABASE_ANON_KEY`).
4. For `BACKEND_URL`: get the backend service's internal URL from Railway
   (it's something like `http://web-production-8c4a7.up.railway.app` — use the
   public one for simplicity, or the internal `service.railway.internal` for speed).
5. Deploy. Visit the frontend URL → /login → sign up → see the dashboard.
