"""Export route - download the full 20-sheet financial statement Excel"""
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import export_engine

router = APIRouter()


@router.get("/export/{project_id}/excel")
def export_excel(project_id: int, db: Session = Depends(get_db)):
    """Generate and download the complete 20-sheet financial statement Excel."""
    try:
        filepath = export_engine.export_full_excel(db, project_id)
        filename = os.path.basename(filepath)
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Export failed: {str(e)}")


@router.get("/export/{project_id}/generate")
def generate_excel(project_id: int, db: Session = Depends(get_db)):
    """Generate Excel file and return filepath (without downloading)."""
    try:
        filepath = export_engine.export_full_excel(db, project_id)
        return {
            "status": "generated",
            "filepath": filepath,
            "filename": os.path.basename(filepath),
            "size_bytes": os.path.getsize(filepath),
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Export failed: {str(e)}")


@router.get("/export/{project_id}/pdf")
def export_pdf(project_id: int, db: Session = Depends(get_db)):
    """Generate PDF from the Excel output using openpyxl data."""
    try:
        # Generate Excel first, then convert key sheets to PDF
        from app.services.pdf_export import generate_pdf
        filepath = generate_pdf(db, project_id)
        filename = os.path.basename(filepath)
        return FileResponse(path=filepath, filename=filename, media_type="application/pdf")
    except ImportError:
        raise HTTPException(501, "PDF export requires reportlab. Install: pip install reportlab")
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"PDF export failed: {str(e)}")


@router.get("/export/{project_id}/docx")
def export_docx(project_id: int, db: Session = Depends(get_db)):
    """Generate Word document of financial statements."""
    try:
        from app.services.docx_export import generate_docx
        filepath = generate_docx(db, project_id)
        filename = os.path.basename(filepath)
        return FileResponse(path=filepath, filename=filename,
                            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    except ImportError:
        raise HTTPException(501, "Word export requires python-docx. Install: pip install python-docx")
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Word export failed: {str(e)}")
