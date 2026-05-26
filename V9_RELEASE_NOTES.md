# SSAA Financials Tool — V9 Release Notes

## What's new in V9

V9 ships 8 sections of UX and workflow improvements on top of V8.2. All changes preserve V8.2 functionality (97/97 tests pass).

### ⚡ Section 3: Signing Block auto-populate
Click **"Auto-fill from Client"** on the project dashboard. Pulls auditor info and signing directors automatically. No more retyping the same names every year.

### 🔍 Section 4: Mapping page unified filter
Filters now combine instead of cancelling each other. New "Custom CoA" pill shows only ledgers mapped to your client's custom codes. Live "X shown" counter.

### 📊 Section 5: Ageing from TB (no upload)
No more separate ageing upload. Map ledgers to TR / TP leaf codes (`BS-AS-02-03-XX` / `BS-EL-04-02-XX`) and the ageing matrix auto-builds. Editable view on data entry page.

### 🏢 Section 6: Service company hides closing stock
Set project type to "service" → closing stock tab disappears entirely. PPE becomes default tab.

### 👥 Section 7: Related Party expandable rows
Each party row expands inline to show / edit / add / delete its transactions. New "Pick from Client Master" dropdown sources directors + shareholders. Custom transaction type field works.

### 📈 Section 8: Ratios with computed values side-by-side
Ratio tab now shows computed CY / PY / variance % / flag (>25%) above the PY-1 input form. Click "↻ Recompute" after editing PY-1 values.

### 🎯 Section 9: Preview page with 6 tabs + drill-down
Preview now has Balance Sheet / P&L / Notes / **Cash Flow** / **Ratios** / **EPS**. Click "↳" on any line item to see all TB ledgers behind it in a modal. "✎ Edit Mapping" jump-back links on every tab.

### 📥 Section 10: Master data templates
Three new downloads on client dashboard:
- **Blank template** — 6-sheet Excel with sample rows
- **Export current** — same 6 sheets with this client's data pre-filled
- **PPE template** — pre-filled with 13 standard asset classes

---

## Access
- URL: `http://127.0.0.1:8000` (after `python run.py`)
- Access code: `ssaa2025`

## Demo Walkthrough (suggested order for CA demo)

1. **Land on firm dashboard** — show client list
2. **Click into a client** — show split layout, mention master data carries across FYs
3. **Click "Export current"** — show Excel template auto-fills with their data
4. **Open a project** — show signing block "Auto-fill from Client" button
5. **Click "Upload & Map"** — demo unified filter bar, search for "creditor", filter to unmapped
6. **Go to Data tab → Ageing** — show ageing matrix derives from TB automatically
7. **Go to Data tab → Ratios** — show 11 ratios computed live with variance flagging
8. **Go to Data tab → Related Party** — expand a party row to show inline txn editing
9. **Go to Preview** — show 6 tabs, drill down on a line to see TB ledgers behind it
10. **Click Excel export** — 20-sheet workbook with full formatting

## Technical
- 77 files, ~10,500 lines of Python, 107 API endpoints
- FastAPI + SQLite (SQLAlchemy ORM) + Jinja2 templates
- All test cases: `python3 test_e2e.py` → 97/97 pass

## Cloud Deploy
- `Procfile` for Render/Heroku
- `railway.toml` for Railway
- SQLite DB at `data/tce.db` — back up before deploy
