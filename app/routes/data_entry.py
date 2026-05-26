"""Data entry routes - Closing Stock, PPE Schedule, Note Enrichment, Signing Block"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import closing_stock_service, ppe_service, note_enrichment_service
from app.models import SigningBlock

router = APIRouter()


# ============= CLOSING STOCK =============

class ClosingStockInput(BaseModel):
    project_id: int
    stock_type: str
    cy_amount: float = 0
    py_amount: float = 0


@router.get("/closing-stock/{project_id}/types")
def get_stock_types(project_id: int, db: Session = Depends(get_db)):
    """Get applicable stock types based on company type."""
    from app.models import Project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    return {
        "company_type": project.company_type,
        "stock_types": closing_stock_service.get_applicable_stock_types(project.company_type),
    }


@router.post("/closing-stock/")
def save_closing_stock(payload: ClosingStockInput, db: Session = Depends(get_db)):
    """Save closing stock value."""
    try:
        entry = closing_stock_service.save_closing_stock(
            db, payload.project_id, payload.stock_type,
            payload.cy_amount, payload.py_amount
        )
        return {"id": entry.id, "stock_type": entry.stock_type, "cy": entry.cy_amount}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/closing-stock/{project_id}")
def get_closing_stock(project_id: int, db: Session = Depends(get_db)):
    """Get all closing stock entries."""
    return closing_stock_service.get_closing_stock(db, project_id)


# ============= PPE SCHEDULE =============

class PPEInput(BaseModel):
    gross_opening: float | None = None
    gross_additions: float | None = None
    gross_disposals: float | None = None
    dep_opening: float | None = None
    dep_for_year: float | None = None
    dep_on_disposals: float | None = None
    py_gross_opening: float | None = None
    py_gross_additions: float | None = None
    py_gross_disposals: float | None = None
    py_dep_opening: float | None = None
    py_dep_for_year: float | None = None
    py_dep_on_disposals: float | None = None


@router.get("/ppe/{project_id}")
def get_ppe(project_id: int, db: Session = Depends(get_db)):
    """Get PPE schedule with validation."""
    return ppe_service.get_ppe_schedule(db, project_id)


@router.put("/ppe/{entry_id}")
def update_ppe(entry_id: int, payload: PPEInput, db: Session = Depends(get_db)):
    """Update a PPE entry."""
    try:
        entry = ppe_service.save_ppe_entry(db, entry_id, **payload.model_dump(exclude_none=True))
        return {
            "id": entry.id, "asset_class": entry.asset_class,
            "gross_closing": entry.gross_closing, "dep_closing": entry.dep_closing,
            "net_cy": entry.net_cy,
        }
    except ValueError as e:
        raise HTTPException(404, str(e))


# ============= NOTE ENRICHMENT =============

class EnrichmentUpdate(BaseModel):
    value_text: str | None = None
    value_amount: float | None = None
    value_bool: bool | None = None


@router.get("/note-enrichment/{project_id}")
def get_all_enrichments(project_id: int, db: Session = Depends(get_db)):
    """Get all note enrichment data."""
    return note_enrichment_service.get_note_enrichments(db, project_id)


@router.get("/note-enrichment/{project_id}/{note_ref}")
def get_note_enrichment(project_id: int, note_ref: str, db: Session = Depends(get_db)):
    """Get enrichment data for a specific note."""
    return note_enrichment_service.get_note_enrichments(db, project_id, note_ref)


@router.put("/note-enrichment/{enrichment_id}")
def update_enrichment(enrichment_id: int, payload: EnrichmentUpdate,
                      db: Session = Depends(get_db)):
    """Update a note enrichment field."""
    try:
        field = note_enrichment_service.update_enrichment(
            db, enrichment_id, **payload.model_dump(exclude_none=True)
        )
        return {"id": field.id, "note": field.note_ref, "key": field.field_key, "status": "updated"}
    except ValueError as e:
        raise HTTPException(404, str(e))


# ============= SIGNING BLOCK =============

class SigningInput(BaseModel):
    project_id: int
    auditor_firm: str | None = None
    auditor_frn: str | None = None
    partner_name: str | None = None
    partner_membership_no: str | None = None
    partner_udin: str | None = None
    director1_name: str | None = None
    director1_din: str | None = None
    director1_designation: str | None = "Director"
    director2_name: str | None = None
    director2_din: str | None = None
    director2_designation: str | None = "Director"
    place: str | None = None
    signing_date: date | None = None


@router.get("/signing/{project_id}")
def get_signing(project_id: int, db: Session = Depends(get_db)):
    """Get signing block data."""
    sb = db.query(SigningBlock).filter(SigningBlock.project_id == project_id).first()
    if not sb:
        return {"project_id": project_id, "status": "not_set"}
    return {
        "id": sb.id,
        "auditor_firm": sb.auditor_firm, "auditor_frn": sb.auditor_frn,
        "partner_name": sb.partner_name, "partner_membership_no": sb.partner_membership_no,
        "partner_udin": sb.partner_udin,
        "director1_name": sb.director1_name, "director1_din": sb.director1_din,
        "director1_designation": sb.director1_designation,
        "director2_name": sb.director2_name, "director2_din": sb.director2_din,
        "director2_designation": sb.director2_designation,
        "place": sb.place,
        "signing_date": str(sb.signing_date) if sb.signing_date else None,
    }


@router.post("/signing/")
def save_signing(payload: SigningInput, db: Session = Depends(get_db)):
    """Save/update signing block."""
    existing = db.query(SigningBlock).filter(
        SigningBlock.project_id == payload.project_id
    ).first()

    data = payload.model_dump(exclude_none=True)
    data.pop("project_id", None)

    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
        db.commit()
        return {"id": existing.id, "status": "updated"}
    else:
        sb = SigningBlock(project_id=payload.project_id, **data)
        db.add(sb)
        db.commit()
        db.refresh(sb)
        return {"id": sb.id, "status": "created"}


@router.post("/signing/{project_id}/auto-populate")
def auto_populate_signing(project_id: int, db: Session = Depends(get_db)):
    """
    Auto-fill signing block from client master:
    - Auditor from Client.auditor_name / .auditor_frn / .auditor_membership_no
    - Director1 + Director2 from Directors where signs_financials=True
    """
    from app.models import Project, Client, Director

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return {"error": "project_not_found"}
    client = db.query(Client).filter(Client.id == project.client_id).first()
    if not client:
        return {"error": "client_not_found"}

    signing_directors = (
        db.query(Director)
        .filter(Director.client_id == client.id, Director.signs_financials == True)
        .order_by(Director.id)
        .all()
    )

    sb = db.query(SigningBlock).filter(SigningBlock.project_id == project_id).first()
    created = False
    if not sb:
        sb = SigningBlock(project_id=project_id)
        db.add(sb)
        created = True

    # Auditor
    sb.auditor_firm = client.auditor_name or sb.auditor_firm
    sb.auditor_frn = client.auditor_frn or sb.auditor_frn
    sb.partner_membership_no = client.auditor_membership_no or sb.partner_membership_no

    # Directors
    if len(signing_directors) >= 1:
        d1 = signing_directors[0]
        sb.director1_name = d1.name
        sb.director1_din = d1.din
        sb.director1_designation = d1.designation or "Director"
    if len(signing_directors) >= 2:
        d2 = signing_directors[1]
        sb.director2_name = d2.name
        sb.director2_din = d2.din
        sb.director2_designation = d2.designation or "Director"

    db.commit()
    db.refresh(sb)

    return {
        "id": sb.id,
        "status": "created" if created else "updated",
        "auditor_firm": sb.auditor_firm,
        "auditor_frn": sb.auditor_frn,
        "partner_membership_no": sb.partner_membership_no,
        "director1_name": sb.director1_name,
        "director1_din": sb.director1_din,
        "director2_name": sb.director2_name,
        "director2_din": sb.director2_din,
        "signing_directors_found": len(signing_directors),
        "auditor_found": bool(client.auditor_name),
    }


# ============= RATIO PY-1 VALUES =============

class RatioPY1Input(BaseModel):
    project_id: int
    total_equity_py1: float = 0
    total_debt_py1: float = 0
    total_current_assets_py1: float = 0
    total_current_liabilities_py1: float = 0
    trade_receivables_py1: float = 0
    trade_payables_py1: float = 0
    inventory_py1: float = 0
    net_worth_py1: float = 0
    capital_employed_py1: float = 0


@router.get("/ratio-py1/{project_id}")
def get_ratio_py1(project_id: int, db: Session = Depends(get_db)):
    from app.models import RatioPriorYear
    r = db.query(RatioPriorYear).filter(RatioPriorYear.project_id == project_id).first()
    if not r:
        return {"project_id": project_id, "status": "not_set"}
    return {k: getattr(r, k) for k in [
        "total_equity_py1", "total_debt_py1", "total_current_assets_py1",
        "total_current_liabilities_py1", "trade_receivables_py1", "trade_payables_py1",
        "inventory_py1", "net_worth_py1", "capital_employed_py1",
    ]}


@router.post("/ratio-py1/")
def save_ratio_py1(payload: RatioPY1Input, db: Session = Depends(get_db)):
    from app.models import RatioPriorYear
    existing = db.query(RatioPriorYear).filter(RatioPriorYear.project_id == payload.project_id).first()
    data = payload.model_dump()
    data.pop("project_id")
    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
        db.commit()
        return {"status": "updated"}
    else:
        r = RatioPriorYear(project_id=payload.project_id, **data)
        db.add(r); db.commit()
        return {"status": "created"}


# ============= COMPANY PROFILE QUESTIONNAIRE =============

class ProfileInput(BaseModel):
    project_id: int
    has_forex_transactions: bool = False
    has_related_party_txns: bool = True
    has_csr_obligation: bool = False
    has_subsidiary_holding: bool = False
    has_contingent_liabilities: bool = False
    has_msme_vendors: bool = False
    has_cwip: bool = False
    has_intangible_under_dev: bool = False
    has_loans_to_directors: bool = False
    has_scheme_of_arrangement: bool = False
    has_crypto_transactions: bool = False
    has_benami_property: bool = False


@router.get("/profile/{project_id}")
def get_profile(project_id: int, db: Session = Depends(get_db)):
    from app.models import CompanyProfile
    p = db.query(CompanyProfile).filter(CompanyProfile.project_id == project_id).first()
    if not p:
        return {"project_id": project_id, "status": "not_set"}
    return {k: getattr(p, k) for k in [
        "has_forex_transactions", "has_related_party_txns", "has_csr_obligation",
        "has_subsidiary_holding", "has_contingent_liabilities", "has_msme_vendors",
        "has_cwip", "has_intangible_under_dev", "has_loans_to_directors",
        "has_scheme_of_arrangement", "has_crypto_transactions", "has_benami_property",
    ]}


@router.post("/profile/")
def save_profile(payload: ProfileInput, db: Session = Depends(get_db)):
    from app.models import CompanyProfile
    existing = db.query(CompanyProfile).filter(CompanyProfile.project_id == payload.project_id).first()
    data = payload.model_dump()
    data.pop("project_id")
    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
        db.commit()
        return {"status": "updated"}
    else:
        p = CompanyProfile(project_id=payload.project_id, **data)
        db.add(p); db.commit()
        return {"status": "created"}
