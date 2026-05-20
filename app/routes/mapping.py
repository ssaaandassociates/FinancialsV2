"""Mapping routes - auto-map TB ledgers to CoA codes"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import mapping_service
from app.models import CoAMaster

router = APIRouter()


class ManualMap(BaseModel):
    tb_row_id: int
    coa_code: str


@router.post("/map/{project_id}/auto")
def auto_map(project_id: int, force: bool = False, db: Session = Depends(get_db)):
    """Auto-map all TB ledgers for a project."""
    try:
        return mapping_service.auto_map_project(db, project_id, force=force)
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/map/manual")
def manual_map(payload: ManualMap, db: Session = Depends(get_db)):
    """Manually assign a CoA code to a TB row."""
    try:
        return mapping_service.set_manual_mapping(db, payload.tb_row_id, payload.coa_code)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/map/{project_id}/summary")
def mapping_summary(project_id: int, db: Session = Depends(get_db)):
    """Get mapping completion statistics."""
    return mapping_service.get_mapping_summary(db, project_id)


@router.get("/coa/")
def list_coa(fs_type: str = None, db: Session = Depends(get_db)):
    """List all CoA master codes (optionally filter by BS/PL)."""
    q = db.query(CoAMaster)
    if fs_type:
        q = q.filter(CoAMaster.fs_type == fs_type.upper())
    codes = q.order_by(CoAMaster.code).all()
    return [
        {
            "code": c.code,
            "level": c.level,
            "particulars": c.particulars,
            "schedule_ref": c.schedule_ref,
            "nature": c.nature,
            "fs_type": c.fs_type,
            "note_ref": c.note_ref,
            "tally_group": c.tally_group,
        }
        for c in codes
    ]
