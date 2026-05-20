"""
PPE Schedule Service — with full CY and PY Gross Block + Depreciation.
Validates Net CY against TB balance.
"""
from sqlalchemy.orm import Session
from app.models import PPEScheduleEntry
from app.services.financial_engine import get_adjusted_balances

PPE_ASSET_CLASSES = [
    ("Land (Freehold)", "BS-AS-01-01-01", "tangible"),
    ("Land (Leasehold)", "BS-AS-01-01-02", "tangible"),
    ("Buildings", "BS-AS-01-01-03", "tangible"),
    ("Plant & Equipment", "BS-AS-01-01-04", "tangible"),
    ("Furniture & Fixtures", "BS-AS-01-01-05", "tangible"),
    ("Vehicles", "BS-AS-01-01-06", "tangible"),
    ("Office Equipment", "BS-AS-01-01-07", "tangible"),
    ("Computers", "BS-AS-01-01-08", "tangible"),
    ("Other Tangible Assets", "BS-AS-01-01-09", "tangible"),
    ("Goodwill", "BS-AS-01-01-10", "intangible"),
    ("Computer Software", "BS-AS-01-01-11", "intangible"),
    ("Brands / Trademarks", "BS-AS-01-01-12", "intangible"),
    ("Copyrights / Patents / IP", "BS-AS-01-01-13", "intangible"),
    ("Other Intangible Assets", "BS-AS-01-01-14", "intangible"),
]


def seed_ppe_schedule(db: Session, project_id: int) -> int:
    existing = db.query(PPEScheduleEntry).filter(PPEScheduleEntry.project_id == project_id).count()
    if existing > 0:
        return existing
    for asset_class, coa_code, asset_type in PPE_ASSET_CLASSES:
        db.add(PPEScheduleEntry(project_id=project_id, asset_class=asset_class,
                                 coa_code=coa_code, asset_type=asset_type))
    db.commit()
    return len(PPE_ASSET_CLASSES)


def save_ppe_entry(db: Session, entry_id: int, **fields) -> PPEScheduleEntry:
    entry = db.query(PPEScheduleEntry).filter(PPEScheduleEntry.id == entry_id).first()
    if not entry:
        raise ValueError(f"PPE entry {entry_id} not found")
    allowed = {
        'gross_opening', 'gross_additions', 'gross_disposals',
        'dep_opening', 'dep_for_year', 'dep_on_disposals',
        'py_gross_opening', 'py_gross_additions', 'py_gross_disposals',
        'py_dep_opening', 'py_dep_for_year', 'py_dep_on_disposals',
    }
    for k, v in fields.items():
        if k in allowed and v is not None:
            setattr(entry, k, float(v))
    db.commit()
    db.refresh(entry)
    return entry


def _row_dict(e, tb_balance_cy=0, tb_balance_py=0):
    """Build a dict for one PPE row with all computed values."""
    return {
        "id": e.id,
        "asset_class": e.asset_class,
        "coa_code": e.coa_code,
        "asset_type": e.asset_type,
        # CY
        "gross_opening": e.gross_opening or 0,
        "gross_additions": e.gross_additions or 0,
        "gross_disposals": e.gross_disposals or 0,
        "gross_closing": e.gross_closing,
        "dep_opening": e.dep_opening or 0,
        "dep_for_year": e.dep_for_year or 0,
        "dep_on_disposals": e.dep_on_disposals or 0,
        "dep_closing": e.dep_closing,
        "net_cy": e.net_cy,
        # PY
        "py_gross_opening": e.py_gross_opening or 0,
        "py_gross_additions": e.py_gross_additions or 0,
        "py_gross_disposals": e.py_gross_disposals or 0,
        "py_gross_closing": e.py_gross_closing,
        "py_dep_opening": e.py_dep_opening or 0,
        "py_dep_for_year": e.py_dep_for_year or 0,
        "py_dep_on_disposals": e.py_dep_on_disposals or 0,
        "py_dep_closing": e.py_dep_closing,
        "net_py": e.net_py,
        # Validation
        "tb_balance_cy": tb_balance_cy,
        "tb_balance_py": tb_balance_py,
        "tb_matched": abs(e.net_cy - tb_balance_cy) < 1.0 if (e.gross_opening or e.gross_additions) else True,
    }


def _empty_totals():
    keys = [
        "gross_opening", "gross_additions", "gross_disposals", "gross_closing",
        "dep_opening", "dep_for_year", "dep_on_disposals", "dep_closing", "net_cy",
        "py_gross_opening", "py_gross_additions", "py_gross_disposals", "py_gross_closing",
        "py_dep_opening", "py_dep_for_year", "py_dep_on_disposals", "py_dep_closing", "net_py",
    ]
    return {k: 0 for k in keys}


def _add_to_totals(totals, row):
    for k in totals:
        totals[k] += row.get(k, 0)


def get_ppe_schedule(db: Session, project_id: int) -> dict:
    seed_ppe_schedule(db, project_id)
    entries = db.query(PPEScheduleEntry).filter(PPEScheduleEntry.project_id == project_id).all()
    balances = get_adjusted_balances(db, project_id)

    tangible, intangible = [], []
    total_tang, total_intang = _empty_totals(), _empty_totals()
    warnings = []

    for e in entries:
        tb_cy = balances.get(e.coa_code, {}).get("cy_net", 0)
        tb_py = balances.get(e.coa_code, {}).get("py_net", 0)
        row = _row_dict(e, tb_cy, tb_py)

        if not row["tb_matched"] and tb_cy != 0:
            warnings.append(f"{e.asset_class}: PPE Net CY={e.net_cy:,.0f} vs TB={tb_cy:,.0f}")

        if e.asset_type == "tangible":
            tangible.append(row)
            _add_to_totals(total_tang, row)
        else:
            intangible.append(row)
            _add_to_totals(total_intang, row)

    grand = {k: total_tang[k] + total_intang[k] for k in total_tang}

    return {
        "tangible": tangible, "intangible": intangible,
        "total_tangible": total_tang, "total_intangible": total_intang,
        "grand_total": grand,
        "validation_warnings": warnings,
        "is_valid": len(warnings) == 0,
    }
