"""
Routes for master-data template downloads — Section 10 V9
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import templates_service

router = APIRouter()


@router.get("/templates/master-blank")
def download_blank_master():
    """Download a blank master-data template with sample rows."""
    buf = templates_service.generate_blank_master_template()
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="SSAA_Master_Template_Blank.xlsx"'},
    )


@router.get("/templates/master-current/{client_id}")
def download_current_master(client_id: int, db: Session = Depends(get_db)):
    """Export current client master data as Excel."""
    try:
        buf, safe_name = templates_service.generate_current_master_template(db, client_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="SSAA_Master_{safe_name}.xlsx"'},
    )


@router.get("/templates/ppe")
def download_ppe_template():
    """Download a PPE schedule template pre-filled with standard CoA codes."""
    buf = templates_service.generate_ppe_template()
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="SSAA_PPE_Template.xlsx"'},
    )
