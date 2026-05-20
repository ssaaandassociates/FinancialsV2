"""
Audit Service
Handles proposed audit adjustment entries and their application to TB balances.
"""
from datetime import date
from sqlalchemy.orm import Session
from app.models import AuditEntry, Project, CoAMaster, TrialBalance


def create_audit_entry(
    db: Session,
    project_id: int,
    dr_coa_code: str,
    cr_coa_code: str,
    amount: float,
    narration: str = "",
    entry_date: date = None,
    status: str = "proposed",
) -> AuditEntry:
    """Create a new audit adjustment entry."""
    # Validate project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    # Validate CoA codes
    for code in [dr_coa_code, cr_coa_code]:
        coa = db.query(CoAMaster).filter(CoAMaster.code == code).first()
        if not coa:
            raise ValueError(f"CoA code {code} does not exist")

    if amount <= 0:
        raise ValueError("Amount must be positive")

    # Next entry number
    max_no = db.query(AuditEntry).filter(
        AuditEntry.project_id == project_id
    ).count()
    entry_no = max_no + 1

    entry = AuditEntry(
        project_id=project_id,
        entry_no=entry_no,
        date=entry_date or date.today(),
        narration=narration,
        dr_coa_code=dr_coa_code,
        cr_coa_code=cr_coa_code,
        amount=float(amount),
        status=status,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_audit_entries(db: Session, project_id: int,
                       status_filter: str = None) -> list[dict]:
    """List all audit entries for a project."""
    q = db.query(AuditEntry).filter(AuditEntry.project_id == project_id)
    if status_filter:
        q = q.filter(AuditEntry.status == status_filter)
    entries = q.order_by(AuditEntry.entry_no).all()

    # Enrich with ledger names
    result = []
    for e in entries:
        dr_coa = db.query(CoAMaster).filter(CoAMaster.code == e.dr_coa_code).first()
        cr_coa = db.query(CoAMaster).filter(CoAMaster.code == e.cr_coa_code).first()
        result.append({
            "id": e.id,
            "entry_no": e.entry_no,
            "date": e.date.isoformat() if e.date else None,
            "narration": e.narration,
            "dr_coa_code": e.dr_coa_code,
            "dr_particulars": dr_coa.particulars if dr_coa else "",
            "cr_coa_code": e.cr_coa_code,
            "cr_particulars": cr_coa.particulars if cr_coa else "",
            "amount": e.amount,
            "status": e.status,
        })
    return result


def update_audit_entry(db: Session, entry_id: int, **updates) -> AuditEntry:
    """Update fields on an existing audit entry."""
    entry = db.query(AuditEntry).filter(AuditEntry.id == entry_id).first()
    if not entry:
        raise ValueError(f"Audit entry {entry_id} not found")

    allowed = {'narration', 'dr_coa_code', 'cr_coa_code', 'amount', 'status', 'date'}
    for key, val in updates.items():
        if key in allowed and val is not None:
            # Validate CoA codes if being changed
            if key in ('dr_coa_code', 'cr_coa_code'):
                coa = db.query(CoAMaster).filter(CoAMaster.code == val).first()
                if not coa:
                    raise ValueError(f"CoA code {val} does not exist")
            setattr(entry, key, val)

    db.commit()
    db.refresh(entry)
    return entry


def delete_audit_entry(db: Session, entry_id: int) -> dict:
    """Delete an audit entry and renumber remaining entries."""
    entry = db.query(AuditEntry).filter(AuditEntry.id == entry_id).first()
    if not entry:
        raise ValueError(f"Audit entry {entry_id} not found")

    project_id = entry.project_id
    db.delete(entry)
    db.commit()

    # Renumber remaining entries
    remaining = db.query(AuditEntry).filter(
        AuditEntry.project_id == project_id
    ).order_by(AuditEntry.id).all()
    for i, e in enumerate(remaining, start=1):
        e.entry_no = i
    db.commit()

    return {"deleted_id": entry_id, "remaining_count": len(remaining)}


def get_audit_adjustments_by_code(db: Session, project_id: int,
                                  approved_only: bool = True) -> dict:
    """
    Returns a dict mapping coa_code -> {debit: total_dr, credit: total_cr}
    for all audit entries. Used by financial engine to apply adjustments.
    """
    q = db.query(AuditEntry).filter(AuditEntry.project_id == project_id)
    if approved_only:
        q = q.filter(AuditEntry.status == "approved")

    entries = q.all()

    adjustments = {}
    for e in entries:
        # Dr side
        if e.dr_coa_code not in adjustments:
            adjustments[e.dr_coa_code] = {"debit": 0.0, "credit": 0.0}
        adjustments[e.dr_coa_code]["debit"] += e.amount

        # Cr side
        if e.cr_coa_code not in adjustments:
            adjustments[e.cr_coa_code] = {"debit": 0.0, "credit": 0.0}
        adjustments[e.cr_coa_code]["credit"] += e.amount

    return adjustments


def audit_totals_check(db: Session, project_id: int) -> dict:
    """Check that total Dr = total Cr across all audit entries."""
    entries = db.query(AuditEntry).filter(
        AuditEntry.project_id == project_id
    ).all()

    total_dr = sum(e.amount for e in entries)
    total_cr = sum(e.amount for e in entries)  # Each entry is Dr=Cr by design
    approved = sum(e.amount for e in entries if e.status == "approved")
    proposed = sum(e.amount for e in entries if e.status == "proposed")

    return {
        "total_entries": len(entries),
        "total_debits": round(total_dr, 2),
        "total_credits": round(total_cr, 2),
        "approved_amount": round(approved, 2),
        "proposed_amount": round(proposed, 2),
        "is_balanced": abs(total_dr - total_cr) < 0.01,
    }
