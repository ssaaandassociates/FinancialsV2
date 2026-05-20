"""
Financial Engine
Generates Balance Sheet and Profit & Loss statement from mapped Trial Balance,
applying audit adjustments and retained earnings auto-balance.
"""
from sqlalchemy.orm import Session
from collections import defaultdict
from app.models import TrialBalance, CoAMaster, Project
from app.services.audit_service import get_audit_adjustments_by_code
from app.core.constants import get_sign, ROUNDING
from app.core.fs_structure import BS_STRUCTURE, PL_STRUCTURE


def get_adjusted_balances(db: Session, project_id: int,
                          approved_only: bool = True) -> dict:
    """
    Returns dict: coa_code -> {"cy_net": X, "py_net": Y}
    where CY Net = Raw TB Net + Audit Adjustments + Closing Stock Adjustments
    """
    # Get all TB rows grouped by CoA code
    tb_rows = db.query(TrialBalance).filter(
        TrialBalance.project_id == project_id
    ).all()

    balances = defaultdict(lambda: {"cy_net": 0.0, "py_net": 0.0})
    for r in tb_rows:
        code = r.coa_code or "UNMAPPED"
        balances[code]["cy_net"] += (r.cy_debit or 0) - (r.cy_credit or 0)
        balances[code]["py_net"] += (r.py_debit or 0) - (r.py_credit or 0)

    # Apply audit adjustments to CY (not PY - PY is already closed)
    adjustments = get_audit_adjustments_by_code(db, project_id, approved_only=approved_only)
    for code, adj in adjustments.items():
        balances[code]["cy_net"] += adj["debit"] - adj["credit"]

    # Apply closing stock adjustments (manual input, not in TB)
    from app.services.closing_stock_service import get_closing_stock_adjustments
    cs_adj = get_closing_stock_adjustments(db, project_id)
    for code, vals in cs_adj.items():
        balances[code]["cy_net"] += vals["cy_net"]
        balances[code]["py_net"] += vals["py_net"]

    return dict(balances)


def sum_by_prefix(balances: dict, prefix: str) -> tuple[float, float]:
    """Sum cy_net and py_net for all codes starting with prefix."""
    cy_total = 0.0
    py_total = 0.0
    for code, vals in balances.items():
        if code.startswith(prefix):
            cy_total += vals["cy_net"]
            py_total += vals["py_net"]
    return cy_total, py_total


def generate_pl(db: Session, project_id: int) -> dict:
    """
    Generate P&L statement as a structured dict.
    Returns: {line_items: [...], pat_cy: X, pat_py: Y}
    """
    balances = get_adjusted_balances(db, project_id)

    # Revenue - negate (Cr in TB = negative Dr-Cr)
    rev_cy, rev_py = sum_by_prefix(balances, "PL-01")
    rev_cy, rev_py = -rev_cy, -rev_py

    # Other Income - negate
    oi_cy, oi_py = sum_by_prefix(balances, "PL-02")
    oi_cy, oi_py = -oi_cy, -oi_py

    # Total Revenue
    total_revenue_cy = rev_cy + oi_cy
    total_revenue_py = rev_py + oi_py

    # Expenses (Dr in TB = positive)
    cost_materials_cy, cost_materials_py = sum_by_prefix(balances, "PL-04-01")
    purchases_sit_cy, purchases_sit_py = sum_by_prefix(balances, "PL-04-02")
    changes_inv_cy, changes_inv_py = sum_by_prefix(balances, "PL-04-03")
    emp_cy, emp_py = sum_by_prefix(balances, "PL-04-04")
    fin_cy, fin_py = sum_by_prefix(balances, "PL-04-05")
    dep_cy, dep_py = sum_by_prefix(balances, "PL-04-06")
    oe_cy, oe_py = sum_by_prefix(balances, "PL-04-07")

    total_expenses_cy = (cost_materials_cy + purchases_sit_cy + changes_inv_cy
                         + emp_cy + fin_cy + dep_cy + oe_cy)
    total_expenses_py = (cost_materials_py + purchases_sit_py + changes_inv_py
                         + emp_py + fin_py + dep_py + oe_py)

    # Profit before exceptional/extraordinary/tax
    pbt_ex_cy = total_revenue_cy - total_expenses_cy
    pbt_ex_py = total_revenue_py - total_expenses_py

    # Exceptional & Extraordinary
    exc_cy, exc_py = sum_by_prefix(balances, "PL-06")
    extra_cy, extra_py = sum_by_prefix(balances, "PL-08")

    pbt_eo_cy = pbt_ex_cy - exc_cy
    pbt_eo_py = pbt_ex_py - exc_py

    pbt_cy = pbt_eo_cy - extra_cy
    pbt_py = pbt_eo_py - extra_py

    # Tax
    current_tax_cy = balances.get("PL-10-01", {}).get("cy_net", 0)
    current_tax_py = balances.get("PL-10-01", {}).get("py_net", 0)
    deferred_tax_cy = balances.get("PL-10-02", {}).get("cy_net", 0)
    deferred_tax_py = balances.get("PL-10-02", {}).get("py_net", 0)
    mat_credit_cy = -balances.get("PL-10-03", {}).get("cy_net", 0)  # negate Cr
    mat_credit_py = -balances.get("PL-10-03", {}).get("py_net", 0)

    total_tax_cy = current_tax_cy + deferred_tax_cy - mat_credit_cy
    total_tax_py = current_tax_py + deferred_tax_py - mat_credit_py

    # PAT
    pat_cy = pbt_cy - total_tax_cy
    pat_py = pbt_py - total_tax_py

    line_items = [
        ("I", "Revenue from Operations", "Rev", rev_cy, rev_py, 2, False),
        ("II", "Other Income", "OI", oi_cy, oi_py, 2, False),
        ("III", "Total Revenue (I + II)", "", total_revenue_cy, total_revenue_py, 1, True),
        ("IV", "Expenses:", "", None, None, 1, False),
        ("", "  Cost of Materials Consumed", "Exp", cost_materials_cy, cost_materials_py, 3, False),
        ("", "  Purchases of Stock-in-Trade", "Exp", purchases_sit_cy, purchases_sit_py, 3, False),
        ("", "  Changes in Inventories", "", changes_inv_cy, changes_inv_py, 3, False),
        ("", "  Employee Benefits Expense", "Emp", emp_cy, emp_py, 3, False),
        ("", "  Finance Costs", "Fin", fin_cy, fin_py, 3, False),
        ("", "  Depreciation & Amortization", "Dep", dep_cy, dep_py, 3, False),
        ("", "  Other Expenses", "OE", oe_cy, oe_py, 3, False),
        ("", "  Total Expenses (IV)", "", total_expenses_cy, total_expenses_py, 1, True),
        ("V", "PBT before Exceptional & Extraordinary (III-IV)", "", pbt_ex_cy, pbt_ex_py, 1, True),
        ("VI", "Exceptional Items", "", exc_cy, exc_py, 2, False),
        ("VII", "PBT before Extraordinary (V-VI)", "", pbt_eo_cy, pbt_eo_py, 1, True),
        ("VIII", "Extraordinary Items", "", extra_cy, extra_py, 2, False),
        ("IX", "Profit Before Tax (VII-VIII)", "", pbt_cy, pbt_py, 1, True),
        ("X", "Tax Expense:", "", None, None, 2, False),
        ("", "  Current Tax", "Tax", current_tax_cy, current_tax_py, 3, False),
        ("", "  Deferred Tax", "Tax", deferred_tax_cy, deferred_tax_py, 3, False),
        ("", "  MAT Credit Entitlement", "Tax", -mat_credit_cy, -mat_credit_py, 3, False),
        ("XI", "Profit for the Period", "", pat_cy, pat_py, 1, True),
    ]

    return {
        "line_items": line_items,
        "pat_cy": pat_cy,
        "pat_py": pat_py,
        "total_revenue_cy": total_revenue_cy,
        "total_revenue_py": total_revenue_py,
        "total_expenses_cy": total_expenses_cy,
        "total_expenses_py": total_expenses_py,
    }


def generate_bs(db: Session, project_id: int,
                auto_retained_earnings: bool = True) -> dict:
    """
    Generate Balance Sheet. Auto-adjusts retained earnings with current year profit.
    Returns: {line_items: [...], total_el_cy, total_as_cy, is_balanced}
    """
    balances = get_adjusted_balances(db, project_id)

    # Auto-add CY profit to Retained Earnings (BS-EL-01-02-09)
    if auto_retained_earnings:
        pl = generate_pl(db, project_id)
        pat_cy = pl["pat_cy"]
        # Profit is a credit to retained earnings → negative in Dr-Cr convention
        if "BS-EL-01-02-09" not in balances:
            balances["BS-EL-01-02-09"] = {"cy_net": 0, "py_net": 0}
        balances["BS-EL-01-02-09"]["cy_net"] -= pat_cy

    line_items = []

    # EQUITY AND LIABILITIES
    line_items.append(("", "EQUITY AND LIABILITIES", "", None, None, 1, False))

    # 1. Shareholders' Funds
    sc_cy, sc_py = sum_by_prefix(balances, "BS-EL-01-01")
    sc_cy, sc_py = -sc_cy, -sc_py  # Liability: negate
    reserves_cy, reserves_py = sum_by_prefix(balances, "BS-EL-01-02")
    reserves_cy, reserves_py = -reserves_cy, -reserves_py
    mw_cy, mw_py = sum_by_prefix(balances, "BS-EL-01-03")
    mw_cy, mw_py = -mw_cy, -mw_py
    shf_cy = sc_cy + reserves_cy + mw_cy
    shf_py = sc_py + reserves_py + mw_py

    line_items.append(("1.", "Shareholders' Funds", "", shf_cy, shf_py, 2, True))
    line_items.append(("(a)", "Share Capital", "A", sc_cy, sc_py, 3, False))
    line_items.append(("(b)", "Reserves and Surplus", "B", reserves_cy, reserves_py, 3, False))
    line_items.append(("(c)", "Money Against Share Warrants", "", mw_cy, mw_py, 3, False))

    # 2. Share Application Money
    sam_cy, sam_py = sum_by_prefix(balances, "BS-EL-02")
    sam_cy, sam_py = -sam_cy, -sam_py
    line_items.append(("2.", "Share Application Money Pending Allotment", "", sam_cy, sam_py, 2, False))

    # 3. Non-Current Liabilities
    ltb_cy, ltb_py = sum_by_prefix(balances, "BS-EL-03-01")
    ltb_cy, ltb_py = -ltb_cy, -ltb_py
    dtl_cy, dtl_py = sum_by_prefix(balances, "BS-EL-03-02")
    dtl_cy, dtl_py = -dtl_cy, -dtl_py
    ol_cy, ol_py = sum_by_prefix(balances, "BS-EL-03-03")
    ol_cy, ol_py = -ol_cy, -ol_py
    ltp_cy, ltp_py = sum_by_prefix(balances, "BS-EL-03-04")
    ltp_cy, ltp_py = -ltp_cy, -ltp_py
    ncl_cy = ltb_cy + dtl_cy + ol_cy + ltp_cy
    ncl_py = ltb_py + dtl_py + ol_py + ltp_py

    line_items.append(("3.", "Non-Current Liabilities", "", ncl_cy, ncl_py, 2, True))
    line_items.append(("(a)", "Long-Term Borrowings", "C", ltb_cy, ltb_py, 3, False))
    line_items.append(("(b)", "Deferred Tax Liabilities (Net)", "", dtl_cy, dtl_py, 3, False))
    line_items.append(("(c)", "Other Long-Term Liabilities", "D", ol_cy, ol_py, 3, False))
    line_items.append(("(d)", "Long-Term Provisions", "E", ltp_cy, ltp_py, 3, False))

    # 4. Current Liabilities
    stb_cy, stb_py = sum_by_prefix(balances, "BS-EL-04-01")
    stb_cy, stb_py = -stb_cy, -stb_py
    tp_cy, tp_py = sum_by_prefix(balances, "BS-EL-04-02")
    tp_cy, tp_py = -tp_cy, -tp_py
    ocl_cy, ocl_py = sum_by_prefix(balances, "BS-EL-04-03")
    ocl_cy, ocl_py = -ocl_cy, -ocl_py
    stp_cy, stp_py = sum_by_prefix(balances, "BS-EL-04-04")
    stp_cy, stp_py = -stp_cy, -stp_py
    cl_cy = stb_cy + tp_cy + ocl_cy + stp_cy
    cl_py = stb_py + tp_py + ocl_py + stp_py

    line_items.append(("4.", "Current Liabilities", "", cl_cy, cl_py, 2, True))
    line_items.append(("(a)", "Short-Term Borrowings", "F", stb_cy, stb_py, 3, False))
    line_items.append(("(b)", "Trade Payables", "FA", tp_cy, tp_py, 3, False))
    line_items.append(("(c)", "Other Current Liabilities", "G", ocl_cy, ocl_py, 3, False))
    line_items.append(("(d)", "Short-Term Provisions", "H", stp_cy, stp_py, 3, False))

    total_el_cy = shf_cy + sam_cy + ncl_cy + cl_cy
    total_el_py = shf_py + sam_py + ncl_py + cl_py
    line_items.append(("", "TOTAL EQUITY & LIABILITIES", "", total_el_cy, total_el_py, 1, True))

    # ASSETS
    line_items.append(("", "ASSETS", "", None, None, 1, False))

    # 1. Non-Current Assets
    tang_cy, tang_py = 0.0, 0.0
    for idx in range(1, 10):  # BS-AS-01-01-01 to -09 (Tangible)
        code = f"BS-AS-01-01-{idx:02d}"
        if code in balances:
            tang_cy += balances[code]["cy_net"]
            tang_py += balances[code]["py_net"]
    intang_cy, intang_py = 0.0, 0.0
    for idx in range(10, 15):  # 10-14 Intangible
        code = f"BS-AS-01-01-{idx:02d}"
        if code in balances:
            intang_cy += balances[code]["cy_net"]
            intang_py += balances[code]["py_net"]
    cwip_cy = balances.get("BS-AS-01-01-15", {}).get("cy_net", 0)
    cwip_py = balances.get("BS-AS-01-01-15", {}).get("py_net", 0)
    iud_cy = balances.get("BS-AS-01-01-16", {}).get("cy_net", 0)
    iud_py = balances.get("BS-AS-01-01-16", {}).get("py_net", 0)

    nci_cy, nci_py = sum_by_prefix(balances, "BS-AS-01-02")
    dta_cy, dta_py = sum_by_prefix(balances, "BS-AS-01-03")
    ltla_cy, ltla_py = sum_by_prefix(balances, "BS-AS-01-04")
    oca_cy, oca_py = sum_by_prefix(balances, "BS-AS-01-05")

    nca_cy = tang_cy + intang_cy + cwip_cy + iud_cy + nci_cy + dta_cy + ltla_cy + oca_cy
    nca_py = tang_py + intang_py + cwip_py + iud_py + nci_py + dta_py + ltla_py + oca_py

    line_items.append(("1.", "Non-Current Assets", "", nca_cy, nca_py, 2, True))
    line_items.append(("(a)", "Property, Plant and Equipment", "", None, None, 3, False))
    line_items.append(("", "  (i) Tangible Assets", "I", tang_cy, tang_py, 4, False))
    line_items.append(("", "  (ii) Intangible Assets", "J", intang_cy, intang_py, 4, False))
    line_items.append(("", "  (iii) Capital Work-in-Progress", "", cwip_cy, cwip_py, 4, False))
    line_items.append(("", "  (iv) Intangible Under Development", "", iud_cy, iud_py, 4, False))
    line_items.append(("(b)", "Non-Current Investments", "K", nci_cy, nci_py, 3, False))
    line_items.append(("(c)", "Deferred Tax Assets (Net)", "", dta_cy, dta_py, 3, False))
    line_items.append(("(d)", "Long-Term Loans & Advances", "L", ltla_cy, ltla_py, 3, False))
    line_items.append(("(e)", "Other Non-Current Assets", "M", oca_cy, oca_py, 3, False))

    # 2. Current Assets
    ci_cy, ci_py = sum_by_prefix(balances, "BS-AS-02-01")
    inv_cy, inv_py = sum_by_prefix(balances, "BS-AS-02-02")
    tr_cy, tr_py = sum_by_prefix(balances, "BS-AS-02-03")
    cash_cy, cash_py = sum_by_prefix(balances, "BS-AS-02-04")
    stla_cy, stla_py = sum_by_prefix(balances, "BS-AS-02-05")
    oc_cy, oc_py = sum_by_prefix(balances, "BS-AS-02-06")

    ca_cy = ci_cy + inv_cy + tr_cy + cash_cy + stla_cy + oc_cy
    ca_py = ci_py + inv_py + tr_py + cash_py + stla_py + oc_py

    line_items.append(("2.", "Current Assets", "", ca_cy, ca_py, 2, True))
    line_items.append(("(a)", "Current Investments", "N", ci_cy, ci_py, 3, False))
    line_items.append(("(b)", "Inventories", "O", inv_cy, inv_py, 3, False))
    line_items.append(("(c)", "Trade Receivables", "P", tr_cy, tr_py, 3, False))
    line_items.append(("(d)", "Cash and Cash Equivalents", "Q", cash_cy, cash_py, 3, False))
    line_items.append(("(e)", "Short-Term Loans & Advances", "R", stla_cy, stla_py, 3, False))
    line_items.append(("(f)", "Other Current Assets", "S", oc_cy, oc_py, 3, False))

    total_as_cy = nca_cy + ca_cy
    total_as_py = nca_py + ca_py
    line_items.append(("", "TOTAL ASSETS", "", total_as_cy, total_as_py, 1, True))

    is_balanced_cy = abs(total_el_cy - total_as_cy) < 1.0
    is_balanced_py = abs(total_el_py - total_as_py) < 1.0

    return {
        "line_items": line_items,
        "total_el_cy": total_el_cy,
        "total_el_py": total_el_py,
        "total_as_cy": total_as_cy,
        "total_as_py": total_as_py,
        "difference_cy": round(total_as_cy - total_el_cy, 2),
        "difference_py": round(total_as_py - total_el_py, 2),
        "is_balanced_cy": is_balanced_cy,
        "is_balanced_py": is_balanced_py,
    }


def apply_rounding(value: float, rounding: str) -> float:
    """Apply rounding per project setting."""
    divisor = ROUNDING.get(rounding, 1)
    return round(value / divisor, 2) if divisor > 1 else round(value, 2)
