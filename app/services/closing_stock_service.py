"""
Closing Stock Service

Closing stock is NOT part of Trial Balance — it must be entered manually.
It affects both P&L (reduces COGS) and BS (Inventories note).

Company Type Logic:
  SERVICE:       No stock at all
  TRADING:       Closing Stock-in-Trade only
  MANUFACTURING: Closing Raw Material + WIP + Finished Goods + Stores & Spares

Stock CoA Code Mapping:
  BS Side (Inventories on Balance Sheet):
    Raw Material     → BS-AS-02-02-01
    WIP              → BS-AS-02-02-02
    Finished Goods   → BS-AS-02-02-03
    Stock-in-Trade   → BS-AS-02-02-04
    Stores & Spares  → BS-AS-02-02-05

  PL Side (Credit entries to reduce COGS):
    Closing RM       → PL-04-01-03 (deducted from Cost of Materials Consumed)
    Closing FG       → PL-04-03-04 (Changes in Inventories)
    Closing WIP      → PL-04-03-05 (Changes in Inventories)
    Closing SIT      → PL-04-03-06 (Changes in Inventories)
"""
from sqlalchemy.orm import Session
from app.models import ClosingStock, Project


# Stock type → (BS code for inventory, PL code for closing deduction)
STOCK_CONFIG = {
    "raw_material":    ("BS-AS-02-02-01", "PL-04-01-03", "Raw Materials"),
    "wip":             ("BS-AS-02-02-02", "PL-04-03-05", "Work-in-Progress"),
    "finished_goods":  ("BS-AS-02-02-03", "PL-04-03-04", "Finished Goods"),
    "stock_in_trade":  ("BS-AS-02-02-04", "PL-04-03-06", "Stock-in-Trade"),
    "stores_spares":   ("BS-AS-02-02-05", None,           "Stores & Spares"),
}

# Which stock types apply to which company type
STOCK_BY_COMPANY_TYPE = {
    "service": [],
    "trading": ["stock_in_trade"],
    "manufacturing": ["raw_material", "wip", "finished_goods", "stores_spares"],
}


def get_applicable_stock_types(company_type: str) -> list[dict]:
    """Return stock types applicable for this company type."""
    types = STOCK_BY_COMPANY_TYPE.get(company_type, [])
    return [
        {
            "key": t,
            "label": STOCK_CONFIG[t][2],
            "bs_code": STOCK_CONFIG[t][0],
            "pl_code": STOCK_CONFIG[t][1],
        }
        for t in types
    ]


def save_closing_stock(db: Session, project_id: int,
                       stock_type: str, cy_amount: float,
                       py_amount: float = 0) -> ClosingStock:
    """Save or update closing stock for a specific type."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    if stock_type not in STOCK_CONFIG:
        raise ValueError(f"Invalid stock type: {stock_type}")

    bs_code, pl_code, _ = STOCK_CONFIG[stock_type]

    # Upsert
    existing = db.query(ClosingStock).filter(
        ClosingStock.project_id == project_id,
        ClosingStock.stock_type == stock_type,
    ).first()

    if existing:
        existing.cy_amount = cy_amount
        existing.py_amount = py_amount
        existing.coa_code = bs_code
        db.commit()
        db.refresh(existing)
        return existing

    entry = ClosingStock(
        project_id=project_id,
        stock_type=stock_type,
        cy_amount=cy_amount,
        py_amount=py_amount,
        coa_code=bs_code,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_closing_stock(db: Session, project_id: int) -> list[dict]:
    """Get all closing stock entries for a project."""
    rows = db.query(ClosingStock).filter(
        ClosingStock.project_id == project_id
    ).all()
    return [
        {
            "id": r.id,
            "stock_type": r.stock_type,
            "label": STOCK_CONFIG.get(r.stock_type, ("", "", r.stock_type))[2],
            "cy_amount": r.cy_amount,
            "py_amount": r.py_amount,
            "bs_code": STOCK_CONFIG.get(r.stock_type, ("", "", ""))[0],
            "pl_code": STOCK_CONFIG.get(r.stock_type, ("", "", ""))[1],
        }
        for r in rows
    ]


def get_closing_stock_adjustments(db: Session, project_id: int) -> dict:
    """
    Returns closing stock as balance adjustments to be applied by financial engine.
    Returns dict: coa_code → {"cy_net": amount, "py_net": amount}

    Closing stock creates:
    - CREDIT in PL (reduces expense) → negative Dr-Cr value
    - DEBIT in BS (asset) → positive Dr-Cr value

    Since TB stores Dr-Cr, closing stock:
    - PL closing code gets NEGATIVE value (credit = reduces COGS)
    - BS inventory code gets POSITIVE value (debit = asset on BS)
    """
    rows = db.query(ClosingStock).filter(
        ClosingStock.project_id == project_id
    ).all()

    adjustments = {}
    for r in rows:
        bs_code, pl_code, _ = STOCK_CONFIG.get(r.stock_type, (None, None, None))

        # BS side: Closing stock is an asset (Debit balance = positive)
        if bs_code:
            if bs_code not in adjustments:
                adjustments[bs_code] = {"cy_net": 0, "py_net": 0}
            adjustments[bs_code]["cy_net"] += r.cy_amount or 0
            adjustments[bs_code]["py_net"] += r.py_amount or 0

        # PL side: Closing stock is a credit (reduces expense = negative in Dr-Cr)
        if pl_code:
            if pl_code not in adjustments:
                adjustments[pl_code] = {"cy_net": 0, "py_net": 0}
            adjustments[pl_code]["cy_net"] -= r.cy_amount or 0  # Credit = negative
            adjustments[pl_code]["py_net"] -= r.py_amount or 0

    return adjustments
