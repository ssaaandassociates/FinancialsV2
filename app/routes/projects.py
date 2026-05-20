"""Projects & Clients API routes"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
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
    authorized_capital: float | None = 0
    paid_up_capital: float | None = 0
    face_value: float | None = 10
    tax_rate: float | None = 0.2987


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
    authorized_capital: float | None = None
    paid_up_capital: float | None = None
    face_value: float | None = None
    tax_rate: float | None = None


class ProjectCreate(BaseModel):
    client_id: int
    financial_year: str
    bs_date_cy: date | None = None
    bs_date_py: date | None = None
    rounding: str = "Rupees"
    company_type: str = "trading"  # service / trading / manufacturing


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


@router.get("/projects/")
def list_projects(client_id: int = None, db: Session = Depends(get_db)):
    return project_service.list_projects(db, client_id=client_id)


@router.get("/projects/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    try:
        return project_service.get_project(db, project_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


# ============= DIRECTORS =============

class DirectorInput(BaseModel):
    client_id: int
    name: str
    din: str | None = None
    designation: str = "Director"

class KMPInput(BaseModel):
    client_id: int
    name: str
    designation: str = "CEO"
    pan: str | None = None


@router.post("/directors/")
def add_director(payload: DirectorInput, db: Session = Depends(get_db)):
    from app.models.client import Director
    d = Director(client_id=payload.client_id, name=payload.name,
                 din=payload.din, designation=payload.designation)
    db.add(d); db.commit(); db.refresh(d)
    return {"id": d.id, "name": d.name, "din": d.din}


@router.get("/directors/{client_id}")
def list_directors(client_id: int, db: Session = Depends(get_db)):
    from app.models.client import Director
    dirs = db.query(Director).filter(Director.client_id == client_id, Director.is_active == True).all()
    return [{"id": d.id, "name": d.name, "din": d.din, "designation": d.designation} for d in dirs]


@router.delete("/directors/{director_id}")
def delete_director(director_id: int, db: Session = Depends(get_db)):
    from app.models.client import Director
    d = db.query(Director).filter(Director.id == director_id).first()
    if d: d.is_active = False; db.commit()
    return {"status": "deleted"}


@router.post("/kmp/")
def add_kmp(payload: KMPInput, db: Session = Depends(get_db)):
    from app.models.client import KMP
    k = KMP(client_id=payload.client_id, name=payload.name,
            designation=payload.designation, pan=payload.pan)
    db.add(k); db.commit(); db.refresh(k)
    return {"id": k.id, "name": k.name}


@router.get("/kmp/{client_id}")
def list_kmp(client_id: int, db: Session = Depends(get_db)):
    from app.models.client import KMP
    kl = db.query(KMP).filter(KMP.client_id == client_id, KMP.is_active == True).all()
    return [{"id": k.id, "name": k.name, "designation": k.designation, "pan": k.pan} for k in kl]


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
