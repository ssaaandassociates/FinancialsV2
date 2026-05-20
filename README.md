# TCE Financial Statement Engine v3.0
### TrustFactON Compliance Engine
### Evenset Consultancy Services OPC Pvt Ltd

---

## Quick Start (First Time)

1. **Extract** this zip to any folder (e.g., `E:\TCE-Engine`)
2. **Double-click** `SETUP.bat` — installs dependencies and creates Desktop shortcut
3. **Double-click** `TCE Engine` on your Desktop — app starts and browser opens

That's it. The database auto-creates on first run with 248 Schedule III CoA codes.

## Daily Usage

Double-click **"TCE Engine"** on Desktop → browser opens at `http://127.0.0.1:8000/`

To stop: Close the console window or press `Ctrl+C`.

## Workflow

```
① Setup      → Create client, project (FY, company type, BS dates)
② Upload TB  → Upload Tally Trial Balance (Excel/CSV) → Auto-Map CoA codes
③ Data Entry → Closing Stock (if trading/mfg), PPE Gross Block + Depreciation
④ Enrich     → Note disclosures (context-aware), Accounting Policies, Audit Entries
⑤ Preview    → View BS, PL, Notes, Cash Flow, Ratios in browser
⑥ Export     → Download 20-sheet publication-ready Excel
```

All data is saved automatically in `data/tce.db`. You can close the app and resume later — nothing is lost.

## Company Types

- **Service** — No stock/inventory
- **Trading** — Closing Stock-in-Trade only
- **Manufacturing** — Raw Material + WIP + Finished Goods + Stores & Spares

## Excel Output (20 Sheets)

Master, TB, Audit Entries, CoA Codes, Balance Sheet, Profit & Loss,
Notes-BS, Notes-PL, Cash Flow, SOCIE, TR Ageing, TP Ageing, MSME,
PPE Schedule, Related Party, Accounting Policies, Additional Disclosures,
EPS, Ratio Analysis, Contingent Liabilities

## Tech Stack

- Python + FastAPI + SQLite + Jinja2 + openpyxl
- 57 API endpoints, 6 web pages, 18 DB tables
- 248 CoA codes, 80+ keyword mapping patterns

## Files

| File | Purpose |
|------|---------|
| `SETUP.bat` | First-time setup (run once) |
| `TCE Engine.bat` | Daily launcher (double-click) |
| `start_tce.pyw` | Silent launcher (no console window) |
| `run.py` | Python entry point |
| `data/tce.db` | Your data (auto-created, keep backup!) |
| `output/` | Generated Excel files |

---
Built by **Evenset Consultancy Services OPC Pvt Ltd** | Brand: **TrustFactON**
