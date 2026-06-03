# Slice 2 — Mapping Page (COMPLETE)

The mapping/upload page is now fully ported to React with all V9 features + UX improvements
your testers asked for.

## What's in it

### Page layout
- **Sticky top bar** that follows the page — shows save status + "Save all" button.
  Stays visible across hundreds of TB rows so you never lose changes.
- Project landing page (`/project/[id]`) shows a workflow checklist with progress
  ("X/Y mapped") and links to Upload & Map.

### Actions
- **Upload TB** — drag-and-drop dialog accepting xlsx/xls/csv
- **Auto-map** — runs 31 keyword rules + tally-group fallback; modal shows result breakdown;
  "Re-run (overwrite)" available to redo mappings
- **Import from prev FY** — dropdown of other projects of same client with mapping counts;
  matches ledger names and copies CoA codes across
- **Import mapped TB** — bypass the grid: upload an Excel with CoA codes already in
- **TB template download** — Tally-format sample
- **Export** — current mapping state as Excel

### Mapping grid
- **Searchable combobox for both Major and Sub-code** — type to filter by code or name.
  Keyboard nav (↑↓ Enter Esc). This was your Issue #4.
- Sub-code dropdown filtered by selected Major (uses the V9.4 backend fix where parent
  resolution walks the actual parent_code chain — Revenue subs now show correctly).
- Custom CoA mappings (codes not in standard 248) still render correctly in sub dropdown.
- Per-row save status dot: red (unmapped), gold (dirty), spinner (saving), check (saved).
- **Copy mapping** — per-row copy icon opens a dialog to select target rows and copy
  the source CoA to all of them at once.

### Unified filter bar
- Status pills: All / Unmapped / Mapped / Custom CoA — AND-combine with other filters
- Group dropdown (auto-populated from TB)
- Search box (matches ledger name OR tally group)
- "X shown" live counter
- "Clear" button when any filter is active

### Hybrid auto-save (the smart bit)
- Changing a mapping flips the row to "dirty" (gold pulse)
- After 2 seconds of no further edits, ALL pending changes batch-save in one API call
  (uses `POST /map/batch`)
- Rows turn green ("saved"), then the indicator fades after 1.5s
- Failed saves show red ⚠ on the row + counter in the sticky bar
- "Save all" button forces immediate flush
- `beforeunload` warning if user tries to close the tab with unsaved changes
- Pending changes also flushed on unmount

## Files added
    frontend/src/lib/mapping-api.ts                  (typed API helpers for TB + CoA + mapping)
    frontend/src/components/ui/combobox.tsx          (searchable combobox primitive)
    frontend/src/components/ui/file-upload.tsx       (drag-drop file input)
    frontend/src/app/project/[id]/upload/page.tsx    (the mapping page)
    frontend/src/app/project/[id]/page.tsx           (rewritten — workflow checklist)

## Verified
- Backend: 97/97 e2e + 11/11 multi-tenant isolation tests pass
- Frontend: `npm run build` clean — 7 routes
    /                  148 KB
    /login             157 KB
    /dashboard         165 KB
    /client/[id]       174 KB
    /project/[id]      166 KB
    /project/[id]/upload 174 KB  ← new this slice
- All 6 production routes return 200

## NOT in this slice (next)
- Slice 3: Data entry tabs (ageing, ratios, RP, closing stock)
- Slice 4: Preview + Export
- Master-data IMPORT flow (upload filled blank template back) — deferred to a quick
  follow-up; the templates DOWNLOAD already works on the client dashboard.

## Deploy
Same as previous slices:
1. Push to GitHub
2. Both Railway services auto-redeploy
3. No new env vars
