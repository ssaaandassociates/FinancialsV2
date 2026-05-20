"""
Share Capital Engine (Note A)
Full Schedule III Division I disclosure:

1. Capital Structure (Authorised → Issued → Subscribed → Paid-up)
2. Reconciliation (Opening + Issues - Buybacks = Closing)
3. Rights, preferences & restrictions
4. Shareholders holding >5%
5. Promoter shareholding with % change from PY
6. 5-year allotment history (bonus, without cash, buyback)
7. Terms of convertible securities
8. Calls unpaid (by directors/officers separately)
9. Forfeited shares (amount originally paid up)
"""
from sqlalchemy.orm import Session
from app.models import ShareEvent, Shareholder, Client, Project
from app.services.financial_engine import get_adjusted_balances


def save_share_event(
    db: Session, project_id: int,
    event_type: str, event_date=None, share_class: str = "equity",
    no_of_shares: int = 0, face_value: float = 10, premium: float = 0,
    period: str = "CY", narration: str = ""
) -> ShareEvent:
    """Save a share capital movement event."""
    total = no_of_shares * (face_value + premium)
    event = ShareEvent(
        project_id=project_id,
        event_type=event_type,
        event_date=event_date,
        share_class=share_class,
        no_of_shares=no_of_shares,
        face_value=face_value,
        premium=premium,
        total_amount=total,
        period=period,
        narration=narration,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def save_shareholder(
    db: Session, project_id: int,
    name: str, no_of_shares_cy: int, no_of_shares_py: int = 0,
    share_class: str = "equity", is_promoter: bool = False,
    din_pan: str = ""
) -> Shareholder:
    """Save a shareholder record."""
    sh = Shareholder(
        project_id=project_id,
        name=name,
        share_class=share_class,
        no_of_shares_cy=no_of_shares_cy,
        no_of_shares_py=no_of_shares_py,
        is_promoter=is_promoter,
        din_pan=din_pan,
    )
    db.add(sh)
    db.commit()
    db.refresh(sh)
    return sh


def compute_shareholding_pct(db: Session, project_id: int):
    """Recompute % holding for all shareholders of a project."""
    shareholders = db.query(Shareholder).filter(
        Shareholder.project_id == project_id
    ).all()

    total_cy = sum(s.no_of_shares_cy for s in shareholders)
    total_py = sum(s.no_of_shares_py for s in shareholders)

    for s in shareholders:
        s.pct_holding_cy = round((s.no_of_shares_cy / total_cy * 100) if total_cy > 0 else 0, 2)
        s.pct_holding_py = round((s.no_of_shares_py / total_py * 100) if total_py > 0 else 0, 2)

    db.commit()
    return {"total_shares_cy": total_cy, "total_shares_py": total_py, "shareholders": len(shareholders)}


def get_share_reconciliation(db: Session, project_id: int) -> dict:
    """
    Build share capital reconciliation:
    Opening + Issues + Bonus + Rights - Buybacks - Forfeited = Closing
    """
    events_cy = db.query(ShareEvent).filter(
        ShareEvent.project_id == project_id,
        ShareEvent.period == "CY"
    ).order_by(ShareEvent.event_date).all()

    events_py = db.query(ShareEvent).filter(
        ShareEvent.project_id == project_id,
        ShareEvent.period == "PY"
    ).order_by(ShareEvent.event_date).all()

    def summarize(events):
        opening = {"shares": 0, "amount": 0}
        additions = {"shares": 0, "amount": 0}
        deductions = {"shares": 0, "amount": 0}
        details = []

        for e in events:
            entry = {
                "type": e.event_type,
                "date": str(e.event_date) if e.event_date else "",
                "shares": e.no_of_shares,
                "amount": e.total_amount,
                "narration": e.narration,
            }
            details.append(entry)

            if e.event_type == "opening":
                opening["shares"] += e.no_of_shares
                opening["amount"] += e.total_amount
            elif e.event_type in ("buyback", "forfeiture"):
                deductions["shares"] += e.no_of_shares
                deductions["amount"] += e.total_amount
            else:  # issue, bonus, rights
                additions["shares"] += e.no_of_shares
                additions["amount"] += e.total_amount

        closing = {
            "shares": opening["shares"] + additions["shares"] - deductions["shares"],
            "amount": opening["amount"] + additions["amount"] - deductions["amount"],
        }

        return {
            "opening": opening,
            "additions": additions,
            "deductions": deductions,
            "closing": closing,
            "details": details,
        }

    return {
        "cy": summarize(events_cy),
        "py": summarize(events_py),
    }


def get_major_shareholders(db: Session, project_id: int, threshold_pct: float = 5.0) -> list[dict]:
    """Get shareholders holding more than threshold_pct %."""
    compute_shareholding_pct(db, project_id)
    shareholders = db.query(Shareholder).filter(
        Shareholder.project_id == project_id
    ).order_by(Shareholder.pct_holding_cy.desc()).all()

    all_sh = []
    major = []
    for s in shareholders:
        entry = {
            "name": s.name,
            "share_class": s.share_class,
            "shares_cy": s.no_of_shares_cy,
            "shares_py": s.no_of_shares_py,
            "pct_cy": s.pct_holding_cy,
            "pct_py": s.pct_holding_py,
            "is_promoter": s.is_promoter,
            "din_pan": s.din_pan,
        }
        all_sh.append(entry)
        if s.pct_holding_cy >= threshold_pct:
            major.append(entry)

    return {
        "all_shareholders": all_sh,
        "major_shareholders": major,
        "threshold_pct": threshold_pct,
    }


def get_promoter_holding(db: Session, project_id: int) -> list[dict]:
    """
    Get promoter shareholding with % change from PY.
    (Schedule III requirement since 2023)
    """
    compute_shareholding_pct(db, project_id)
    promoters = db.query(Shareholder).filter(
        Shareholder.project_id == project_id,
        Shareholder.is_promoter == True,
    ).order_by(Shareholder.pct_holding_cy.desc()).all()

    result = []
    for p in promoters:
        pct_change = 0
        if p.pct_holding_py and p.pct_holding_py > 0:
            pct_change = round(p.pct_holding_cy - p.pct_holding_py, 2)

        result.append({
            "name": p.name,
            "shares_cy": p.no_of_shares_cy,
            "pct_cy": p.pct_holding_cy,
            "shares_py": p.no_of_shares_py,
            "pct_py": p.pct_holding_py,
            "pct_change": pct_change,
        })

    return result


def generate_full_note_a(db: Session, project_id: int) -> dict:
    """
    Build complete Note A: Share Capital disclosure.
    Combines:
    1. Capital structure from TB balances
    2. Reconciliation from share events
    3. Major shareholders
    4. Promoter holding with % change
    """
    balances = get_adjusted_balances(db, project_id)

    # Capital structure from TB codes
    def get_bal(code):
        cy = -(balances.get(code, {}).get("cy_net", 0))
        py = -(balances.get(code, {}).get("py_net", 0))
        return {"cy": round(cy, 2), "py": round(py, 2)}

    capital_structure = {
        "authorised_equity": get_bal("BS-EL-01-01-01"),
        "authorised_preference": get_bal("BS-EL-01-01-04"),
        "issued_equity": get_bal("BS-EL-01-01-02"),
        "issued_preference": get_bal("BS-EL-01-01-05"),
        "subscribed_not_paid": get_bal("BS-EL-01-01-03"),
        "calls_unpaid": get_bal("BS-EL-01-01-06"),
        "forfeited_shares": get_bal("BS-EL-01-01-07"),
    }

    return {
        "capital_structure": capital_structure,
        "reconciliation": get_share_reconciliation(db, project_id),
        "shareholders": get_major_shareholders(db, project_id),
        "promoter_holding": get_promoter_holding(db, project_id),
    }
