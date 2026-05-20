"""
Mapping Service
Auto-suggests CoA codes for TB ledgers based on:
1. Exact ledger name match (if exists in history)
2. Tally group → CoA code mapping rules
3. Keyword matching in ledger name
"""
from sqlalchemy.orm import Session
from app.models import TrialBalance, TBMapping, CoAMaster


# Keyword → CoA code hints for ledger name matching
LEDGER_KEYWORDS = {
    # Liabilities
    'share capital': 'BS-EL-01-01-02',
    'equity share': 'BS-EL-01-01-02',
    'preference share': 'BS-EL-01-01-05',
    'securities premium': 'BS-EL-01-02-03',
    'general reserve': 'BS-EL-01-02-07',
    'profit & loss': 'BS-EL-01-02-09',
    'retained earnings': 'BS-EL-01-02-09',
    'term loan': 'BS-EL-03-01-03',
    'cash credit': 'BS-EL-04-01-01',
    'overdraft': 'BS-EL-04-01-01',
    'tds payable': 'BS-EL-04-03-10',
    'gst payable': 'BS-EL-04-03-10',
    'pf payable': 'BS-EL-04-03-10',
    'esi payable': 'BS-EL-04-03-10',
    'duties & taxes': 'BS-EL-04-03-10',
    'provision for tax': 'BS-EL-04-04-02',
    'provision for gratuity': 'BS-EL-03-04-01',
    'unpaid dividend': 'BS-EL-04-03-06',
    # Assets
    'land': 'BS-AS-01-01-01',
    'building': 'BS-AS-01-01-03',
    'plant': 'BS-AS-01-01-04',
    'machinery': 'BS-AS-01-01-04',
    'furniture': 'BS-AS-01-01-05',
    'vehicle': 'BS-AS-01-01-06',
    'car': 'BS-AS-01-01-06',
    'office equipment': 'BS-AS-01-01-07',
    'computer': 'BS-AS-01-01-08',
    'software': 'BS-AS-01-01-11',
    'goodwill': 'BS-AS-01-01-10',
    'capital wip': 'BS-AS-01-01-15',
    'cwip': 'BS-AS-01-01-15',
    'investment': 'BS-AS-01-02-02',
    'mutual fund': 'BS-AS-01-02-06',
    'security deposit': 'BS-AS-01-04-02',
    'raw material': 'BS-AS-02-02-01',
    'finished goods': 'BS-AS-02-02-03',
    'work in progress': 'BS-AS-02-02-02',
    'stock in trade': 'BS-AS-02-02-04',
    'stores & spares': 'BS-AS-02-02-05',
    'sundry debtor': 'BS-AS-02-03-01',
    'trade receivable': 'BS-AS-02-03-01',
    'debtor': 'BS-AS-02-03-01',
    'cash on hand': 'BS-AS-02-04-07',
    'cash in hand': 'BS-AS-02-04-07',
    'petty cash': 'BS-AS-02-04-07',
    'bank': 'BS-AS-02-04-01',
    'fixed deposit': 'BS-AS-02-04-02',
    'fdr': 'BS-AS-02-04-02',
    'advance tax': 'BS-AS-02-05-06',
    'tds receivable': 'BS-AS-02-05-06',
    'gst input': 'BS-AS-02-05-07',
    'gst input credit': 'BS-AS-02-05-07',
    'gst receivable': 'BS-AS-02-05-07',
    'input credit': 'BS-AS-02-05-07',
    'prepaid insurance': 'BS-AS-02-05-08',
    'prepaid': 'BS-AS-02-05-08',
    'advance to supplier': 'BS-AS-02-05-09',
    # Revenue
    'sales': 'PL-01-01',
    'revenue': 'PL-01-01',
    'service income': 'PL-01-03',
    'export': 'PL-01-04',
    'interest income': 'PL-02-02',
    'interest received': 'PL-02-02',
    'interest on fd': 'PL-02-01',
    'dividend income': 'PL-02-03',
    'dividend received': 'PL-02-03',
    'rent received': 'PL-02-06',
    'commission received': 'PL-02-08',
    # Expenses
    'purchase': 'PL-04-01-02',
    'raw material consumed': 'PL-04-01',
    'salary': 'PL-04-04-01',
    'salaries': 'PL-04-04-01',
    'wages': 'PL-04-04-01',
    'pf contribution': 'PL-04-04-02',
    'esi contribution': 'PL-04-04-02',
    'gratuity expense': 'PL-04-04-04',
    'staff welfare': 'PL-04-04-05',
    'director remuneration': 'PL-04-04-06',
    'interest expense': 'PL-04-05-01',
    'bank charges': 'PL-04-05-02',
    'interest on loan': 'PL-04-05-01',
    'depreciation': 'PL-04-06-01',
    'amortization': 'PL-04-06-02',
    'power and fuel': 'PL-04-07-02',
    'electricity': 'PL-04-07-02',
    'rent paid': 'PL-04-07-03',
    'rent expense': 'PL-04-07-03',
    'repair': 'PL-04-07-05',
    'insurance': 'PL-04-07-06',
    'rates and taxes': 'PL-04-07-07',
    'property tax': 'PL-04-07-07',
    'telephone': 'PL-04-07-08',
    'communication': 'PL-04-07-08',
    'travelling': 'PL-04-07-09',
    'conveyance': 'PL-04-07-09',
    'printing': 'PL-04-07-10',
    'stationery': 'PL-04-07-10',
    'legal': 'PL-04-07-11',
    'professional': 'PL-04-07-11',
    'audit fee': 'PL-04-07-12',
    'statutory audit': 'PL-04-07-12',
    'tax audit': 'PL-04-07-13',
    'bad debt': 'PL-04-07-17',
    'provision for doubtful': 'PL-04-07-18',
    'csr': 'PL-04-07-21',
    'donation': 'PL-04-07-22',
    'freight': 'PL-04-07-23',
    'commission paid': 'PL-04-07-24',
    'advertisement': 'PL-04-07-25',
    'sitting fee': 'PL-04-07-26',
    'current tax': 'PL-10-01',
    'income tax': 'PL-10-01',
    'deferred tax': 'PL-10-02',
    'mat credit': 'PL-10-03',
}


def suggest_by_tally_group(db: Session, tally_group: str) -> tuple[str | None, float]:
    """Return (coa_code, confidence) by looking up Tally group in mapping rules."""
    if not tally_group:
        return None, 0.0

    # Exact match first
    rule = db.query(TBMapping).filter(
        TBMapping.tally_group == tally_group
    ).order_by(TBMapping.confidence.desc()).first()

    if rule:
        return rule.suggested_coa_code, rule.confidence

    # Case-insensitive match
    group_lower = tally_group.lower().strip()
    all_rules = db.query(TBMapping).all()
    for rule in all_rules:
        if rule.tally_group.lower().strip() == group_lower:
            return rule.suggested_coa_code, rule.confidence

    return None, 0.0


def suggest_by_ledger_keywords(ledger_name: str) -> tuple[str | None, float]:
    """Suggest CoA based on keywords in ledger name."""
    if not ledger_name:
        return None, 0.0

    name_lower = ledger_name.lower()

    # Sort keywords by length descending (longer = more specific)
    sorted_keywords = sorted(LEDGER_KEYWORDS.items(), key=lambda x: -len(x[0]))

    for keyword, code in sorted_keywords:
        if keyword in name_lower:
            # Confidence based on keyword specificity
            confidence = min(0.9, 0.5 + len(keyword) / 40)
            return code, round(confidence, 2)

    return None, 0.0


def auto_map_project(db: Session, project_id: int, force: bool = False) -> dict:
    """
    Auto-map all TB ledgers for a project.

    Priority (each ledger):
    1. Keyword match in ledger name (most specific - e.g. "Depreciation" → PL-04-06-01)
    2. Tally group match (fallback - e.g. "Indirect Expenses" → PL-04-07-27 miscellaneous)

    This avoids the problem where all "Indirect Expenses" ledgers collapse to one code.
    - force=True: overwrite existing mappings
    - force=False: only map where coa_code is empty
    """
    rows = db.query(TrialBalance).filter(TrialBalance.project_id == project_id).all()

    mapped_by_keyword = 0
    mapped_by_group = 0
    unmapped = 0
    low_confidence = 0

    for row in rows:
        if row.coa_code and not force:
            continue

        # Try keyword FIRST (more specific)
        code, conf = suggest_by_ledger_keywords(row.ledger_name)
        source = "keyword"

        # Fall back to tally group
        if not code:
            code, conf = suggest_by_tally_group(db, row.tally_group)
            source = "group"

        if code:
            row.coa_code = code
            if source == "keyword":
                mapped_by_keyword += 1
            else:
                mapped_by_group += 1
            if conf < 0.7:
                low_confidence += 1
        else:
            unmapped += 1

    db.commit()

    return {
        "total_rows": len(rows),
        "mapped_by_keyword": mapped_by_keyword,
        "mapped_by_tally_group": mapped_by_group,
        "unmapped": unmapped,
        "low_confidence_warnings": low_confidence,
    }


def set_manual_mapping(db: Session, tb_row_id: int, coa_code: str) -> dict:
    """Manually assign a CoA code to a TB row."""
    row = db.query(TrialBalance).filter(TrialBalance.id == tb_row_id).first()
    if not row:
        raise ValueError(f"TB row {tb_row_id} not found")

    # Validate the CoA code exists
    coa = db.query(CoAMaster).filter(CoAMaster.code == coa_code).first()
    if not coa:
        raise ValueError(f"CoA code {coa_code} does not exist")

    row.coa_code = coa_code
    db.commit()

    return {
        "id": row.id,
        "ledger_name": row.ledger_name,
        "new_coa_code": coa_code,
        "particulars": coa.particulars,
    }


def get_mapping_summary(db: Session, project_id: int) -> dict:
    """Return mapping statistics for a project."""
    rows = db.query(TrialBalance).filter(TrialBalance.project_id == project_id).all()
    total = len(rows)
    mapped = sum(1 for r in rows if r.coa_code)
    unmapped = total - mapped

    return {
        "total_ledgers": total,
        "mapped": mapped,
        "unmapped": unmapped,
        "completion_pct": round((mapped / total * 100) if total > 0 else 0, 2),
    }
