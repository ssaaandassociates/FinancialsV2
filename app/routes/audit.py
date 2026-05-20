"""Audit routes - manage proposed audit adjustment entries"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import audit_service

router = APIRouter()


class AuditCreate(BaseModel):
    project_id: int
    dr_coa_code: str
    cr_coa_code: str
    amount: float
    narration: str = ""
    entry_date: date | None = None
    status: str = "proposed"


class AuditUpdate(BaseModel):
    narration: str | None = None
    dr_coa_code: str | None = None
    cr_coa_code: str | None = None
    amount: float | None = None
    status: str | None = None
    entry_date: date | None = None


@router.post("/audit/")
def create_audit(payload: AuditCreate, db: Session = Depends(get_db)):
    """Create new audit adjustment entry."""
    try:
        e = audit_service.create_audit_entry(
            db,
            project_id=payload.project_id,
            dr_coa_code=payload.dr_coa_code,
            cr_coa_code=payload.cr_coa_code,
            amount=payload.amount,
            narration=payload.narration,
            entry_date=payload.entry_date,
            status=payload.status,
        )
        return {
            "id": e.id,
            "entry_no": e.entry_no,
            "status": "created",
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/audit/{project_id}")
def list_audit(project_id: int, status: str = None, db: Session = Depends(get_db)):
    """List audit entries for a project."""
    return audit_service.list_audit_entries(db, project_id, status_filter=status)


@router.put("/audit/{entry_id}")
def update_audit(entry_id: int, payload: AuditUpdate, db: Session = Depends(get_db)):
    """Update an audit entry."""
    try:
        updates = payload.model_dump(exclude_none=True)
        # Map entry_date to 'date' field
        if 'entry_date' in updates:
            updates['date'] = updates.pop('entry_date')
        e = audit_service.update_audit_entry(db, entry_id, **updates)
        return {"id": e.id, "status": "updated"}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.delete("/audit/{entry_id}")
def delete_audit(entry_id: int, db: Session = Depends(get_db)):
    """Delete an audit entry."""
    try:
        return audit_service.delete_audit_entry(db, entry_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/audit/{project_id}/check")
def audit_check(project_id: int, db: Session = Depends(get_db)):
    """Audit totals balance check."""
    return audit_service.audit_totals_check(db, project_id)
