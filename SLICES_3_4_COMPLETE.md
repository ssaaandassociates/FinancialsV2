# Slices 3 + 4 — Data Entry + Preview/Export (COMPLETE)

The entire React workflow is now end-to-end testable: sign up → client → project →
upload TB → map → audit → enrich → preview → export.

## Slice 3 — Data entry pages

### `/project/[id]/audit`
- Add / edit / delete adjusting entries (date, description, Dr CoA, Cr CoA, amount, status)
- Inline status dropdown per row (proposed / approved / posted)
- Live "Balanced ₹X" badge at top — turns red with the difference if Dr ≠ Cr
- Excel export of all entries

### `/project/[id]/data` (hub)
- Card list linking to 5 enrichment areas

### `/project/[id]/data/ageing`
- TR + TP matrices, both CY and PY
- AUTO-DERIVED from TB mappings — no separate upload
- Reads from /api/ageing/{pid}/schedule/{tr|tp}

### `/project/[id]/data/ratios`
- TOP card: all computed ratios with CY, PY, variance %, flagged badge
- BOTTOM card: PY-1 inputs (numerator + denominator per ratio)
- "Recompute" button (top-right) batch-saves and recomputes
- Flagged variance >25% highlighted red

### `/project/[id]/data/related-parties`
- Expandable rows per party — click ► to reveal txns
- Add / edit / delete txns inline
- Custom transaction type via "— Custom —" option
- "Auto-add KMP" button pulls directors flagged as KMP from client master
- "Pick from master" dropdown in Add Party dialog

### `/project/[id]/data/stock-ppe`
- Closing stock: table of stock types × CY/PY amounts, Save All
- PPE schedule: full 12-column grid (gross open/add/disp + dep open/yr/disp × CY/PY)
- Inline editable, Save All button

### `/project/[id]/data/signing`
- Signing block: auditor + 2 directors with all fields
- "Auto-fill from client" button (pulls from client master, signs_financials flag)
- CIF imports + Forex section
- Other Schedule III disclosures — list of sections with editable CY/PY/notes per item

## Slice 4 — Preview & Export

### `/project/[id]/preview`
- 6 tabs: BS / P&L / Notes / Cash Flow / Ratios / EPS
- Top validation badge: "Balance sheet balances" or "Out by ₹X"
- "Refresh" button to regenerate
- "Excel" and "PDF" download buttons in top-right
- Drill-down: every line with a note_ref shows "Note X ↗" pill
  → opens modal listing all TB ledgers under that note + totals
  → "Open mapping page" link to jump back and edit
- "Edit Mapping" / "Edit PY-1" jump-back links on every tab

## Files added
    frontend/src/lib/project-api.ts                  (typed helpers for all remaining endpoints)
    frontend/src/lib/use-auth-guard.ts               (auth gate hook)
    frontend/src/components/project-shell.tsx        (shared chrome for project sub-pages)
    frontend/src/app/project/[id]/audit/page.tsx
    frontend/src/app/project/[id]/data/page.tsx
    frontend/src/app/project/[id]/data/ageing/page.tsx
    frontend/src/app/project/[id]/data/ratios/page.tsx
    frontend/src/app/project/[id]/data/related-parties/page.tsx
    frontend/src/app/project/[id]/data/stock-ppe/page.tsx
    frontend/src/app/project/[id]/data/signing/page.tsx
    frontend/src/app/project/[id]/preview/page.tsx
    frontend/src/app/project/[id]/page.tsx          (rewritten — 4-step workflow with live progress)

## Verified
- Backend: 97/97 e2e + 11/11 multi-tenant isolation
- Frontend: `npm run build` clean — 15 routes
- All 14 production routes return 200

## Full route map
    /                                       (root redirect)
    /login                                  Supabase login
    /dashboard                              Firm dashboard, client list
    /client/[id]                            6-tab client workspace
    /project/[id]                           4-step workflow checklist
    /project/[id]/upload                    TB upload + mapping
    /project/[id]/audit                     Audit entries
    /project/[id]/data                      Enrich hub
    /project/[id]/data/ageing               TR/TP ageing (derived)
    /project/[id]/data/ratios               Ratios + EPS
    /project/[id]/data/related-parties      RP + transactions
    /project/[id]/data/stock-ppe            Closing stock + PPE
    /project/[id]/data/signing              Signing + disclosures
    /project/[id]/preview                   6-tab preview + drill + export

## End-to-end test flow for testers
1. Sign up at /login → create account
2. Dashboard → "New client" → create client
3. Open client → Overview tab → fill master data, save
4. Other tabs as needed: Directors, Shareholders, Custom CoA, Policies
5. Projects tab → "New project" with FY + dates
6. Open project → Upload & Map → upload Tally TB → auto-map → fix unmapped
7. Audit entries → add any adjusting JVs
8. Enrich data → fill ageing (auto), ratios PY-1, related parties, stock/PPE, signing
9. Preview & Export → check all 6 tabs → drill into any line → download Excel/PDF

## Deploy
Same as previous slices:
1. Push to GitHub
2. Both Railway services auto-redeploy
3. No new env vars
