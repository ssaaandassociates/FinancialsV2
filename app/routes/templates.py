"""
Routes for master-data + PPE template downloads AND imports.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import templates_service, templates_import_service

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


# ============= IMPORTS =============

@router.post("/templates/master-import/{client_id}")
async def import_master(
    client_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a filled master-data workbook (blank template or export-current).
    Upserts directors/shareholders/policies/custom-CoA by their natural keys
    and updates the Client row's fields from the Client Master sheet.
    """
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls", ".xlsm")):
        raise HTTPException(400, "Please upload an Excel file (.xlsx / .xlsm).")
    content = await file.read()
    try:
        result = templates_import_service.import_master_data(db, client_id, content)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(400, f"Import failed: {e}")
    return result


@router.post("/templates/ppe-import/{project_id}")
async def import_ppe(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a filled PPE schedule. Matches on (project_id, coa_code) and updates
    the 12 amount columns. Creates new rows if a code is not yet seeded.
    """
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls", ".xlsm")):
        raise HTTPException(400, "Please upload an Excel file (.xlsx / .xlsm).")
    content = await file.read()
    try:
        result = templates_import_service.import_ppe(db, project_id, content)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(400, f"Import failed: {e}")
    return result
