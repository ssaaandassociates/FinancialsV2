# SSAA Financials Tool — Feature Tracker

## V9 Complete (Latest) — 77 files, ~10,500 Python lines, 107 endpoints, 97/97 tests passing

---

## V9 SECTIONS (NEW IN THIS RELEASE)

### Section 3: Signing Block auto-populate from Client master ✅
- New endpoint: `POST /api/signing/{project_id}/auto-populate`
- Pulls auditor (firm, FRN, partner M. No.) from Client master
- Pulls Director 1 and Director 2 from `Directors` where `signs_financials=True`
- "⚡ Auto-fill from Client" button on project dashboard signing block
- New form fields: UDIN, Director DIN fields
- Tested: pulls 2 directors + auditor end-to-end

### Section 4: Mapping page unified filter ✅
- All filters (status pills, group dropdown, search box) now AND-combine instead of cancelling each other
- New "Custom CoA" filter pill — shows only ledgers mapped to client's custom codes
- Live "X shown" badge updates as filters change
- "✕ Clear" button resets all filters at once
- Active filter pill highlighted

### Section 5: Ageing derived from TB (no separate upload) ✅
- New service functions: `derive_tr_matrix_from_tb()` and `derive_tp_matrix_from_tb()` in `ageing_engine.py`
- Old Ageing tab in data entry replaced with read-only derived matrix view
- TR matrix: 5 categories × 5 buckets (<6M, 6M-1Y, 1-2Y, 2-3Y, >3Y) + totals
- TP matrix: 5 categories × 4 buckets (<1Y, 1-2Y, 2-3Y, >3Y) + totals
- Maps leaf CoA codes BS-AS-02-03-XX (TR) and BS-EL-04-02-XX (TP) to matrix cells
- Status badge shows # of TR/TP ledgers mapped

### Section 6: Service company hides closing stock ✅
- Closing Stock tab and form completely hidden when `project.company_type == 'service'`
- Informational notice appears explaining why
- PPE tab becomes default-active tab for service companies
- Toggle works dynamically when company type changes

### Section 7: Related Party expandable rows + KMP autocomplete + custom txn type ✅
- New endpoints:
  - `GET /api/rp-transactions/party/{party_id}` — list per party
  - `PUT /api/rp-transactions/{txn_id}` — update single txn
  - `DELETE /api/rp-transactions/{txn_id}` — delete single txn
  - `GET /api/rp/kmp-candidates/{project_id}` — autocomplete source from client master
- Each party row in RP tab expands to show its transactions inline
- Per-party: add / edit (inline) / delete transactions
- "Pick from Client Master" dropdown in Add Party modal sources directors + non-director shareholders with suggested categories
- Custom transaction type field appears when "— Custom —" selected

### Section 8: Ratios live values side-by-side with PY-1 inputs ✅
- Ratio tab in data entry now shows **two cards**:
  1. **Top:** Computed Ratios table — all 11 ratios with CY, PY, variance %, flag for >25%
  2. **Bottom:** PY-1 input fields (unchanged) with "↻ Recompute" button
- Flagged variance rows highlighted in red
- Numerator/denominator description shown per ratio
- Flagged-count badge in card header

### Section 9: Preview page with 6 tabs + edit modals ✅
- Old preview had 3 tabs (BS / PL / Notes); now has 6:
  - Balance Sheet
  - Profit & Loss
  - Notes
  - **Cash Flow** (new — indirect method, with reconciliation badge)
  - **Ratios** (new — same shape as data entry tab)
  - **EPS** (new — Basic + Diluted, both years)
- "✎ Edit Mapping" / "✎ Edit Disclosures" jump-back links on each tab
- New "↳" drill-down icon on every BS/PL line with a note ref
- New endpoint: `GET /api/preview/{project_id}/line-detail?note_ref=X` — returns TB ledgers behind a line
- Line drill modal shows all ledgers mapped to that note + totals + "Open Source Page" link

### Section 10: Master data templates (blank + export-current) ✅
- New service: `templates_service.py`
- New routes: `routes/templates.py`
- Three downloads on Client Dashboard:
  - **Blank template** (`/api/templates/master-blank`) — 6-sheet Excel: README, Client Master, Directors, Shareholders, Custom CoA, Policies. Includes 1 sample row per sheet as guidance.
  - **Export current** (`/api/templates/master-current/{client_id}`) — same 6 sheets, populated with this client's existing data. Filename auto-includes client name.
  - **PPE template** (`/api/templates/ppe`) — pre-filled with 13 standard asset-class CoA codes; user just fills amounts.
- Professional styling (navy headers, borders, autosized columns)

---

## V8.2 FEATURES (PRESERVED)

### Section 1: Client Dashboard redesign
- Split layout: MCA-style master data (left) + projects + 4 blocks (right)
- Master data inline edit
- Project status pills, duplicate project, OPC badge

### Section 2: Audit Entries workflow page ③
- Dedicated /project/{id}/audit page
- CRUD with status (proposed / approved / posted)
- Excel export of audit entries
- Inline status changes

### Core engine (preserved from V6/V7)
- 248 CoA codes seeded automatically
- 31 auto-mapping rules
- BS + P&L + Notes A-S generation
- Cash Flow statement (indirect method)
- 11 Schedule III ratios with variance flagging
- EPS computation (Basic + Diluted)
- 20-sheet Excel export (A4 portrait/landscape, professional formatting)
- PDF and Word exports
- 17 accounting policies (auto-seeded)
- 20 additional disclosures (auto-seeded — CIF, CSR, ratios, benami, crypto, etc.)
- Share capital engine (Note A with all 12 sub-disclosures)
- PPE schedule (CY + PY split)
- Validation service

---

## ENDPOINT COUNT EVOLUTION
- V6: 91 endpoints
- V8.2: 98 endpoints
- **V9: 107 endpoints** (+9 new: signing auto-populate, RP txn CRUD x3, KMP candidates, line-detail, 3 template downloads)

---

## ACCESS
- URL: http://127.0.0.1:8000
- Access code: `ssaa2025`

## DEPLOYMENT
- `Procfile` (Render/Heroku) and `railway.toml` (Railway) both included for cloud deploy

## TEST COVERAGE
- `test_e2e.py`: 97 checks across all sprints + V9 sections
- Run: `python3 test_e2e.py`
