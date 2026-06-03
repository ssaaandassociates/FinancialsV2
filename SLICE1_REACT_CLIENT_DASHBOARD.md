# Slice 1 — React Client Dashboard (COMPLETE)

The Jinja `/client/{id}` page is now a fully-functional React/Next.js page with
tabbed IA and full CRUD for every block.

## What's in it

### Layout
- Tabbed page header with master data export buttons + delete client (top-right).
- 6 tabs, URL-hash-synced so reloads preserve the active tab:
  - **Overview** — master data (Identification, Auditor, Share capital) with view/edit toggle
  - **Projects** — list, create (FY + dates + company type), duplicate, delete (with confirm)
  - **Directors** — add/edit/delete; KMP, Signs-financials, Active flags
  - **Shareholders** — add/edit/delete in a table; CY/PY shares + %, promoter & director flags
  - **Policies** — numbered list; title + body + active flag
  - **Custom CoA** — code, particulars, parent, nature, FS type, note ref

### Safety
- Delete client requires typing the exact client name (matches V9.4 backend)
- All API calls automatically carry the Supabase Bearer token via the api.ts helper
- All queries scoped by firm_id when AUTH_ENABLED on backend → real multi-tenant

### Files added
    frontend/src/lib/client-api.ts             (typed API helpers for all 6 entities)
    frontend/src/app/client/[id]/page.tsx       (orchestrator + delete)
    frontend/src/app/client/[id]/tabs/
        overview.tsx
        projects.tsx
        directors.tsx
        shareholders.tsx
        policies.tsx
        custom-coa.tsx
    frontend/src/components/ui/                 (new primitives)
        label.tsx, textarea.tsx, select.tsx, checkbox.tsx,
        tabs.tsx, dialog.tsx, empty.tsx

## Verified
- Backend: 97/97 e2e + 11/11 multi-tenant isolation tests pass
- Frontend: `npm run build` clean — 6 routes
    /           148 KB
    /login      157 KB
    /dashboard  165 KB
    /client/[id] 173 KB   ← new this slice, 11.7 KB page bundle
    /project/[id] 164 KB
- Production server runs, all routes return 200

## What's NOT yet in this slice
Deferred to next slices for proper scope:
- Master-data IMPORT flow (parser + upsert from filled blank template)
- PPE template IMPORT + move PPE to a dedicated tab inside Project
- Searchable combobox for sub-codes (lands in Slice 2 — mapping page)
- Project workspace itself (upload / mapping / data entry / preview)

## Deploy
Same flow as Slice 0c:
1. Push to GitHub
2. Backend service on Railway: auto-redeploys (no impact, legacy mode unchanged)
3. Frontend service on Railway: auto-redeploys, picks up new tab pages
4. No new env vars needed — uses the same Supabase + BACKEND_URL set in Slice 0c
