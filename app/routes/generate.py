"""Generate routes - BS, PL, Notes, Cash Flow, Ratios, EPS"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import (
    financial_engine,
    notes_engine,
    cashflow_engine,
    ratio_engine,
    eps_engine,
    validation_service,
)

router = APIRouter()


class PYMinus1Data(BaseModel):
    trade_receivables: float | None = None
    trade_payables: float | None = None
    inventory: float | None = None
    shareholders_equity: float | None = None
    investments: float | None = None


class ShareEvent(BaseModel):
    date: str
    shares: int
    type: str  # opening | issue | buyback


class EPSInput(BaseModel):
    share_events: list[ShareEvent] | None = None
    dilutive_potential_shares: int = 0
    preference_dividend: float = 0
    dilutive_adjustment: float = 0


@router.get("/generate/{project_id}/pl")
def get_pl(project_id: int, db: Session = Depends(get_db)):
    """Generate Profit & Loss statement."""
    try:
        return financial_engine.generate_pl(db, project_id)
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/generate/{project_id}/bs")
def get_bs(project_id: int, db: Session = Depends(get_db)):
    """Generate Balance Sheet."""
    try:
        return financial_engine.generate_bs(db, project_id)
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/generate/{project_id}/notes")
def get_notes(project_id: int, db: Session = Depends(get_db)):
    """Generate all Notes (BS A-S + PL Rev/OI/Emp/Fin/Dep/OE/Tax)."""
    try:
        return notes_engine.generate_all_notes(db, project_id)
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/generate/{project_id}/cashflow")
def get_cashflow(project_id: int, db: Session = Depends(get_db)):
    """Generate Cash Flow Statement (Indirect Method)."""
    try:
        return cashflow_engine.generate_cashflow(db, project_id)
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/generate/{project_id}/ratios")
def get_ratios(project_id: int, py_minus_1: PYMinus1Data | None = None,
               db: Session = Depends(get_db)):
    """Generate 11 mandatory Schedule III ratios with variance flagging."""
    try:
        py_data = py_minus_1.model_dump(exclude_none=True) if py_minus_1 else None
        return ratio_engine.generate_ratios(db, project_id, py_minus_1_data=py_data)
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/generate/{project_id}/eps")
def get_eps(project_id: int, payload: EPSInput | None = None,
            db: Session = Depends(get_db)):
    """Generate EPS computation (Basic + Diluted)."""
    try:
        from datetime import datetime
        events = None
        if payload and payload.share_events:
            events = [
                {"date": datetime.fromisoformat(e.date).date(), "shares": e.shares, "type": e.type}
                for e in payload.share_events
            ]
        return eps_engine.generate_eps(
            db, project_id,
            share_events=events,
            dilutive_potential_shares=payload.dilutive_potential_shares if payload else 0,
            preference_dividend=payload.preference_dividend if payload else 0,
            dilutive_adjustment=payload.dilutive_adjustment if payload else 0,
        )
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/generate/{project_id}/all")
def get_all(project_id: int, db: Session = Depends(get_db)):
    """Generate complete financial statements in one call."""
    try:
        return {
            "balance_sheet": financial_engine.generate_bs(db, project_id),
            "profit_and_loss": financial_engine.generate_pl(db, project_id),
            "notes": notes_engine.generate_all_notes(db, project_id),
            "cash_flow": cashflow_engine.generate_cashflow(db, project_id),
            "ratios": ratio_engine.generate_ratios(db, project_id),
            "eps": eps_engine.generate_eps(db, project_id),
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/validate/{project_id}")
def validate_project(project_id: int, db: Session = Depends(get_db)):
    """Run all validation checks before export."""
    try:
        return validation_service.run_validation(db, project_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


# =========================================================================
# Section 9 V9 — Preview line drill-down
# =========================================================================

@router.get("/preview/{project_id}/line-detail")
def line_detail(project_id: int, note_ref: str, db: Session = Depends(get_db)):
    """
    Return TB ledger detail for a BS/PL line.
    Lookup: all TB rows whose coa_code maps to the given note_ref via CoA master.
    """
    from app.models import TrialBalance, CoAMaster
    from app.models.client import CustomCoACode, Client
    from app.models import Project

    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(404, "Project not found")

    # Find all CoA codes that have this note_ref
    note_codes = {c.code for c in db.query(CoAMaster).filter(CoAMaster.note_ref == note_ref).all()}
    # Also custom codes for this client
    custom = db.query(CustomCoACode).filter(
        CustomCoACode.client_id == proj.client_id,
        CustomCoACode.note_ref == note_ref
    ).all()
    note_codes.update(c.code for c in custom)

    if not note_codes:
        return {"note_ref": note_ref, "ledgers": [], "total_cy": 0, "total_py": 0}

    # Fetch matching TB rows
    rows = db.query(TrialBalance).filter(
        TrialBalance.project_id == project_id,
        TrialBalance.coa_code.in_(list(note_codes))
    ).all()

    ledgers = []
    total_cy = 0.0
    total_py = 0.0
    for r in rows:
        cy = r.cy_net
        py = r.py_net
        total_cy += cy or 0
        total_py += py or 0
        ledgers.append({
            "ledger_name": r.ledger_name,
            "coa_code": r.coa_code,
            "cy_net": cy,
            "py_net": py,
        })

    return {
        "note_ref": note_ref,
        "ledgers": ledgers,
        "total_cy": total_cy,
        "total_py": total_py,
    }
