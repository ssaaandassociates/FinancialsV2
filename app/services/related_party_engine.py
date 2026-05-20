"""
Related Party Engine (AS-18)
Handles:
- Party master CRUD (KMP, Relatives, Entities, Holding/Sub)
- Transaction matrix (Purchase/Sale/Loan/Remuneration etc × party categories)
- Aggregated disclosure output
"""
from sqlalchemy.orm import Session
from app.models import RelatedParty, RPTransaction


# Standard transaction types for the matrix
TRANSACTION_TYPES = [
    "Purchase of Goods", "Sale of Goods",
    "Services Rendered", "Services Received",
    "Loans Given", "Loans Taken",
    "Interest Paid", "Interest Received",
    "Remuneration", "Sitting Fees",
    "Rent Paid", "Rent Received",
    "Commission", "Guarantee Given",
    "Outstanding Receivable", "Outstanding Payable",
]

PARTY_CATEGORIES = ["KMP", "Relative of KMP", "Entity", "Holding/Sub"]


def add_related_party(db: Session, project_id: int, name: str,
                      category: str, relationship: str = "",
                      pan_cin: str = "") -> RelatedParty:
    party = RelatedParty(
        project_id=project_id, name=name,
        category=category, relationship=relationship,
        pan_cin=pan_cin,
    )
    db.add(party)
    db.commit()
    db.refresh(party)
    return party


def list_related_parties(db: Session, project_id: int) -> list[dict]:
    parties = db.query(RelatedParty).filter(
        RelatedParty.project_id == project_id
    ).order_by(RelatedParty.category, RelatedParty.name).all()
    return [
        {
            "id": p.id, "name": p.name, "category": p.category,
            "relationship": p.relationship, "pan_cin": p.pan_cin,
        }
        for p in parties
    ]


def add_rp_transaction(db: Session, project_id: int, party_id: int,
                       transaction_type: str, cy_amount: float = 0,
                       py_amount: float = 0) -> RPTransaction:
    # Check if already exists - update instead of duplicate
    existing = db.query(RPTransaction).filter(
        RPTransaction.project_id == project_id,
        RPTransaction.party_id == party_id,
        RPTransaction.transaction_type == transaction_type,
    ).first()

    if existing:
        existing.cy_amount = cy_amount
        existing.py_amount = py_amount
        db.commit()
        db.refresh(existing)
        return existing

    txn = RPTransaction(
        project_id=project_id, party_id=party_id,
        transaction_type=transaction_type,
        cy_amount=cy_amount, py_amount=py_amount,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def generate_rp_disclosure(db: Session, project_id: int) -> dict:
    """
    Generate the full Related Party disclosure:
    1. Party list grouped by category
    2. Transaction matrix: txn_type × category with CY/PY totals
    """
    parties = db.query(RelatedParty).filter(
        RelatedParty.project_id == project_id
    ).all()

    transactions = db.query(RPTransaction).filter(
        RPTransaction.project_id == project_id
    ).all()

    # Build party lookup
    party_map = {p.id: p for p in parties}

    # Party list grouped by category
    party_list = {}
    for p in parties:
        cat = p.category or "Other"
        if cat not in party_list:
            party_list[cat] = []
        party_list[cat].append({
            "name": p.name, "relationship": p.relationship,
            "pan_cin": p.pan_cin,
        })

    # Transaction matrix: txn_type → {category → {cy, py}}
    matrix = {}
    for txn_type in TRANSACTION_TYPES:
        matrix[txn_type] = {}
        for cat in PARTY_CATEGORIES:
            matrix[txn_type][cat] = {"cy": 0, "py": 0}

    for txn in transactions:
        party = party_map.get(txn.party_id)
        if not party:
            continue
        cat = party.category or "Other"
        if cat not in PARTY_CATEGORIES:
            cat = "Entity"
        if txn.transaction_type in matrix:
            matrix[txn.transaction_type][cat]["cy"] += txn.cy_amount or 0
            matrix[txn.transaction_type][cat]["py"] += txn.py_amount or 0

    # Add row totals
    for txn_type in matrix:
        total_cy = sum(matrix[txn_type][cat]["cy"] for cat in PARTY_CATEGORIES)
        total_py = sum(matrix[txn_type][cat]["py"] for cat in PARTY_CATEGORIES)
        matrix[txn_type]["Total"] = {"cy": total_cy, "py": total_py}

    return {
        "parties": party_list,
        "matrix": matrix,
        "transaction_types": TRANSACTION_TYPES,
        "categories": PARTY_CATEGORIES,
    }
