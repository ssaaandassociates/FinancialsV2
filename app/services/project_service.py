"""
Client and Project Service
Handles multi-client support and project (FY) management.
"""
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.models import Client, Project


def create_client(db: Session, name: str, **kwargs) -> Client:
    """Create a new client."""
    client = Client(name=name, **kwargs)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def list_clients(db: Session) -> list[dict]:
    """List all clients with project counts."""
    clients = db.query(Client).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "cin": c.cin,
            "auditor_name": c.auditor_name,
            "project_count": len(c.projects),
        }
        for c in clients
    ]


def get_client(db: Session, client_id: int) -> dict:
    """Get full client details."""
    c = db.query(Client).filter(Client.id == client_id).first()
    if not c:
        raise ValueError(f"Client {client_id} not found")
    return {
        "id": c.id,
        "name": c.name,
        "cin": c.cin,
        "date_of_incorporation": c.date_of_incorporation.isoformat() if c.date_of_incorporation else None,
        "registered_office": c.registered_office,
        "auditor_name": c.auditor_name,
        "auditor_frn": c.auditor_frn,
        "authorized_capital": c.authorized_capital,
        "paid_up_capital": c.paid_up_capital,
        "face_value": c.face_value,
        "tax_rate": c.tax_rate,
        "projects": [{"id": p.id, "fy": p.financial_year, "status": p.status} for p in c.projects],
    }


def update_client(db: Session, client_id: int, **updates) -> Client:
    """Update client fields."""
    c = db.query(Client).filter(Client.id == client_id).first()
    if not c:
        raise ValueError(f"Client {client_id} not found")

    allowed = {'name', 'cin', 'date_of_incorporation', 'registered_office',
               'auditor_name', 'auditor_frn', 'authorized_capital',
               'paid_up_capital', 'face_value', 'tax_rate'}
    for k, v in updates.items():
        if k in allowed and v is not None:
            if k == 'date_of_incorporation' and isinstance(v, str):
                v = datetime.fromisoformat(v).date()
            setattr(c, k, v)

    db.commit()
    db.refresh(c)
    return c


def create_project(db: Session, client_id: int, financial_year: str,
                   bs_date_cy: date = None, bs_date_py: date = None,
                   rounding: str = "Rupees", company_type: str = "trading") -> Project:
    """Create a new project (FY) for a client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise ValueError(f"Client {client_id} not found")

    project = Project(
        client_id=client_id,
        financial_year=financial_year,
        bs_date_cy=bs_date_cy,
        bs_date_py=bs_date_py,
        rounding=rounding,
        company_type=company_type,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def list_projects(db: Session, client_id: int = None) -> list[dict]:
    """List all projects (optionally filtered by client)."""
    q = db.query(Project)
    if client_id:
        q = q.filter(Project.client_id == client_id)
    projects = q.all()
    return [
        {
            "id": p.id,
            "client_id": p.client_id,
            "client_name": p.client.name if p.client else None,
            "financial_year": p.financial_year,
            "bs_date_cy": p.bs_date_cy.isoformat() if p.bs_date_cy else None,
            "bs_date_py": p.bs_date_py.isoformat() if p.bs_date_py else None,
            "rounding": p.rounding,
            "status": p.status,
        }
        for p in projects
    ]


def get_project(db: Session, project_id: int) -> dict:
    """Get full project details."""
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise ValueError(f"Project {project_id} not found")
    return {
        "id": p.id,
        "client_id": p.client_id,
        "client_name": p.client.name if p.client else None,
        "financial_year": p.financial_year,
        "bs_date_cy": p.bs_date_cy.isoformat() if p.bs_date_cy else None,
        "bs_date_py": p.bs_date_py.isoformat() if p.bs_date_py else None,
        "rounding": p.rounding,
        "company_type": p.company_type,
        "status": p.status,
        "tb_row_count": len(p.trial_balances),
        "audit_entry_count": len(p.audit_entries),
    }
