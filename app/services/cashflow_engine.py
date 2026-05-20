"""
Cash Flow Statement Engine (Indirect Method as per AS-3)

Structure:
A. Cash Flow from Operating Activities
   - PBT
   - Adjustments (Dep, Finance Cost, Interest Income, etc.)
   - Operating Profit before WC Changes
   - WC Changes (Inc/Dec in Receivables, Payables, Inventory, etc.)
   - Cash Generated from Ops
   - Less: Income Tax Paid
   - Net Cash from Operating

B. Cash Flow from Investing Activities
   - Purchase/Sale of FA, Investments, Interest Received, Dividend Received

C. Cash Flow from Financing Activities
   - Share Capital, Borrowings, Interest Paid, Dividend Paid
"""
from sqlalchemy.orm import Session
from app.services.financial_engine import (
    get_adjusted_balances, sum_by_prefix, generate_pl
)


def generate_cashflow(db: Session, project_id: int) -> dict:
    """Generate Cash Flow Statement using indirect method."""
    balances = get_adjusted_balances(db, project_id)
    pl = generate_pl(db, project_id)

    # ---------- A. OPERATING ACTIVITIES ----------
    pbt_cy = pl["pat_cy"] + (pl["line_items"][-5][3] if pl["line_items"][-5][3] else 0)
    # Better: pull PBT directly from line items
    pbt_cy = next((li[3] for li in pl["line_items"] if li[1] == "Profit Before Tax (VII-VIII)"), 0)
    pbt_py = next((li[4] for li in pl["line_items"] if li[1] == "Profit Before Tax (VII-VIII)"), 0)

    # Adjustments (add back non-cash and non-operating)
    dep_cy, dep_py = sum_by_prefix(balances, "PL-04-06")  # Depreciation
    fin_cy, fin_py = sum_by_prefix(balances, "PL-04-05")  # Finance Costs
    int_inc_cy = -(balances.get("PL-02-01", {}).get("cy_net", 0)
                   + balances.get("PL-02-02", {}).get("cy_net", 0))  # Interest income
    int_inc_py = -(balances.get("PL-02-01", {}).get("py_net", 0)
                   + balances.get("PL-02-02", {}).get("py_net", 0))
    div_inc_cy = -balances.get("PL-02-03", {}).get("cy_net", 0)
    div_inc_py = -balances.get("PL-02-03", {}).get("py_net", 0)
    profit_sale_fa_cy = -balances.get("PL-02-05", {}).get("cy_net", 0)
    profit_sale_fa_py = -balances.get("PL-02-05", {}).get("py_net", 0)
    loss_sale_fa_cy = balances.get("PL-04-07-19", {}).get("cy_net", 0)
    loss_sale_fa_py = balances.get("PL-04-07-19", {}).get("py_net", 0)
    prov_doubt_cy = balances.get("PL-04-07-18", {}).get("cy_net", 0)
    prov_doubt_py = balances.get("PL-04-07-18", {}).get("py_net", 0)

    op_profit_before_wc_cy = (pbt_cy + dep_cy + fin_cy - int_inc_cy - div_inc_cy
                              - profit_sale_fa_cy + loss_sale_fa_cy + prov_doubt_cy)
    op_profit_before_wc_py = (pbt_py + dep_py + fin_py - int_inc_py - div_inc_py
                              - profit_sale_fa_py + loss_sale_fa_py + prov_doubt_py)

    # Working Capital Changes (Inc in CA = use of cash → negative; Inc in CL = source → positive)
    # Use BS movement: CY - PY
    def bs_movement(prefix, sign=1):
        cy, py = sum_by_prefix(balances, prefix)
        return sign * (cy - py)

    # Trade Receivables (Asset): Inc = -ve cash
    inc_tr = -bs_movement("BS-AS-02-03")
    # Inventories (Asset): Inc = -ve cash
    inc_inv = -bs_movement("BS-AS-02-02")
    # Other CA: Inc = -ve cash
    inc_oca = -bs_movement("BS-AS-02-06")
    # ST Loans & Adv (Asset): Inc = -ve cash
    inc_stla = -bs_movement("BS-AS-02-05")

    # Trade Payables (Liability, sign flipped): Inc = +ve cash
    inc_tp = -bs_movement("BS-EL-04-02")  # negate → liab inc = positive
    # Other CL: Inc = +ve cash
    inc_ocl = -bs_movement("BS-EL-04-03")
    # ST Provisions: Inc = +ve cash
    inc_stp = -bs_movement("BS-EL-04-04")

    wc_changes = inc_tr + inc_inv + inc_oca + inc_stla + inc_tp + inc_ocl + inc_stp

    cash_from_ops_cy = op_profit_before_wc_cy + wc_changes

    # Income Tax Paid (use current tax provision movement + CY current tax)
    tax_paid_cy = balances.get("PL-10-01", {}).get("cy_net", 0)
    tax_paid_py = balances.get("PL-10-01", {}).get("py_net", 0)

    net_op_cy = cash_from_ops_cy - tax_paid_cy
    net_op_py = op_profit_before_wc_py - tax_paid_py  # PY simplified

    # ---------- B. INVESTING ACTIVITIES ----------
    # Purchase of Fixed Assets = Net increase in tangible+intangible
    fa_movement = -(bs_movement("BS-AS-01-01"))  # Asset increase = negative cash

    # Purchase of Investments
    inv_movement = -(bs_movement("BS-AS-01-02") + bs_movement("BS-AS-02-01"))

    # Interest Received (already in PL - reverse from operating)
    int_rec = int_inc_cy
    div_rec = div_inc_cy

    net_inv_cy = fa_movement + inv_movement + int_rec + div_rec + profit_sale_fa_cy

    # ---------- C. FINANCING ACTIVITIES ----------
    # Share Capital movement
    sc_movement = -bs_movement("BS-EL-01-01")  # Liab inc = positive cash

    # Securities Premium movement
    sp_movement = -(balances.get("BS-EL-01-02-03", {}).get("cy_net", 0)
                    - balances.get("BS-EL-01-02-03", {}).get("py_net", 0))

    # LT Borrowings movement
    ltb_movement = -bs_movement("BS-EL-03-01")
    # ST Borrowings movement
    stb_movement = -bs_movement("BS-EL-04-01")

    # Interest Paid
    int_paid = -fin_cy
    # Dividend Paid (proxy from proposed dividend movement)
    div_paid = 0  # Manual input typically

    net_fin_cy = sc_movement + sp_movement + ltb_movement + stb_movement + int_paid + div_paid

    # ---------- NET CHANGE IN CASH ----------
    net_change_cy = net_op_cy + net_inv_cy + net_fin_cy

    # Opening & Closing Cash (from BS Cash & Equivalents)
    cash_open_cy = balances.get("BS-AS-02-04-01", {}).get("py_net", 0) + \
                   balances.get("BS-AS-02-04-06", {}).get("py_net", 0) + \
                   balances.get("BS-AS-02-04-07", {}).get("py_net", 0)
    cash_close_cy, _ = sum_by_prefix(balances, "BS-AS-02-04")

    line_items = [
        ("A.", "CASH FLOW FROM OPERATING ACTIVITIES", None, None, True, 1),
        ("", "Profit Before Tax", pbt_cy, pbt_py, False, 2),
        ("", "Adjustments for:", None, None, True, 2),
        ("", "  Depreciation & Amortization", dep_cy, dep_py, False, 3),
        ("", "  Finance Costs", fin_cy, fin_py, False, 3),
        ("", "  Interest Income", -int_inc_cy, -int_inc_py, False, 3),
        ("", "  Dividend Income", -div_inc_cy, -div_inc_py, False, 3),
        ("", "  (Profit)/Loss on Sale of Assets", -profit_sale_fa_cy + loss_sale_fa_cy,
         -profit_sale_fa_py + loss_sale_fa_py, False, 3),
        ("", "  Provision for Doubtful Debts", prov_doubt_cy, prov_doubt_py, False, 3),
        ("", "Operating Profit Before WC Changes", op_profit_before_wc_cy,
         op_profit_before_wc_py, True, 2),
        ("", "Changes in Working Capital:", None, None, True, 2),
        ("", "  (Inc)/Dec in Trade Receivables", inc_tr, 0, False, 3),
        ("", "  (Inc)/Dec in Inventories", inc_inv, 0, False, 3),
        ("", "  (Inc)/Dec in Other Current Assets", inc_oca, 0, False, 3),
        ("", "  (Inc)/Dec in Loans & Advances (ST)", inc_stla, 0, False, 3),
        ("", "  Inc/(Dec) in Trade Payables", inc_tp, 0, False, 3),
        ("", "  Inc/(Dec) in Other Current Liab", inc_ocl, 0, False, 3),
        ("", "  Inc/(Dec) in Provisions (ST)", inc_stp, 0, False, 3),
        ("", "Cash Generated from Operations", cash_from_ops_cy, 0, True, 2),
        ("", "  Less: Income Tax Paid (Net)", tax_paid_cy, tax_paid_py, False, 3),
        ("", "Net Cash from Operating Activities (A)", net_op_cy, net_op_py, True, 1),
        ("", "", None, None, False, 0),
        ("B.", "CASH FLOW FROM INVESTING ACTIVITIES", None, None, True, 1),
        ("", "  Purchase of Fixed Assets (Net)", fa_movement, 0, False, 3),
        ("", "  (Purchase)/Sale of Investments (Net)", inv_movement, 0, False, 3),
        ("", "  Interest Received", int_rec, 0, False, 3),
        ("", "  Dividend Received", div_rec, 0, False, 3),
        ("", "  Profit on Sale of Assets", profit_sale_fa_cy, 0, False, 3),
        ("", "Net Cash from Investing Activities (B)", net_inv_cy, 0, True, 1),
        ("", "", None, None, False, 0),
        ("C.", "CASH FLOW FROM FINANCING ACTIVITIES", None, None, True, 1),
        ("", "  Proceeds from Share Capital (Net)", sc_movement, 0, False, 3),
        ("", "  Securities Premium Received", sp_movement, 0, False, 3),
        ("", "  Proceeds/(Repayment) of LT Borrowings (Net)", ltb_movement, 0, False, 3),
        ("", "  Proceeds/(Repayment) of ST Borrowings (Net)", stb_movement, 0, False, 3),
        ("", "  Finance Costs Paid", int_paid, 0, False, 3),
        ("", "  Dividend Paid", div_paid, 0, False, 3),
        ("", "Net Cash from Financing Activities (C)", net_fin_cy, 0, True, 1),
        ("", "", None, None, False, 0),
        ("", "Net Inc/(Dec) in Cash & Equivalents (A+B+C)", net_change_cy, 0, True, 1),
        ("", "Cash & Equivalents at Beginning", cash_open_cy, 0, False, 2),
        ("", "Cash & Equivalents at End", cash_close_cy, 0, True, 1),
    ]

    return {
        "line_items": line_items,
        "net_op_cy": round(net_op_cy, 2),
        "net_inv_cy": round(net_inv_cy, 2),
        "net_fin_cy": round(net_fin_cy, 2),
        "net_change_cy": round(net_change_cy, 2),
        "cash_open_cy": round(cash_open_cy, 2),
        "cash_close_cy": round(cash_close_cy, 2),
        "reconciliation_diff": round(cash_close_cy - cash_open_cy - net_change_cy, 2),
    }
