"""
Notes Engine
Generates all Note schedules (A through S for BS, plus PL notes)
with sub-line item detail pulled from mapped TB + audit adjustments.
"""
from sqlalchemy.orm import Session
from app.models import CoAMaster
from app.services.financial_engine import get_adjusted_balances, sum_by_prefix


def _get_coa_details(db: Session, codes: list[str]) -> dict:
    """Return dict: code → particulars"""
    coa_rows = db.query(CoAMaster).filter(CoAMaster.code.in_(codes)).all()
    return {c.code: c.particulars for c in coa_rows}


def _build_note(db: Session, balances: dict, items: list[tuple],
                sign_multiplier: int = 1) -> dict:
    """
    Build a note with sub-line items.
    items = list of (sno, label, code) tuples
    sign_multiplier = 1 for Assets, -1 for Liabilities/Income
    """
    line_items = []
    total_cy = 0.0
    total_py = 0.0

    for sno, label, code in items:
        if code:
            cy = balances.get(code, {}).get("cy_net", 0) * sign_multiplier
            py = balances.get(code, {}).get("py_net", 0) * sign_multiplier
        else:
            cy = 0
            py = 0
        line_items.append({
            "sno": sno,
            "particulars": label,
            "coa_code": code,
            "cy_amount": round(cy, 2),
            "py_amount": round(py, 2),
        })
        total_cy += cy
        total_py += py

    return {
        "items": line_items,
        "total_cy": round(total_cy, 2),
        "total_py": round(total_py, 2),
    }


def generate_note_a_share_capital(db: Session, balances: dict) -> dict:
    """Note A: Share Capital"""
    items = [
        ("(a)", "Equity Share Capital - Authorised", "BS-EL-01-01-01"),
        ("", "Preference Share Capital - Authorised", "BS-EL-01-01-04"),
        ("(b)", "Equity Share Capital - Issued & Paid Up", "BS-EL-01-01-02"),
        ("", "Preference Share Capital - Issued & Paid Up", "BS-EL-01-01-05"),
        ("", "Equity Share Capital - Subscribed Not Paid", "BS-EL-01-01-03"),
        ("(k)", "Less: Calls Unpaid", "BS-EL-01-01-06"),
        ("(l)", "Add: Forfeited Shares", "BS-EL-01-01-07"),
    ]
    return _build_note(db, balances, items, sign_multiplier=-1)


def generate_note_b_reserves(db: Session, balances: dict) -> dict:
    """Note B: Reserves and Surplus"""
    items = [
        ("(a)", "Capital Reserves", "BS-EL-01-02-01"),
        ("(b)", "Capital Redemption Reserve", "BS-EL-01-02-02"),
        ("(c)", "Securities Premium", "BS-EL-01-02-03"),
        ("(d)", "Debenture Redemption Reserve", "BS-EL-01-02-04"),
        ("(e)", "Revaluation Reserve", "BS-EL-01-02-05"),
        ("(f)", "Share Options Outstanding Account", "BS-EL-01-02-06"),
        ("(g)", "General Reserve", "BS-EL-01-02-07"),
        ("", "Other Reserves (Specify)", "BS-EL-01-02-08"),
        ("(h)", "Surplus - Balance in P&L", "BS-EL-01-02-09"),
    ]
    return _build_note(db, balances, items, sign_multiplier=-1)


def generate_note_c_lt_borrowings(db: Session, balances: dict) -> dict:
    """Note C: Long-Term Borrowings"""
    items = [
        ("(a)", "Bonds/Debentures - Secured", "BS-EL-03-01-01"),
        ("", "Bonds/Debentures - Unsecured", "BS-EL-03-01-02"),
        ("(b)", "Term Loans from Banks - Secured", "BS-EL-03-01-03"),
        ("", "Term Loans from Banks - Unsecured", "BS-EL-03-01-04"),
        ("", "Term Loans from Others - Secured", "BS-EL-03-01-05"),
        ("", "Term Loans from Others - Unsecured", "BS-EL-03-01-06"),
        ("(c)", "Deferred Payment Liabilities", "BS-EL-03-01-07"),
        ("(d)", "Deposits", "BS-EL-03-01-08"),
        ("(e)", "Loans from Related Parties", "BS-EL-03-01-09"),
        ("(f)", "Finance Lease Obligations", "BS-EL-03-01-10"),
        ("(g)", "Other Loans & Advances", "BS-EL-03-01-11"),
    ]
    return _build_note(db, balances, items, sign_multiplier=-1)


def generate_note_d_other_lt_liab(db: Session, balances: dict) -> dict:
    items = [
        ("(a)", "Trade Payables (LT)", "BS-EL-03-03-01"),
        ("(b)", "Others", "BS-EL-03-03-02"),
    ]
    return _build_note(db, balances, items, sign_multiplier=-1)


def generate_note_e_lt_provisions(db: Session, balances: dict) -> dict:
    items = [
        ("(a)", "Employee Benefits (LT)", "BS-EL-03-04-01"),
        ("(b)", "Other LT Provisions", "BS-EL-03-04-02"),
    ]
    return _build_note(db, balances, items, sign_multiplier=-1)


def generate_note_f_st_borrowings(db: Session, balances: dict) -> dict:
    """Note F: Short-Term Borrowings"""
    items = [
        ("(a)", "Loans on Demand - Banks (Secured)", "BS-EL-04-01-01"),
        ("", "Loans on Demand - Banks (Unsecured)", "BS-EL-04-01-02"),
        ("", "Loans on Demand - Others (Secured)", "BS-EL-04-01-03"),
        ("", "Loans on Demand - Others (Unsecured)", "BS-EL-04-01-04"),
        ("(b)", "Loans from Related Parties", "BS-EL-04-01-05"),
        ("(c)", "Deposits", "BS-EL-04-01-06"),
        ("(d)", "Other Short-Term Loans", "BS-EL-04-01-07"),
    ]
    return _build_note(db, balances, items, sign_multiplier=-1)


def generate_note_fa_trade_payables(db: Session, balances: dict) -> dict:
    """Note FA: Trade Payables with MSME/Others split and ageing"""
    msme_cy, msme_py = 0, 0
    oth_cy, oth_py = 0, 0
    for suffix in ['01', '02', '03', '04', '09', '10', '11', '12']:
        code = f"BS-EL-04-02-{suffix}"
        msme_cy += balances.get(code, {}).get("cy_net", 0)
        msme_py += balances.get(code, {}).get("py_net", 0)
    for suffix in ['05', '06', '07', '08', '13', '14', '15', '16']:
        code = f"BS-EL-04-02-{suffix}"
        oth_cy += balances.get(code, {}).get("cy_net", 0)
        oth_py += balances.get(code, {}).get("py_net", 0)
    unbilled_cy = balances.get("BS-EL-04-02-17", {}).get("cy_net", 0)
    unbilled_py = balances.get("BS-EL-04-02-17", {}).get("py_net", 0)

    items = [
        ("(A)", "Total MSME", -msme_cy, -msme_py),
        ("(B)", "Total Others", -oth_cy, -oth_py),
        ("(C)", "Unbilled Dues", -unbilled_cy, -unbilled_py),
    ]
    line_items = [
        {"sno": s, "particulars": p, "cy_amount": round(cy, 2), "py_amount": round(py, 2)}
        for s, p, cy, py in items
    ]
    total_cy = sum(x["cy_amount"] for x in line_items)
    total_py = sum(x["py_amount"] for x in line_items)
    return {"items": line_items, "total_cy": total_cy, "total_py": total_py}


def generate_note_g_other_current_liab(db: Session, balances: dict) -> dict:
    items = [
        ("(a)", "Current Maturities of LT Debt", "BS-EL-04-03-01"),
        ("(b)", "Current Maturities of Finance Lease", "BS-EL-04-03-02"),
        ("(c)", "Interest Accrued but Not Due", "BS-EL-04-03-03"),
        ("(d)", "Interest Accrued and Due", "BS-EL-04-03-04"),
        ("(e)", "Income Received in Advance", "BS-EL-04-03-05"),
        ("(f)", "Unpaid Dividends", "BS-EL-04-03-06"),
        ("(g)", "Share Appln Money Refundable", "BS-EL-04-03-07"),
        ("(h)", "Unpaid Matured Deposits & Int.", "BS-EL-04-03-08"),
        ("(i)", "Unpaid Matured Debentures & Int.", "BS-EL-04-03-09"),
        ("(j)", "Statutory Dues Payable", "BS-EL-04-03-10"),
        ("", "Other Payables", "BS-EL-04-03-11"),
    ]
    return _build_note(db, balances, items, sign_multiplier=-1)


def generate_note_h_st_provisions(db: Session, balances: dict) -> dict:
    items = [
        ("(a)", "Employee Benefits (ST)", "BS-EL-04-04-01"),
        ("(b)", "Provision for Income Tax", "BS-EL-04-04-02"),
        ("", "Proposed Dividend", "BS-EL-04-04-03"),
        ("", "Tax on Proposed Dividend", "BS-EL-04-04-04"),
        ("", "Other ST Provisions", "BS-EL-04-04-05"),
    ]
    return _build_note(db, balances, items, sign_multiplier=-1)


def generate_note_i_tangible(db: Session, balances: dict) -> dict:
    """Note I: Tangible Assets"""
    items = [
        ("(a)", "Land (Freehold)", "BS-AS-01-01-01"),
        ("", "Land (Leasehold)", "BS-AS-01-01-02"),
        ("(b)", "Buildings", "BS-AS-01-01-03"),
        ("(c)", "Plant and Equipment", "BS-AS-01-01-04"),
        ("(d)", "Furniture and Fixtures", "BS-AS-01-01-05"),
        ("(e)", "Vehicles", "BS-AS-01-01-06"),
        ("(f)", "Office Equipment", "BS-AS-01-01-07"),
        ("", "Computers", "BS-AS-01-01-08"),
        ("(g)", "Other Tangible Assets", "BS-AS-01-01-09"),
    ]
    return _build_note(db, balances, items, sign_multiplier=1)


def generate_note_j_intangible(db: Session, balances: dict) -> dict:
    items = [
        ("(a)", "Goodwill", "BS-AS-01-01-10"),
        ("(b)", "Brands / Trademarks", "BS-AS-01-01-12"),
        ("(c)", "Computer Software", "BS-AS-01-01-11"),
        ("(f)", "Copyrights / Patents / IP", "BS-AS-01-01-13"),
        ("(i)", "Other Intangible Assets", "BS-AS-01-01-14"),
    ]
    return _build_note(db, balances, items, sign_multiplier=1)


def generate_note_k_nc_investments(db: Session, balances: dict) -> dict:
    items = [
        ("(a)", "Investment Property", "BS-AS-01-02-01"),
        ("(b)", "Equity Instruments", "BS-AS-01-02-02"),
        ("(c)", "Preference Shares", "BS-AS-01-02-03"),
        ("(d)", "Govt/Trust Securities", "BS-AS-01-02-04"),
        ("(e)", "Debentures/Bonds", "BS-AS-01-02-05"),
        ("(f)", "Mutual Funds", "BS-AS-01-02-06"),
        ("(g)", "Partnership Firms", "BS-AS-01-02-07"),
        ("(h)", "Other Investments", "BS-AS-01-02-08"),
    ]
    return _build_note(db, balances, items, sign_multiplier=1)


def generate_note_l_lt_loans(db: Session, balances: dict) -> dict:
    items = [
        ("(a)", "Capital Advances", "BS-AS-01-04-01"),
        ("(b)", "Security Deposits", "BS-AS-01-04-02"),
        ("(c)", "Loans to Related Parties", "BS-AS-01-04-03"),
        ("(d)", "Other LT Loans & Advances", "BS-AS-01-04-04"),
    ]
    return _build_note(db, balances, items, sign_multiplier=1)


def generate_note_m_other_nc_assets(db: Session, balances: dict) -> dict:
    items = [
        ("(i)", "Long-Term Trade Receivables", "BS-AS-01-05-01"),
        ("(ii)", "Other Non-Current Assets", "BS-AS-01-05-02"),
    ]
    return _build_note(db, balances, items, sign_multiplier=1)


def generate_note_n_current_investments(db: Session, balances: dict) -> dict:
    items = [
        ("(a)", "Equity Instruments (Current)", "BS-AS-02-01-01"),
        ("(e)", "Mutual Funds (Current)", "BS-AS-02-01-02"),
        ("(g)", "Other Current Investments", "BS-AS-02-01-03"),
    ]
    return _build_note(db, balances, items, sign_multiplier=1)


def generate_note_o_inventories(db: Session, balances: dict) -> dict:
    items = [
        ("(a)", "Raw Materials", "BS-AS-02-02-01"),
        ("(b)", "Work-in-Progress", "BS-AS-02-02-02"),
        ("(c)", "Finished Goods", "BS-AS-02-02-03"),
        ("(d)", "Stock-in-Trade", "BS-AS-02-02-04"),
        ("(e)", "Stores and Spares", "BS-AS-02-02-05"),
        ("(f)", "Loose Tools", "BS-AS-02-02-06"),
    ]
    return _build_note(db, balances, items, sign_multiplier=1)


def generate_note_p_trade_receivables(db: Session, balances: dict) -> dict:
    """Note P: Trade Receivables with ageing (aggregated for note, detailed in ageing schedule)"""
    undisp_good_cy, undisp_good_py = 0, 0
    for suffix in ['01', '02', '03', '04', '05']:
        code = f"BS-AS-02-03-{suffix}"
        undisp_good_cy += balances.get(code, {}).get("cy_net", 0)
        undisp_good_py += balances.get(code, {}).get("py_net", 0)

    undisp_doubt_cy, undisp_doubt_py = 0, 0
    for suffix in ['06', '07', '08', '09', '10']:
        code = f"BS-AS-02-03-{suffix}"
        undisp_doubt_cy += balances.get(code, {}).get("cy_net", 0)
        undisp_doubt_py += balances.get(code, {}).get("py_net", 0)

    disp_good_cy, disp_good_py = 0, 0
    for suffix in ['11', '12', '13', '14', '15']:
        code = f"BS-AS-02-03-{suffix}"
        disp_good_cy += balances.get(code, {}).get("cy_net", 0)
        disp_good_py += balances.get(code, {}).get("py_net", 0)

    disp_doubt_cy, disp_doubt_py = 0, 0
    for suffix in ['16', '17', '18', '19', '20']:
        code = f"BS-AS-02-03-{suffix}"
        disp_doubt_cy += balances.get(code, {}).get("cy_net", 0)
        disp_doubt_py += balances.get(code, {}).get("py_net", 0)

    others_cy = balances.get("BS-AS-02-03-21", {}).get("cy_net", 0)
    others_py = balances.get("BS-AS-02-03-21", {}).get("py_net", 0)
    allowance_cy = balances.get("BS-AS-02-03-22", {}).get("cy_net", 0)
    allowance_py = balances.get("BS-AS-02-03-22", {}).get("py_net", 0)

    items_data = [
        ("(a)", "Undisputed - Considered Good", undisp_good_cy, undisp_good_py),
        ("", "Undisputed - Considered Doubtful", undisp_doubt_cy, undisp_doubt_py),
        ("(b)", "Disputed - Considered Good", disp_good_cy, disp_good_py),
        ("", "Disputed - Considered Doubtful", disp_doubt_cy, disp_doubt_py),
        ("(c)", "Others", others_cy, others_py),
        ("", "Less: Allowance for Bad & Doubtful Debts", allowance_cy, allowance_py),
    ]
    line_items = [
        {"sno": s, "particulars": p, "cy_amount": round(cy, 2), "py_amount": round(py, 2)}
        for s, p, cy, py in items_data
    ]
    total_cy = sum(x["cy_amount"] for x in line_items)
    total_py = sum(x["py_amount"] for x in line_items)
    return {"items": line_items, "total_cy": total_cy, "total_py": total_py}


def generate_note_q_cash(db: Session, balances: dict) -> dict:
    items = [
        ("(a)", "Bank - Current Accounts", "BS-AS-02-04-01"),
        ("", "Bank - Deposits (<12 Months)", "BS-AS-02-04-02"),
        ("(v)", "Bank - Deposits (>12 Months)", "BS-AS-02-04-03"),
        ("(ii)", "Bank - Earmarked (Unpaid Dividend)", "BS-AS-02-04-04"),
        ("(iii)", "Bank - Margin Money/Security", "BS-AS-02-04-05"),
        ("(b)", "Cheques / Drafts on Hand", "BS-AS-02-04-06"),
        ("(c)", "Cash on Hand", "BS-AS-02-04-07"),
    ]
    return _build_note(db, balances, items, sign_multiplier=1)


def generate_note_r_st_loans(db: Session, balances: dict) -> dict:
    items = [
        ("(a)", "Loans to Related Parties (ST)", "BS-AS-02-05-01"),
        ("", "Secured, Considered Good", "BS-AS-02-05-02"),
        ("(b)", "Unsecured, Considered Good", "BS-AS-02-05-03"),
        ("", "Doubtful", "BS-AS-02-05-04"),
        ("(iii)", "Less: Allowance for Bad Advances", "BS-AS-02-05-05"),
        ("", "Advance Income Tax / TDS", "BS-AS-02-05-06"),
        ("", "GST Input / Govt Balances", "BS-AS-02-05-07"),
        ("", "Prepaid Expenses", "BS-AS-02-05-08"),
        ("", "Advance to Suppliers", "BS-AS-02-05-09"),
    ]
    return _build_note(db, balances, items, sign_multiplier=1)


def generate_note_s_other_current(db: Session, balances: dict) -> dict:
    items = [
        ("", "Accrued Income / Interest Receivable", "BS-AS-02-06-01"),
        ("", "Other Current Assets", "BS-AS-02-06-02"),
    ]
    return _build_note(db, balances, items, sign_multiplier=1)


# ---------- P&L NOTES ----------

def generate_note_rev(db: Session, balances: dict) -> dict:
    """Note: Revenue from Operations"""
    items = [
        ("(a)", "Sale of Products - Manufactured", "PL-01-01"),
        ("", "Sale of Products - Traded", "PL-01-02"),
        ("(b)", "Sale of Services", "PL-01-03"),
        ("(c)", "Other Operating Revenue", "PL-01-04"),
    ]
    return _build_note(db, balances, items, sign_multiplier=-1)


def generate_note_oi(db: Session, balances: dict) -> dict:
    """Note: Other Income"""
    items = [
        ("(a)", "Interest Income - Fixed Deposits", "PL-02-01"),
        ("", "Interest Income - Others", "PL-02-02"),
        ("(b)", "Dividend Income", "PL-02-03"),
        ("(c)", "Gain on Sale of Investments", "PL-02-04"),
        ("(d)", "Profit on Sale of Fixed Assets", "PL-02-05"),
        ("", "Rent Received", "PL-02-06"),
        ("", "Bad Debts Recovered", "PL-02-07"),
        ("", "Liabilities Written Back", "PL-02-08"),
        ("", "Foreign Exchange Gain", "PL-02-09"),
        ("", "Miscellaneous Income", "PL-02-10"),
    ]
    return _build_note(db, balances, items, sign_multiplier=-1)


def generate_note_emp(db: Session, balances: dict) -> dict:
    items = [
        ("(i)", "Salaries and Wages", "PL-04-04-01"),
        ("(ii)", "Contribution to PF & Other Funds", "PL-04-04-02"),
        ("(iii)", "ESOP / ESPP Expense", "PL-04-04-03"),
        ("", "Gratuity Expense", "PL-04-04-04"),
        ("(iv)", "Staff Welfare Expenses", "PL-04-04-05"),
        ("", "Directors' Remuneration", "PL-04-04-06"),
    ]
    return _build_note(db, balances, items, sign_multiplier=1)


def generate_note_fin(db: Session, balances: dict) -> dict:
    items = [
        ("(a)", "Interest Expense on Borrowings", "PL-04-05-01"),
        ("(b)", "Other Borrowing Costs", "PL-04-05-02"),
        ("(c)", "Forex Loss on Borrowings", "PL-04-05-03"),
    ]
    return _build_note(db, balances, items, sign_multiplier=1)


def generate_note_dep(db: Session, balances: dict) -> dict:
    items = [
        ("(a)", "Depreciation on Tangible Assets", "PL-04-06-01"),
        ("(b)", "Amortization of Intangible Assets", "PL-04-06-02"),
    ]
    return _build_note(db, balances, items, sign_multiplier=1)


def generate_note_oe(db: Session, balances: dict) -> dict:
    """Note: Other Expenses - all 27 sub-items"""
    items = [
        ("(a)", "Consumption of Stores & Spares", "PL-04-07-01"),
        ("(b)", "Power and Fuel", "PL-04-07-02"),
        ("(c)", "Rent", "PL-04-07-03"),
        ("(d)", "Repairs to Buildings", "PL-04-07-04"),
        ("(e)", "Repairs to Machinery", "PL-04-07-05"),
        ("(f)", "Insurance", "PL-04-07-06"),
        ("(g)", "Rates & Taxes (Excl. IT)", "PL-04-07-07"),
        ("", "Communication Expenses", "PL-04-07-08"),
        ("", "Travelling & Conveyance", "PL-04-07-09"),
        ("", "Printing & Stationery", "PL-04-07-10"),
        ("", "Legal & Professional Fees", "PL-04-07-11"),
        ("", "Audit Fee - Statutory", "PL-04-07-12"),
        ("", "Audit Fee - Tax Matters", "PL-04-07-13"),
        ("", "Audit Fee - Company Law", "PL-04-07-14"),
        ("", "Audit Fee - Other Services", "PL-04-07-15"),
        ("", "Audit Fee - Reimbursement", "PL-04-07-16"),
        ("", "Bad Debts Written Off", "PL-04-07-17"),
        ("", "Provision for Doubtful Debts", "PL-04-07-18"),
        ("", "Loss on Sale of Fixed Assets", "PL-04-07-19"),
        ("", "Foreign Exchange Loss", "PL-04-07-20"),
        ("", "CSR Expenditure", "PL-04-07-21"),
        ("", "Donations", "PL-04-07-22"),
        ("", "Freight & Forwarding", "PL-04-07-23"),
        ("", "Commission / Brokerage", "PL-04-07-24"),
        ("", "Advertisement & Promotion", "PL-04-07-25"),
        ("", "Directors' Sitting Fees", "PL-04-07-26"),
        ("(h)", "Miscellaneous Expenses", "PL-04-07-27"),
    ]
    return _build_note(db, balances, items, sign_multiplier=1)


def generate_note_tax(db: Session, balances: dict) -> dict:
    items = [
        ("(1)", "Current Tax", "PL-10-01"),
        ("(2)", "Deferred Tax", "PL-10-02"),
        ("(3)", "MAT Credit Entitlement", "PL-10-03"),
    ]
    # Mixed signs - Current/Deferred = Dr (+), MAT = Cr (-)
    line_items = []
    total_cy = 0.0
    total_py = 0.0
    for sno, label, code in items:
        sign = -1 if code == "PL-10-03" else 1
        cy = balances.get(code, {}).get("cy_net", 0) * sign
        py = balances.get(code, {}).get("py_net", 0) * sign
        line_items.append({
            "sno": sno, "particulars": label, "coa_code": code,
            "cy_amount": round(cy, 2), "py_amount": round(py, 2)
        })
        total_cy += cy
        total_py += py
    return {"items": line_items, "total_cy": round(total_cy, 2), "total_py": round(total_py, 2)}


# ---------- MASTER NOTES GENERATOR ----------

def generate_all_notes(db: Session, project_id: int) -> dict:
    """Generate all Notes (BS + PL) in one call."""
    balances = get_adjusted_balances(db, project_id)

    # Apply retained earnings adjustment (add PAT to BS-EL-01-02-09)
    from app.services.financial_engine import generate_pl
    pl = generate_pl(db, project_id)
    if "BS-EL-01-02-09" not in balances:
        balances["BS-EL-01-02-09"] = {"cy_net": 0, "py_net": 0}
    balances["BS-EL-01-02-09"]["cy_net"] -= pl["pat_cy"]

    return {
        "bs_notes": {
            "A": generate_note_a_share_capital(db, balances),
            "B": generate_note_b_reserves(db, balances),
            "C": generate_note_c_lt_borrowings(db, balances),
            "D": generate_note_d_other_lt_liab(db, balances),
            "E": generate_note_e_lt_provisions(db, balances),
            "F": generate_note_f_st_borrowings(db, balances),
            "FA": generate_note_fa_trade_payables(db, balances),
            "G": generate_note_g_other_current_liab(db, balances),
            "H": generate_note_h_st_provisions(db, balances),
            "I": generate_note_i_tangible(db, balances),
            "J": generate_note_j_intangible(db, balances),
            "K": generate_note_k_nc_investments(db, balances),
            "L": generate_note_l_lt_loans(db, balances),
            "M": generate_note_m_other_nc_assets(db, balances),
            "N": generate_note_n_current_investments(db, balances),
            "O": generate_note_o_inventories(db, balances),
            "P": generate_note_p_trade_receivables(db, balances),
            "Q": generate_note_q_cash(db, balances),
            "R": generate_note_r_st_loans(db, balances),
            "S": generate_note_s_other_current(db, balances),
        },
        "pl_notes": {
            "Rev": generate_note_rev(db, balances),
            "OI": generate_note_oi(db, balances),
            "Emp": generate_note_emp(db, balances),
            "Fin": generate_note_fin(db, balances),
            "Dep": generate_note_dep(db, balances),
            "OE": generate_note_oe(db, balances),
            "Tax": generate_note_tax(db, balances),
        },
    }
