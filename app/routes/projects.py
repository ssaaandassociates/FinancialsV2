"""Projects & Clients API routes"""
import os
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import project_service

router = APIRouter()


class ClientCreate(BaseModel):
    name: str
    cin: str | None = None
    pan: str | None = None
    gstin: str | None = None
    principal_activity: str | None = None
    date_of_incorporation: date | None = None
    registered_office: str | None = None
    auditor_name: str | None = None
    auditor_frn: str | None = None
    auditor_membership_no: str | None = None
    authorized_capital: float | None = 0
    paid_up_capital: float | None = 0
    face_value: float | None = 10
    tax_rate: float | None = 0.2987
    authorised_shares: int | None = 0
    authorised_capital: float | None = 0
    subscribed_shares: int | None = 0
    subscribed_capital: float | None = 0
    paidup_shares: int | None = 0
    paidup_capital: float | None = 0


class ClientUpdate(BaseModel):
    name: str | None = None
    cin: str | None = None
    pan: str | None = None
    gstin: str | None = None
    principal_activity: str | None = None
    date_of_incorporation: date | None = None
    registered_office: str | None = None
    auditor_name: str | None = None
    auditor_frn: str | None = None
    auditor_membership_no: str | None = None
    authorized_capital: float | None = None
    paid_up_capital: float | None = None
    face_value: float | None = None
    tax_rate: float | None = None
    authorised_shares: int | None = None
    authorised_capital: float | None = None
    subscribed_shares: int | None = None
    subscribed_capital: float | None = None
    paidup_shares: int | None = None
    paidup_capital: float | None = None


class ProjectCreate(BaseModel):
    client_id: int
    financial_year: str
    bs_date_cy: date | None = None
    bs_date_py: date | None = None
    rounding: str = "Rupees"
    company_type: str = "trading"
    policy_changed: str = "no"


# ----- CLIENT ROUTES -----
@router.post("/clients/")
def create_client(payload: ClientCreate, db: Session = Depends(get_db)):
    try:
        c = project_service.create_client(db, **payload.model_dump(exclude_none=True))
        return {"id": c.id, "name": c.name, "status": "created"}
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/clients/")
def list_clients(db: Session = Depends(get_db)):
    return project_service.list_clients(db)


@router.get("/clients/{client_id}")
def get_client(client_id: int, db: Session = Depends(get_db)):
    try:
        return project_service.get_client(db, client_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.put("/clients/{client_id}")
def update_client(client_id: int, payload: ClientUpdate, db: Session = Depends(get_db)):
    try:
        c = project_service.update_client(db, client_id, **payload.model_dump(exclude_none=True))
        return {"id": c.id, "name": c.name, "status": "updated"}
    except ValueError as e:
        raise HTTPException(404, str(e))


# ----- PROJECT ROUTES -----
@router.post("/projects/")
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    try:
        p = project_service.create_project(db, **payload.model_dump())
        return {"id": p.id, "financial_year": p.financial_year, "status": p.status}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/projects/{project_id}/duplicate")
def duplicate_project(project_id: int, db: Session = Depends(get_db)):
    """Duplicate a project with ALL data (TB, mapping, audit, ageing, PPE, etc.) under V+1."""
    from app.models import (Project, TrialBalance, AuditEntry)
    from app.models.supplementary import (AgeingData, RelatedParty, RPTransaction,
        DisclosureData, ClosingStock, PPEScheduleEntry, NoteEnrichment,
        SigningBlock, CompanyProfile, RatioPriorYear, ShareEvent, Shareholder)

    src = db.query(Project).filter(Project.id == project_id).first()
    if not src:
        raise HTTPException(404, "Source project not found")

    # Find next version
    existing = db.query(Project).filter(
        Project.client_id == src.client_id,
        Project.financial_year == src.financial_year,
    ).count()
    new_version = existing + 1

    # Create new project (copy of source)
    new_proj = Project(
        client_id=src.client_id,
        financial_year=src.financial_year,
        version=new_version,
        bs_date_cy=src.bs_date_cy,
        bs_date_py=src.bs_date_py,
        rounding=src.rounding,
        company_type=src.company_type,
        status="setup",
        policy_changed=src.policy_changed,
    )
    db.add(new_proj); db.commit(); db.refresh(new_proj)

    # Copy TB
    for r in db.query(TrialBalance).filter(TrialBalance.project_id == project_id).all():
        db.add(TrialBalance(project_id=new_proj.id, ledger_name=r.ledger_name,
            tally_group=r.tally_group, cy_debit=r.cy_debit, cy_credit=r.cy_credit,
            py_debit=r.py_debit, py_credit=r.py_credit, coa_code=r.coa_code))
    # Copy audit entries
    for r in db.query(AuditEntry).filter(AuditEntry.project_id == project_id).all():
        db.add(AuditEntry(project_id=new_proj.id, entry_no=r.entry_no, date=r.date,
            narration=r.narration, dr_coa_code=r.dr_coa_code, cr_coa_code=r.cr_coa_code,
            amount=r.amount, status=r.status, approved_by=r.approved_by))
    # Copy ageing
    for r in db.query(AgeingData).filter(AgeingData.project_id == project_id).all():
        db.add(AgeingData(project_id=new_proj.id, ageing_type=r.ageing_type,
            party_name=r.party_name, is_disputed=r.is_disputed, is_doubtful=r.is_doubtful,
            is_msme=r.is_msme, bucket_1=r.bucket_1, bucket_2=r.bucket_2,
            bucket_3=r.bucket_3, bucket_4=r.bucket_4, bucket_5=r.bucket_5, period=r.period))
    # Copy RP parties + transactions
    rp_id_map = {}
    for r in db.query(RelatedParty).filter(RelatedParty.project_id == project_id).all():
        new_rp = RelatedParty(project_id=new_proj.id, name=r.name, category=r.category,
            relationship=r.relationship, pan_cin=r.pan_cin)
        db.add(new_rp); db.flush()
        rp_id_map[r.id] = new_rp.id
    for r in db.query(RPTransaction).filter(RPTransaction.project_id == project_id).all():
        new_party_id = rp_id_map.get(r.party_id)
        if new_party_id:
            db.add(RPTransaction(project_id=new_proj.id, party_id=new_party_id,
                transaction_type=r.transaction_type, cy_amount=r.cy_amount, py_amount=r.py_amount))
    # Copy closing stock, PPE, etc.
    for r in db.query(ClosingStock).filter(ClosingStock.project_id == project_id).all():
        db.add(ClosingStock(project_id=new_proj.id, stock_type=r.stock_type,
            coa_code=r.coa_code, cy_amount=r.cy_amount, py_amount=r.py_amount))
    for r in db.query(PPEScheduleEntry).filter(PPEScheduleEntry.project_id == project_id).all():
        new_ppe = PPEScheduleEntry(project_id=new_proj.id, asset_type=r.asset_type,
            asset_class=r.asset_class, coa_code=r.coa_code)
        for f in ['gross_opening','gross_additions','gross_disposals','dep_opening','dep_for_year','dep_on_disposals',
                   'py_gross_opening','py_gross_additions','py_gross_disposals','py_dep_opening','py_dep_for_year','py_dep_on_disposals']:
            setattr(new_ppe, f, getattr(r, f, 0))
        db.add(new_ppe)
    # Copy enrichments
    for r in db.query(NoteEnrichment).filter(NoteEnrichment.project_id == project_id).all():
        db.add(NoteEnrichment(project_id=new_proj.id, note_ref=r.note_ref,
            field_key=r.field_key, field_type=r.field_type, field_label=r.field_label,
            value_text=r.value_text, value_amount=r.value_amount, value_bool=r.value_bool))
    # Copy disclosures
    for r in db.query(DisclosureData).filter(DisclosureData.project_id == project_id).all():
        db.add(DisclosureData(project_id=new_proj.id, disclosure_ref=r.disclosure_ref,
            sub_ref=r.sub_ref, particulars=r.particulars, cy_amount=r.cy_amount,
            py_amount=r.py_amount, text_value=r.text_value))

    db.commit()
    return {"id": new_proj.id, "financial_year": new_proj.financial_year,
            "version": new_proj.version, "status": "duplicated"}


@router.get("/projects/")
def list_projects(client_id: int = None, db: Session = Depends(get_db)):
    return project_service.list_projects(db, client_id=client_id)


@router.get("/projects/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    try:
        return project_service.get_project(db, project_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


# ============= DIRECTORS (with is_kmp, signs_financials) =============

class DirectorInput(BaseModel):
    client_id: int
    name: str
    din: str | None = None
    designation: str = "Director"
    pan: str | None = None
    is_kmp: bool = False
    signs_financials: bool = False


@router.post("/directors/")
def add_director(payload: DirectorInput, db: Session = Depends(get_db)):
    from app.models.client import Director
    d = Director(client_id=payload.client_id, name=payload.name,
                 din=payload.din, designation=payload.designation,
                 pan=payload.pan, is_kmp=payload.is_kmp,
                 signs_financials=payload.signs_financials)
    db.add(d); db.commit(); db.refresh(d)
    return {"id": d.id, "name": d.name, "din": d.din}


@router.get("/directors/{client_id}")
def list_directors(client_id: int, db: Session = Depends(get_db)):
    from app.models.client import Director
    dirs = db.query(Director).filter(Director.client_id == client_id, Director.is_active == True).all()
    return [{"id": d.id, "name": d.name, "din": d.din, "designation": d.designation,
             "is_kmp": d.is_kmp, "signs_financials": d.signs_financials, "pan": d.pan} for d in dirs]


@router.put("/directors/{director_id}")
def update_director(director_id: int, payload: DirectorInput, db: Session = Depends(get_db)):
    from app.models.client import Director
    d = db.query(Director).filter(Director.id == director_id).first()
    if not d: raise HTTPException(404, "Director not found")
    for k in ['name', 'din', 'designation', 'pan', 'is_kmp', 'signs_financials']:
        v = getattr(payload, k, None)
        if v is not None:
            setattr(d, k, v)
    db.commit()
    return {"id": d.id, "status": "updated"}


@router.delete("/directors/{director_id}")
def delete_director(director_id: int, db: Session = Depends(get_db)):
    from app.models.client import Director
    d = db.query(Director).filter(Director.id == director_id).first()
    if d: d.is_active = False; db.commit()
    return {"status": "deleted"}


# ============= KMP (auto from directors with is_kmp=True) =============

@router.get("/kmp/{client_id}")
def list_kmp(client_id: int, db: Session = Depends(get_db)):
    from app.models.client import Director
    dirs = db.query(Director).filter(
        Director.client_id == client_id, Director.is_active == True, Director.is_kmp == True
    ).all()
    return [{"id": d.id, "name": d.name, "designation": d.designation, "pan": d.pan, "din": d.din} for d in dirs]


# ============= CLIENT-LEVEL SHAREHOLDERS =============

class ShareholderInput(BaseModel):
    client_id: int
    name: str
    no_of_shares_cy: int = 0
    no_of_shares_py: int = 0
    face_value: float = 10
    is_promoter: bool = False
    is_director: bool = False
    din: str | None = None
    pan: str | None = None


@router.post("/client-shareholders/")
def add_client_shareholder(payload: ShareholderInput, db: Session = Depends(get_db)):
    from app.models.client import ClientShareholder, Director, Client
    client = db.query(Client).filter(Client.id == payload.client_id).first()
    if not client: raise HTTPException(404, "Client not found")

    sh = ClientShareholder(
        client_id=payload.client_id, name=payload.name,
        no_of_shares_cy=payload.no_of_shares_cy, no_of_shares_py=payload.no_of_shares_py,
        face_value=payload.face_value or client.face_value,
        is_promoter=payload.is_promoter, is_director=payload.is_director,
        din=payload.din, pan=payload.pan,
    )
    db.add(sh); db.commit(); db.refresh(sh)

    # If is_director, auto-add to directors table
    if payload.is_director and payload.din:
        existing = db.query(Director).filter(
            Director.client_id == payload.client_id, Director.din == payload.din
        ).first()
        if not existing:
            d = Director(client_id=payload.client_id, name=payload.name,
                         din=payload.din, designation="Director", is_kmp=True)
            db.add(d); db.commit()

    # Recompute % holdings
    _recompute_holdings(db, payload.client_id)
    return {"id": sh.id, "name": sh.name, "share_capital_cy": sh.share_capital_cy}


@router.get("/client-shareholders/{client_id}")
def list_client_shareholders(client_id: int, db: Session = Depends(get_db)):
    from app.models.client import ClientShareholder, Client
    client = db.query(Client).filter(Client.id == client_id).first()
    shs = db.query(ClientShareholder).filter(ClientShareholder.client_id == client_id).all()

    total_cy = sum(s.no_of_shares_cy for s in shs)
    total_py = sum(s.no_of_shares_py for s in shs)
    paidup = client.paidup_shares or client.paid_up_capital / (client.face_value or 10) if client else 0

    return {
        "shareholders": [
            {"id": s.id, "name": s.name, "no_of_shares_cy": s.no_of_shares_cy,
             "no_of_shares_py": s.no_of_shares_py, "face_value": s.face_value,
             "share_capital_cy": s.share_capital_cy, "share_capital_py": s.share_capital_py,
             "pct_holding_cy": s.pct_holding_cy, "pct_holding_py": s.pct_holding_py,
             "is_promoter": s.is_promoter, "is_director": s.is_director, "din": s.din}
            for s in shs
        ],
        "total_shares_cy": total_cy, "total_shares_py": total_py,
        "validation": "ok" if total_cy <= (paidup or 999999999) else f"WARNING: Shareholders ({total_cy}) exceed paid-up ({paidup})",
    }


@router.put("/client-shareholders/{shareholder_id}")
def update_client_shareholder(shareholder_id: int, payload: ShareholderInput, db: Session = Depends(get_db)):
    from app.models.client import ClientShareholder, Director
    s = db.query(ClientShareholder).filter(ClientShareholder.id == shareholder_id).first()
    if not s:
        raise HTTPException(404, "Shareholder not found")
    for k in ['name','no_of_shares_cy','no_of_shares_py','face_value','is_promoter','is_director','din','pan']:
        v = getattr(payload, k, None)
        if v is not None:
            setattr(s, k, v)
    db.commit()
    # Auto-add to directors if is_director became True
    if payload.is_director and payload.din:
        existing = db.query(Director).filter(
            Director.client_id == s.client_id, Director.din == payload.din
        ).first()
        if not existing:
            d = Director(client_id=s.client_id, name=payload.name,
                         din=payload.din, designation="Director", is_kmp=True)
            db.add(d); db.commit()
    _recompute_holdings(db, s.client_id)
    return {"id": s.id, "status": "updated"}


@router.delete("/client-shareholders/{shareholder_id}")
def delete_client_shareholder(shareholder_id: int, db: Session = Depends(get_db)):
    from app.models.client import ClientShareholder
    s = db.query(ClientShareholder).filter(ClientShareholder.id == shareholder_id).first()
    if s:
        cid = s.client_id
        db.delete(s); db.commit()
        _recompute_holdings(db, cid)
    return {"status": "deleted"}


def _recompute_holdings(db, client_id):
    from app.models.client import ClientShareholder
    shs = db.query(ClientShareholder).filter(ClientShareholder.client_id == client_id).all()
    total_cy = sum(s.no_of_shares_cy for s in shs)
    total_py = sum(s.no_of_shares_py for s in shs)
    for s in shs:
        s.pct_holding_cy = round((s.no_of_shares_cy / total_cy * 100) if total_cy > 0 else 0, 2)
        s.pct_holding_py = round((s.no_of_shares_py / total_py * 100) if total_py > 0 else 0, 2)
    db.commit()


# ============= CUSTOM COA CODES (client level) =============

class CustomCoAInput(BaseModel):
    client_id: int
    code: str
    particulars: str
    parent_code: str | None = None
    nature: str | None = "Dr"
    fs_type: str | None = "BS"
    note_ref: str | None = None


@router.post("/custom-coa/")
def add_custom_coa(payload: CustomCoAInput, db: Session = Depends(get_db)):
    from app.models.client import CustomCoACode
    c = CustomCoACode(**payload.model_dump())
    db.add(c); db.commit(); db.refresh(c)
    return {"id": c.id, "code": c.code, "particulars": c.particulars}


@router.get("/custom-coa/{client_id}")
def list_custom_coa(client_id: int, db: Session = Depends(get_db)):
    from app.models.client import CustomCoACode
    codes = db.query(CustomCoACode).filter(CustomCoACode.client_id == client_id).all()
    return [{"id": c.id, "code": c.code, "particulars": c.particulars,
             "parent_code": c.parent_code, "fs_type": c.fs_type} for c in codes]


@router.delete("/custom-coa/{code_id}")
def delete_custom_coa(code_id: int, db: Session = Depends(get_db)):
    from app.models.client import CustomCoACode
    c = db.query(CustomCoACode).filter(CustomCoACode.id == code_id).first()
    if c: db.delete(c); db.commit()
    return {"status": "deleted"}


# ============= PROJECT UPDATE / DELETE =============

class ProjectUpdate(BaseModel):
    company_type: str | None = None
    rounding: str | None = None
    financial_year: str | None = None
    bs_date_cy: date | None = None
    bs_date_py: date | None = None


@router.put("/projects/{project_id}")
def update_project(project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)):
    from app.models import Project
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(404, "Project not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    db.commit()
    return {"id": p.id, "status": "updated"}


@router.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    from app.models import (Project, TrialBalance, AuditEntry, PPEScheduleEntry,
        ClosingStock, NoteEnrichment, SigningBlock, CompanyProfile, RatioPriorYear)
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(404, "Project not found")
    # Delete all project-level data
    for model in [TrialBalance, AuditEntry, PPEScheduleEntry, ClosingStock,
                   NoteEnrichment, SigningBlock, CompanyProfile, RatioPriorYear]:
        db.query(model).filter(model.project_id == project_id).delete()
    db.delete(p)
    db.commit()
    return {"status": "deleted"}


# ============= CLIENT DELETE =============

@router.delete("/clients/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    from app.models import Client, Project
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(404, "Client not found")
    # Check if projects exist
    proj_count = db.query(Project).filter(Project.client_id == client_id).count()
    if proj_count > 0:
        raise HTTPException(400, f"Cannot delete client with {proj_count} existing project(s). Delete projects first.")
    db.delete(client)
    db.commit()
    return {"status": "deleted"}


# ============= H8: DATABASE BACKUP & RESTORE =============

@router.get("/db/backup")
def backup_db():
    """H8: Download SQLite database file as backup."""
    import shutil
    from fastapi.responses import FileResponse
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "tce.db")
    if not os.path.exists(db_path):
        raise HTTPException(404, "Database not found")
    backup_path = db_path + ".backup"
    shutil.copy2(db_path, backup_path)
    return FileResponse(backup_path, filename="tce_backup.db",
                        media_type="application/octet-stream")


@router.post("/db/restore")
async def restore_db(file: UploadFile = File(...)):
    """H8: Restore SQLite database from uploaded backup."""
    import shutil
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "tce.db")
    # Save current as .pre-restore
    if os.path.exists(db_path):
        shutil.copy2(db_path, db_path + ".pre-restore")
    contents = await file.read()
    with open(db_path, "wb") as f:
        f.write(contents)
    return {"status": "restored", "size_bytes": len(contents)}


# ============= CLIENT-LEVEL POLICIES CRUD =============

class ClientPolicyInput(BaseModel):
    client_id: int
    policy_number: int
    title: str
    body: str


@router.post("/client-policies/")
def add_client_policy(payload: ClientPolicyInput, db: Session = Depends(get_db)):
    from app.models.client import ClientPolicy
    p = ClientPolicy(**payload.model_dump(), is_active=True)
    db.add(p); db.commit(); db.refresh(p)
    return {"id": p.id, "title": p.title}


@router.get("/client-policies/{client_id}")
def list_client_policies(client_id: int, db: Session = Depends(get_db)):
    from app.models.client import ClientPolicy
    pols = db.query(ClientPolicy).filter(
        ClientPolicy.client_id == client_id, ClientPolicy.is_active == True
    ).order_by(ClientPolicy.policy_number).all()
    return [{"id": p.id, "policy_number": p.policy_number, "title": p.title,
             "body": p.body, "is_active": p.is_active} for p in pols]


@router.put("/client-policies/{policy_id}")
def update_client_policy(policy_id: int, payload: ClientPolicyInput, db: Session = Depends(get_db)):
    from app.models.client import ClientPolicy
    p = db.query(ClientPolicy).filter(ClientPolicy.id == policy_id).first()
    if not p:
        raise HTTPException(404, "Policy not found")
    p.policy_number = payload.policy_number
    p.title = payload.title
    p.body = payload.body
    db.commit()
    return {"id": p.id, "status": "updated"}


@router.delete("/client-policies/{policy_id}")
def delete_client_policy(policy_id: int, db: Session = Depends(get_db)):
    from app.models.client import ClientPolicy
    p = db.query(ClientPolicy).filter(ClientPolicy.id == policy_id).first()
    if p: p.is_active = False; db.commit()
    return {"status": "deleted"}
