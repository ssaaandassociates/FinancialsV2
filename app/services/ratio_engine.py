"""
Ratio Engine - 11 Mandatory Schedule III Ratios

1. Current Ratio = Current Assets / Current Liabilities
2. Debt-Equity Ratio = Total Debt / Shareholders Equity
3. Debt Service Coverage Ratio = (PAT + Dep + Int) / (Int + Principal Repayment)
4. Return on Equity = PAT / Avg Shareholders Equity
5. Inventory Turnover = COGS or Sales / Avg Inventory
6. Trade Receivables Turnover = Net Sales / Avg Trade Receivables
7. Trade Payables Turnover = Net Purchases / Avg Trade Payables
8. Net Capital Turnover Ratio = Net Sales / Working Capital
9. Net Profit Ratio = PAT / Net Sales
10. Return on Capital Employed = EBIT / Capital Employed
11. Return on Investment = Investment Income / Avg Investments

Variance: Flag if change > 25% (per Schedule III requirement)
"""
from sqlalchemy.orm import Session
from app.services.financial_engine import (
    get_adjusted_balances, sum_by_prefix, generate_pl
)


def _safe_div(num: float, den: float) -> float | None:
    if not den or abs(den) < 0.01:
        return None
    return round(num / den, 4)


def _avg(cy: float, py: float) -> float:
    """Average of CY and PY balances"""
    return (cy + py) / 2


def _variance_pct(cy: float | None, py: float | None) -> float | None:
    if cy is None or py is None or abs(py) < 0.01:
        return None
    return round((cy - py) / abs(py), 4)


def _flag_variance(pct: float | None) -> str:
    """Flag if variance > 25% (Schedule III requires explanation)"""
    if pct is None:
        return ""
    if abs(pct) > 0.25:
        return "EXPLAIN"
    return ""


def generate_ratios(db: Session, project_id: int,
                    py_minus_1_data: dict = None) -> dict:
    """
    Generate all 11 ratios with variance analysis.
    py_minus_1_data: optional dict with PY-1 balances for averaging
                     keys: trade_receivables, trade_payables, inventory,
                           shareholders_equity, investments
    """
    balances = get_adjusted_balances(db, project_id)
    pl = generate_pl(db, project_id)

    py_minus_1 = py_minus_1_data or {}

    # ---- BS Aggregates ----
    # Current Assets
    ci_cy, ci_py = sum_by_prefix(balances, "BS-AS-02-01")
    inv_cy, inv_py = sum_by_prefix(balances, "BS-AS-02-02")
    tr_cy, tr_py = sum_by_prefix(balances, "BS-AS-02-03")
    cash_cy, cash_py = sum_by_prefix(balances, "BS-AS-02-04")
    stla_cy, stla_py = sum_by_prefix(balances, "BS-AS-02-05")
    oc_cy, oc_py = sum_by_prefix(balances, "BS-AS-02-06")
    ca_cy = ci_cy + inv_cy + tr_cy + cash_cy + stla_cy + oc_cy
    ca_py = ci_py + inv_py + tr_py + cash_py + stla_py + oc_py

    # Current Liabilities
    stb_cy, stb_py = sum_by_prefix(balances, "BS-EL-04-01")
    tp_cy, tp_py = sum_by_prefix(balances, "BS-EL-04-02")
    ocl_cy, ocl_py = sum_by_prefix(balances, "BS-EL-04-03")
    stp_cy, stp_py = sum_by_prefix(balances, "BS-EL-04-04")
    cl_cy = -(stb_cy + tp_cy + ocl_cy + stp_cy)  # Negate to positive
    cl_py = -(stb_py + tp_py + ocl_py + stp_py)

    # Total Debt = LT + ST Borrowings
    ltb_cy, ltb_py = sum_by_prefix(balances, "BS-EL-03-01")
    debt_cy = -(ltb_cy + stb_cy)
    debt_py = -(ltb_py + stb_py)

    # Shareholders Equity = Share Capital + Reserves + Money against warrants
    sc_cy, sc_py = sum_by_prefix(balances, "BS-EL-01-01")
    res_cy, res_py = sum_by_prefix(balances, "BS-EL-01-02")
    mw_cy, mw_py = sum_by_prefix(balances, "BS-EL-01-03")
    # Adjust reserves with current year PAT (auto-balancing)
    res_cy_adj = res_cy - pl["pat_cy"]  # res_cy is negative (Cr), PAT positive → subtracting adds
    equity_cy = -(sc_cy + res_cy_adj + mw_cy)
    equity_py = -(sc_py + res_py + mw_py)

    # Investments
    inv_nc_cy, inv_nc_py = sum_by_prefix(balances, "BS-AS-01-02")
    investments_cy = inv_nc_cy + ci_cy
    investments_py = inv_nc_py + ci_py

    # Total Assets
    nc_cy = inv_nc_cy
    for p in ["BS-AS-01-01", "BS-AS-01-03", "BS-AS-01-04", "BS-AS-01-05"]:
        c, p_ = sum_by_prefix(balances, p)
        nc_cy += c
        # also add to py
    ta_cy = nc_cy + ca_cy

    # ---- PL Aggregates ----
    sales_cy, sales_py = sum_by_prefix(balances, "PL-01")
    sales_cy, sales_py = -sales_cy, -sales_py

    purchases_cy = balances.get("PL-04-01-02", {}).get("cy_net", 0) + \
                   balances.get("PL-04-02", {}).get("cy_net", 0)
    purchases_py = balances.get("PL-04-01-02", {}).get("py_net", 0) + \
                   balances.get("PL-04-02", {}).get("py_net", 0)

    cost_materials_cy, cost_materials_py = sum_by_prefix(balances, "PL-04-01")

    pat_cy = pl["pat_cy"]
    pat_py = pl["pat_py"]

    pbt_cy = next((li[3] for li in pl["line_items"] if li[1] == "Profit Before Tax (VII-VIII)"), 0)
    pbt_py = next((li[4] for li in pl["line_items"] if li[1] == "Profit Before Tax (VII-VIII)"), 0)

    fin_cy, fin_py = sum_by_prefix(balances, "PL-04-05")  # Finance costs
    dep_cy, dep_py = sum_by_prefix(balances, "PL-04-06")
    ebit_cy = pbt_cy + fin_cy
    ebit_py = pbt_py + fin_py

    int_inc_cy = -(balances.get("PL-02-01", {}).get("cy_net", 0)
                   + balances.get("PL-02-02", {}).get("cy_net", 0))
    div_inc_cy = -balances.get("PL-02-03", {}).get("cy_net", 0)
    inv_income_cy = int_inc_cy + div_inc_cy

    int_inc_py = -(balances.get("PL-02-01", {}).get("py_net", 0)
                   + balances.get("PL-02-02", {}).get("py_net", 0))
    div_inc_py = -balances.get("PL-02-03", {}).get("py_net", 0)
    inv_income_py = int_inc_py + div_inc_py

    # Capital Employed = Equity + LT Debt
    cap_employed_cy = equity_cy + (-ltb_cy)
    cap_employed_py = equity_py + (-ltb_py)

    # PY-1 averages (for CY denominator) and PY-2 (for PY denominator) - simplified as PY only
    avg_tr_cy = _avg(tr_cy, tr_py)
    avg_tr_py = _avg(tr_py, py_minus_1.get("trade_receivables", tr_py))
    avg_tp_cy = _avg(-tp_cy, -tp_py)
    avg_tp_py = _avg(-tp_py, py_minus_1.get("trade_payables", -tp_py))
    avg_inv_cy = _avg(inv_cy, inv_py)
    avg_inv_py = _avg(inv_py, py_minus_1.get("inventory", inv_py))
    avg_eq_cy = _avg(equity_cy, equity_py)
    avg_eq_py = _avg(equity_py, py_minus_1.get("shareholders_equity", equity_py))
    avg_invst_cy = _avg(investments_cy, investments_py)
    avg_invst_py = _avg(investments_py, py_minus_1.get("investments", investments_py))

    # ---- Compute Ratios ----
    ratios = []

    # 1. Current Ratio
    cr_cy = _safe_div(ca_cy, cl_cy)
    cr_py = _safe_div(ca_py, cl_py)
    ratios.append({
        "no": 1, "name": "Current Ratio",
        "numerator": "Current Assets", "denominator": "Current Liabilities",
        "num_cy": ca_cy, "num_py": ca_py,
        "den_cy": cl_cy, "den_py": cl_py,
        "cy": cr_cy, "py": cr_py,
        "variance_pct": _variance_pct(cr_cy, cr_py),
        "flag": _flag_variance(_variance_pct(cr_cy, cr_py)),
    })

    # 2. Debt-Equity
    de_cy = _safe_div(debt_cy, equity_cy)
    de_py = _safe_div(debt_py, equity_py)
    ratios.append({
        "no": 2, "name": "Debt-Equity Ratio",
        "numerator": "Total Debt", "denominator": "Shareholders Equity",
        "num_cy": debt_cy, "num_py": debt_py,
        "den_cy": equity_cy, "den_py": equity_py,
        "cy": de_cy, "py": de_py,
        "variance_pct": _variance_pct(de_cy, de_py),
        "flag": _flag_variance(_variance_pct(de_cy, de_py)),
    })

    # 3. DSCR = (PAT + Dep + Int) / (Int + Principal repayment)
    # Principal repayment proxy: decrease in LT borrowings + current maturities
    cmltd_cy = balances.get("BS-EL-04-03-01", {}).get("cy_net", 0)
    principal_repay_cy = max(0, -ltb_py - (-ltb_cy)) + (-cmltd_cy)
    dscr_num_cy = pat_cy + dep_cy + fin_cy
    dscr_den_cy = fin_cy + principal_repay_cy
    dscr_cy = _safe_div(dscr_num_cy, dscr_den_cy)
    ratios.append({
        "no": 3, "name": "Debt Service Coverage Ratio",
        "numerator": "EBITDA", "denominator": "Interest + Principal",
        "num_cy": dscr_num_cy, "num_py": pat_py + dep_py + fin_py,
        "den_cy": dscr_den_cy, "den_py": fin_py,
        "cy": dscr_cy, "py": _safe_div(pat_py + dep_py + fin_py, fin_py),
        "variance_pct": None, "flag": "",
    })

    # 4. Return on Equity
    roe_cy = _safe_div(pat_cy, avg_eq_cy)
    roe_py = _safe_div(pat_py, avg_eq_py)
    ratios.append({
        "no": 4, "name": "Return on Equity (ROE)",
        "numerator": "PAT", "denominator": "Avg Shareholders Equity",
        "num_cy": pat_cy, "num_py": pat_py,
        "den_cy": avg_eq_cy, "den_py": avg_eq_py,
        "cy": roe_cy, "py": roe_py,
        "variance_pct": _variance_pct(roe_cy, roe_py),
        "flag": _flag_variance(_variance_pct(roe_cy, roe_py)),
    })

    # 5. Inventory Turnover
    it_cy = _safe_div(sales_cy, avg_inv_cy)
    it_py = _safe_div(sales_py, avg_inv_py)
    ratios.append({
        "no": 5, "name": "Inventory Turnover",
        "numerator": "Net Sales", "denominator": "Avg Inventory",
        "num_cy": sales_cy, "num_py": sales_py,
        "den_cy": avg_inv_cy, "den_py": avg_inv_py,
        "cy": it_cy, "py": it_py,
        "variance_pct": _variance_pct(it_cy, it_py),
        "flag": _flag_variance(_variance_pct(it_cy, it_py)),
    })

    # 6. Trade Receivables Turnover
    trt_cy = _safe_div(sales_cy, avg_tr_cy)
    trt_py = _safe_div(sales_py, avg_tr_py)
    ratios.append({
        "no": 6, "name": "Trade Receivables Turnover",
        "numerator": "Net Sales", "denominator": "Avg Trade Receivables",
        "num_cy": sales_cy, "num_py": sales_py,
        "den_cy": avg_tr_cy, "den_py": avg_tr_py,
        "cy": trt_cy, "py": trt_py,
        "variance_pct": _variance_pct(trt_cy, trt_py),
        "flag": _flag_variance(_variance_pct(trt_cy, trt_py)),
    })

    # 7. Trade Payables Turnover
    tpt_cy = _safe_div(purchases_cy, avg_tp_cy)
    tpt_py = _safe_div(purchases_py, avg_tp_py)
    ratios.append({
        "no": 7, "name": "Trade Payables Turnover",
        "numerator": "Net Purchases", "denominator": "Avg Trade Payables",
        "num_cy": purchases_cy, "num_py": purchases_py,
        "den_cy": avg_tp_cy, "den_py": avg_tp_py,
        "cy": tpt_cy, "py": tpt_py,
        "variance_pct": _variance_pct(tpt_cy, tpt_py),
        "flag": _flag_variance(_variance_pct(tpt_cy, tpt_py)),
    })

    # 8. Net Capital Turnover Ratio = Sales / Working Capital
    wc_cy = ca_cy - cl_cy
    wc_py = ca_py - cl_py
    nct_cy = _safe_div(sales_cy, wc_cy)
    nct_py = _safe_div(sales_py, wc_py)
    ratios.append({
        "no": 8, "name": "Net Capital Turnover Ratio",
        "numerator": "Net Sales", "denominator": "Working Capital",
        "num_cy": sales_cy, "num_py": sales_py,
        "den_cy": wc_cy, "den_py": wc_py,
        "cy": nct_cy, "py": nct_py,
        "variance_pct": _variance_pct(nct_cy, nct_py),
        "flag": _flag_variance(_variance_pct(nct_cy, nct_py)),
    })

    # 9. Net Profit Ratio
    np_cy = _safe_div(pat_cy, sales_cy)
    np_py = _safe_div(pat_py, sales_py)
    ratios.append({
        "no": 9, "name": "Net Profit Ratio",
        "numerator": "PAT", "denominator": "Net Sales",
        "num_cy": pat_cy, "num_py": pat_py,
        "den_cy": sales_cy, "den_py": sales_py,
        "cy": np_cy, "py": np_py,
        "variance_pct": _variance_pct(np_cy, np_py),
        "flag": _flag_variance(_variance_pct(np_cy, np_py)),
    })

    # 10. Return on Capital Employed
    roce_cy = _safe_div(ebit_cy, cap_employed_cy)
    roce_py = _safe_div(ebit_py, cap_employed_py)
    ratios.append({
        "no": 10, "name": "Return on Capital Employed (ROCE)",
        "numerator": "EBIT", "denominator": "Capital Employed",
        "num_cy": ebit_cy, "num_py": ebit_py,
        "den_cy": cap_employed_cy, "den_py": cap_employed_py,
        "cy": roce_cy, "py": roce_py,
        "variance_pct": _variance_pct(roce_cy, roce_py),
        "flag": _flag_variance(_variance_pct(roce_cy, roce_py)),
    })

    # 11. Return on Investment
    roi_cy = _safe_div(inv_income_cy, avg_invst_cy)
    roi_py = _safe_div(inv_income_py, avg_invst_py)
    ratios.append({
        "no": 11, "name": "Return on Investment (ROI)",
        "numerator": "Investment Income", "denominator": "Avg Investments",
        "num_cy": inv_income_cy, "num_py": inv_income_py,
        "den_cy": avg_invst_cy, "den_py": avg_invst_py,
        "cy": roi_cy, "py": roi_py,
        "variance_pct": _variance_pct(roi_cy, roi_py),
        "flag": _flag_variance(_variance_pct(roi_cy, roi_py)),
    })

    return {
        "ratios": ratios,
        "py_minus_1_used": bool(py_minus_1_data),
        "flagged_count": sum(1 for r in ratios if r["flag"]),
    }
