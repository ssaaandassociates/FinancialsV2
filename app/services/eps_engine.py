"""
EPS Engine (AS-20)

Basic EPS = (PAT - Preference Dividend) / Weighted Avg Equity Shares Outstanding
Diluted EPS = (PAT - Pref Div + Dilutive adjustments) / Weighted Avg + Dilutive Potential Shares

Weighted Avg = sum of (Shares × Days Outstanding / Total Days)
"""
from datetime import date
from sqlalchemy.orm import Session
from app.models import Project, Client
from app.services.financial_engine import generate_pl, get_adjusted_balances


def weighted_avg_shares(events: list[dict], period_start: date, period_end: date) -> float:
    """
    Compute weighted average shares from a list of share events.
    events = [{"date": date, "shares": int, "type": "opening|issue|buyback"}]
    """
    if not events:
        return 0

    total_days = (period_end - period_start).days + 1
    if total_days <= 0:
        return 0

    # Sort by date
    events_sorted = sorted(events, key=lambda x: x["date"])

    total_weighted = 0.0
    current_shares = 0

    # Opening balance
    opening = next((e for e in events_sorted if e.get("type") == "opening"), None)
    if opening:
        current_shares = opening["shares"]
        events_sorted = [e for e in events_sorted if e is not opening]

    last_date = period_start
    for evt in events_sorted:
        evt_date = evt["date"]
        if evt_date < period_start or evt_date > period_end:
            continue
        # Days at current_shares level
        days = (evt_date - last_date).days
        if days > 0:
            total_weighted += current_shares * days
        # Apply event
        if evt.get("type") == "buyback":
            current_shares -= evt["shares"]
        else:  # issue / bonus / rights
            current_shares += evt["shares"]
        last_date = evt_date

    # Final period
    days = (period_end - last_date).days + 1
    if days > 0:
        total_weighted += current_shares * days

    return round(total_weighted / total_days, 2)


def generate_eps(db: Session, project_id: int,
                 share_events: list[dict] = None,
                 dilutive_potential_shares: int = 0,
                 preference_dividend: float = 0,
                 dilutive_adjustment: float = 0) -> dict:
    """
    Generate EPS computation.

    share_events: list of {"date": "2024-04-01", "shares": 10000, "type": "opening|issue|buyback"}
    If not provided, uses paid-up shares from client's paid_up_capital / face_value (simple)
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    client = project.client
    pl = generate_pl(db, project_id)
    pat_cy = pl["pat_cy"]
    pat_py = pl["pat_py"]

    profit_to_equity_cy = pat_cy - preference_dividend
    profit_to_equity_py = pat_py - preference_dividend

    # Determine shares
    period_start = project.bs_date_py or date(2024, 4, 1)
    if isinstance(period_start, date):
        # Convert to FY start (typically next day after PY BS date)
        from datetime import timedelta
        period_start = period_start + timedelta(days=1)
    period_end = project.bs_date_cy or date(2025, 3, 31)

    if share_events:
        wa_basic = weighted_avg_shares(share_events, period_start, period_end)
    else:
        # Fallback: use paid-up / face value (assume no movement)
        face_value = client.face_value or 10
        paid_up = client.paid_up_capital or 0
        wa_basic = paid_up / face_value if face_value > 0 else 0

    wa_diluted = wa_basic + dilutive_potential_shares

    basic_eps_cy = round(profit_to_equity_cy / wa_basic, 2) if wa_basic > 0 else 0
    basic_eps_py = round(profit_to_equity_py / wa_basic, 2) if wa_basic > 0 else 0

    diluted_profit_cy = profit_to_equity_cy + dilutive_adjustment
    diluted_eps_cy = round(diluted_profit_cy / wa_diluted, 2) if wa_diluted > 0 else 0
    diluted_eps_py = round(profit_to_equity_py / wa_diluted, 2) if wa_diluted > 0 else 0

    return {
        "pat_cy": round(pat_cy, 2),
        "pat_py": round(pat_py, 2),
        "preference_dividend": preference_dividend,
        "profit_to_equity_cy": round(profit_to_equity_cy, 2),
        "profit_to_equity_py": round(profit_to_equity_py, 2),
        "weighted_avg_basic": wa_basic,
        "weighted_avg_diluted": wa_diluted,
        "dilutive_potential_shares": dilutive_potential_shares,
        "face_value": client.face_value,
        "basic_eps_cy": basic_eps_cy,
        "basic_eps_py": basic_eps_py,
        "diluted_eps_cy": diluted_eps_cy,
        "diluted_eps_py": diluted_eps_py,
    }
