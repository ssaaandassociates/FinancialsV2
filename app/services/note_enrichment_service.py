"""
Note Enrichment Service — Context-Aware with Predefined Paragraphs

Design principles:
1. CONTEXT-AWARE: Each note checks what TB codes are mapped — only shows relevant fields
2. PREDEFINED PARAGRAPHS: Standard boilerplate text as dropdown options
3. TB VALUES SHOWN: User sees the amounts alongside disclosure inputs
4. NIL AUTO-FILL: If no data for a disclosure, auto-fill standard nil paragraph

Each field now has:
  - field_key, field_type, field_label (same as before)
  - predefined_options: list of standard text options for dropdown
  - depends_on_codes: list of CoA code prefixes — field only shown if TB has these codes
"""
from sqlalchemy.orm import Session
from app.models import NoteEnrichment, TrialBalance, CoAMaster


# ============================================================
# PREDEFINED PARAGRAPHS — Standard boilerplate per field
# ============================================================

PREDEFINED = {
    # Share Capital
    "rights_restrictions": [
        "The Company has only one class of equity shares having face value of Rs.10/- per share. Each holder of equity share is entitled to one vote per share. In the event of liquidation, the equity shareholders are eligible to receive the remaining assets in proportion to their shareholding.",
        "The Company has two classes of shares: Equity shares of Rs.10/- each and Preference shares of Rs.100/- each. Equity shareholders are entitled to one vote per share.",
    ],
    "convertible_terms": [
        "The Company has not issued any convertible securities during the year.",
        "The Company has issued Compulsory Convertible Preference Shares (CCPS) which are convertible into equity shares at the option of the holder within 10 years from the date of allotment.",
    ],
    "shares_reserved": [
        "No shares are reserved for issue under options, contracts or commitments for the sale of shares.",
    ],
    # Borrowings
    "security_nature": [
        "Secured by hypothecation of plant & machinery and personal guarantee of the director.",
        "Secured by mortgage of immovable property situated at registered office and personal guarantee of directors.",
        "Secured by pledge of fixed deposits held with the lending bank.",
        "Secured by first charge on all current assets and movable fixed assets of the company.",
    ],
    "repayment_terms": [
        "Repayable in 60 equal monthly installments commencing from the date of first disbursement.",
        "Repayable in 36 equal monthly installments.",
        "Repayable on demand.",
        "Bullet repayment at maturity after 5 years from date of disbursement.",
    ],
    "director_guarantee_details": [
        "The loan is guaranteed by personal guarantee of the Managing Director of the company.",
        "No personal guarantee has been given by any director.",
    ],
    "default_period": [
        "There is no default in repayment of loans and interest as at the Balance Sheet date.",
    ],
    "bond_debenture_terms": [
        "The Company has not issued any bonds or debentures during the year or in any previous year.",
    ],
    # Trade Payables / MSME
    "msme_nil": [
        "There are no Micro, Small and Medium Enterprises, to whom the Company owes dues, which are outstanding for more than 45 days as at the Balance Sheet date. This information as required to be disclosed under the Micro, Small and Medium Enterprises Development Act, 2006 has been determined to the extent such parties have been identified on the basis of information available with the Company.",
    ],
    # Inventories
    "inventory_valuation_mode": [
        "Inventories are valued at lower of cost and net realizable value. Cost is determined on First-In-First-Out (FIFO) basis.",
        "Inventories are valued at lower of cost and net realizable value. Cost is determined on Weighted Average basis.",
        "Raw Materials and Stores & Spares are valued at cost on FIFO basis. Work-in-Progress is valued at cost of materials plus appropriate share of production overheads. Finished Goods are valued at lower of cost and net realizable value.",
    ],
    # Investments
    "trade_vs_other": [
        "All investments are classified as non-trade investments.",
        "Investments are classified as Trade and Other investments based on the purpose for which they are held.",
    ],
    # Contingent Liabilities
    "contingent_nil": [
        "There are no contingent liabilities as at the Balance Sheet date.",
        "Claims against the company not acknowledged as debts.",
    ],
    # Additional Disclosures — Standard NIL paras
    "benami_nil": [
        "No proceedings have been initiated or are pending against the Company for holding any Benami property under the Benami Transactions (Prohibition) Act, 1988 (45 of 1988) and the rules made thereunder.",
    ],
    "struck_off_nil": [
        "The Company has not entered into any transactions with companies struck off under Section 248 of the Companies Act, 2013 or Section 560 of the Companies Act, 1956.",
    ],
    "wilful_defaulter_nil": [
        "The Company has not been declared as a wilful defaulter by any bank or financial institution or government or any government authority.",
    ],
    "crypto_nil": [
        "The Company has not traded or invested in any cryptocurrency or virtual currency during the financial year.",
    ],
    "undisclosed_income_nil": [
        "There is no income surrendered or disclosed as income during the current or previous year in the tax assessments under the Income Tax Act, 1961 that has not been recorded in the books of account.",
    ],
    "charges_nil": [
        "There are no charges or satisfaction yet to be registered with the Registrar of Companies beyond the statutory period.",
    ],
    "layers_nil": [
        "The Company has complied with the number of layers prescribed under clause (87) of section 2 of the Companies Act, 2013 read with the Companies (Restriction on number of Layers) Rules, 2017.",
        "The Company does not have any subsidiary or holding company and hence the provisions relating to number of layers are not applicable.",
    ],
    "borrowed_funds_nil": [
        "The Company has not advanced or loaned or invested funds to any other person(s) or entity(ies), including foreign entities (Intermediaries) with the understanding that the Intermediary shall directly or indirectly lend or invest in other persons or entities identified in any manner by or on behalf of the Company (Ultimate Beneficiaries) or provide any guarantee, security or the like to or on behalf of the Ultimate Beneficiaries.",
    ],
    "title_deeds_nil": [
        "The title deeds of all immovable properties (other than properties where the Company is the lessee and the lease agreements are duly executed in favour of the lessee) are held in the name of the Company.",
    ],
    "csr_nil": [
        "The provisions of Section 135 of the Companies Act, 2013 relating to Corporate Social Responsibility are not applicable to the Company.",
    ],
    "regrouping": [
        "Previous year's figures have been regrouped/reclassified wherever necessary to correspond with the current year's classification/disclosure.",
    ],
    "going_concern": [
        "The financial statements have been prepared on a going concern basis. The management has assessed the Company's ability to continue as a going concern and is satisfied that the Company has the resources to continue in business for the foreseeable future.",
    ],
}


# ============================================================
# NOTE FIELDS — Now with predefined options + code dependencies
# Format: (field_key, field_type, label, predefined_key_or_None, depends_on_code_prefixes_or_None)
# ============================================================

NOTE_FIELDS = {
    "A": [
        ("rights_restrictions", "text", "Rights, preferences & restrictions attached to shares", "rights_restrictions", None),
        ("convertible_terms", "text", "Terms of convertible securities", "convertible_terms", None),
        ("shares_reserved", "text", "Shares reserved for issue under options/contracts", "shares_reserved", None),
        ("calls_unpaid_directors", "amount", "Calls unpaid by directors/officers (Rs.)", None, None),
        ("shares_allotted_without_cash_5yr", "text", "5-year: Shares allotted without cash payment", None, None),
        ("bonus_shares_5yr", "text", "5-year: Bonus shares allotted", None, None),
        ("shares_bought_back_5yr", "text", "5-year: Shares bought back", None, None),
    ],
    "B": [
        ("reserve_movement", "text", "Details of reserve movements (additions/deductions)", None, ["BS-EL-01-02"]),
    ],
    "C": [
        ("security_nature", "text", "Nature of security for each secured loan", "security_nature", ["BS-EL-03-01"]),
        ("repayment_terms", "text", "Terms of repayment", "repayment_terms", ["BS-EL-03-01"]),
        ("director_guarantee_details", "text", "Director/promoter guarantee details", "director_guarantee_details", ["BS-EL-03-01"]),
        ("default_period", "text", "Default in repayment (if any)", "default_period", ["BS-EL-03-01"]),
        ("bond_debenture_terms", "text", "Bonds/Debentures terms", "bond_debenture_terms", ["BS-EL-03-01"]),
    ],
    "F": [
        ("st_security_nature", "text", "Nature of security for short-term borrowings", "security_nature", ["BS-EL-04-01"]),
        ("st_repayment_terms", "text", "Terms of repayment", "repayment_terms", ["BS-EL-04-01"]),
        ("st_default", "text", "Default in repayment (if any)", "default_period", ["BS-EL-04-01"]),
    ],
    "FA": [
        ("msme_disclosure", "text", "MSME disclosure under Sec 22 MSMED Act", "msme_nil", ["BS-EL-04-02"]),
    ],
    "I": [
        ("ppe_revaluation", "text", "Revaluation of assets (if any)", None, ["BS-AS-01-01"]),
        ("ppe_leased", "text", "Assets held under lease (if any)", None, ["BS-AS-01-01"]),
    ],
    "K": [
        ("investment_classification", "text", "Trade vs Other investment classification", "trade_vs_other", ["BS-AS-01-02"]),
        ("quoted_details", "text", "Quoted investments: aggregate amount and market value", None, ["BS-AS-01-02"]),
        ("investment_details", "text", "Details of investments in subsidiary/associate/JV", None, ["BS-AS-01-02"]),
    ],
    "O": [
        ("inventory_valuation", "text", "Mode of valuation of inventories", "inventory_valuation_mode", ["BS-AS-02-02"]),
        ("goods_in_transit", "text", "Goods-in-transit details (if any)", None, ["BS-AS-02-02"]),
    ],
    "P": [
        ("tr_dues_directors", "amount", "Trade receivables: Dues from directors/officers (Rs.)", None, ["BS-AS-02-03"]),
    ],
    "Q": [
        ("deposits_lien", "text", "Deposits under lien / held as margin money (if any)", None, ["BS-AS-02-04"]),
    ],
    "OE": [
        ("auditor_remuneration", "text", "Auditor's remuneration breakup (Audit fee / Tax audit / Other services / Reimbursement)", None, ["PL-04-07"]),
    ],
}


# ============================================================
# SERVICE FUNCTIONS
# ============================================================

def seed_note_fields(db: Session, project_id: int, note_ref: str) -> int:
    """Seed enrichment fields for a specific note."""
    existing = db.query(NoteEnrichment).filter(
        NoteEnrichment.project_id == project_id,
        NoteEnrichment.note_ref == note_ref,
    ).count()
    if existing > 0:
        return existing

    fields = NOTE_FIELDS.get(note_ref, [])
    for field_key, field_type, field_label, _, _ in fields:
        db.add(NoteEnrichment(
            project_id=project_id,
            note_ref=note_ref,
            field_key=field_key,
            field_type=field_type,
            field_label=field_label,
        ))
    db.commit()
    return len(fields)


def seed_all_notes(db: Session, project_id: int) -> int:
    total = 0
    for note_ref in NOTE_FIELDS:
        total += seed_note_fields(db, project_id, note_ref)
    return total


def _get_tb_code_prefixes(db: Session, project_id: int) -> set:
    """Get all CoA code prefixes that have TB data mapped."""
    rows = db.query(TrialBalance.coa_code).filter(
        TrialBalance.project_id == project_id,
        TrialBalance.coa_code.isnot(None),
    ).distinct().all()
    prefixes = set()
    for (code,) in rows:
        if code:
            parts = code.split("-")
            for i in range(2, len(parts) + 1):
                prefixes.add("-".join(parts[:i]))
    return prefixes


def _get_tb_ledgers_for_note(db: Session, project_id: int, code_prefixes: list) -> list:
    """Get TB ledger names + amounts for codes matching given prefixes."""
    rows = db.query(TrialBalance).filter(
        TrialBalance.project_id == project_id,
        TrialBalance.coa_code.isnot(None),
    ).all()

    matches = []
    for r in rows:
        if r.coa_code and any(r.coa_code.startswith(p) for p in code_prefixes):
            matches.append({
                "ledger": r.ledger_name,
                "coa_code": r.coa_code,
                "cy_net": round((r.cy_debit or 0) - (r.cy_credit or 0), 2),
                "py_net": round((r.py_debit or 0) - (r.py_credit or 0), 2),
            })
    return matches


# Map note_ref → CoA code prefixes for TB context
NOTE_CODE_MAP = {
    "A": ["BS-EL-01-01"],
    "B": ["BS-EL-01-02"],
    "C": ["BS-EL-03-01"],           # Long-Term Borrowings
    "D": ["BS-EL-03-03"],           # Other LT Liabilities
    "E": ["BS-EL-03-04"],           # LT Provisions
    "F": ["BS-EL-04-01"],           # ST Borrowings
    "FA": ["BS-EL-04-02"],          # Trade Payables
    "G": ["BS-EL-04-03"],           # Other Current Liabilities
    "H": ["BS-EL-04-04"],           # ST Provisions
    "I": ["BS-AS-01-01"],           # Tangible Assets
    "J": ["BS-AS-01-01-10", "BS-AS-01-01-11", "BS-AS-01-01-12", "BS-AS-01-01-13", "BS-AS-01-01-14"],
    "K": ["BS-AS-01-02"],           # NC Investments
    "L": ["BS-AS-01-03"],           # LT Loans & Advances
    "M": ["BS-AS-01-04"],           # Other NC Assets
    "N": ["BS-AS-02-01"],           # Current Investments
    "O": ["BS-AS-02-02"],           # Inventories
    "P": ["BS-AS-02-03"],           # Trade Receivables
    "Q": ["BS-AS-02-04"],           # Cash & Equivalents
    "R": ["BS-AS-02-05"],           # ST Loans & Advances
    "S": ["BS-AS-02-06"],           # Other Current Assets
    "Rev": ["PL-01"],
    "OI": ["PL-02"],
    "Emp": ["PL-04-04"],
    "Fin": ["PL-04-05"],
    "Dep": ["PL-04-06"],
    "OE": ["PL-04-07"],
    "Tax": ["PL-04-08"],
}


def get_note_enrichments(db: Session, project_id: int, note_ref: str = None) -> dict:
    """
    Get context-aware enrichment data.
    Returns: {note_ref: {has_tb_data, tb_ledgers, fields[], predefined_options}}
    """
    seed_all_notes(db, project_id)
    active_prefixes = _get_tb_code_prefixes(db, project_id)

    q = db.query(NoteEnrichment).filter(NoteEnrichment.project_id == project_id)
    if note_ref:
        q = q.filter(NoteEnrichment.note_ref == note_ref)
    rows = q.order_by(NoteEnrichment.note_ref, NoteEnrichment.id).all()

    result = {}

    # Process all notes that have fields defined
    for nref in (NOTE_FIELDS if not note_ref else {note_ref: NOTE_FIELDS.get(note_ref, [])}):
        code_prefixes = NOTE_CODE_MAP.get(nref, [])
        has_tb_data = any(
            any(p.startswith(cp) or cp.startswith(p) for cp in code_prefixes)
            for p in active_prefixes
        ) if code_prefixes else True

        tb_ledgers = _get_tb_ledgers_for_note(db, project_id, code_prefixes) if has_tb_data else []

        note_rows = [r for r in rows if r.note_ref == nref]
        note_fields_def = NOTE_FIELDS.get(nref, [])

        fields = []
        for r in note_rows:
            # Find the field definition to get predefined options and code deps
            fdef = next((f for f in note_fields_def if f[0] == r.field_key), None)
            predefined_key = fdef[3] if fdef and len(fdef) > 3 else None
            depends_codes = fdef[4] if fdef and len(fdef) > 4 else None

            # Check if field is relevant based on code dependencies
            is_relevant = True
            if depends_codes:
                is_relevant = any(
                    any(p.startswith(dc) for p in active_prefixes)
                    for dc in depends_codes
                )

            fields.append({
                "id": r.id,
                "field_key": r.field_key,
                "field_type": r.field_type,
                "field_label": r.field_label,
                "value_text": r.value_text,
                "value_amount": r.value_amount,
                "value_bool": r.value_bool,
                "has_value": r.value_text is not None or r.value_amount is not None or r.value_bool is not None,
                "predefined_options": PREDEFINED.get(predefined_key, []) if predefined_key else [],
                "is_relevant": is_relevant,
            })

        result[nref] = {
            "has_tb_data": has_tb_data,
            "tb_ledgers": tb_ledgers,
            "fields": fields,
        }

    return result


def update_enrichment(db: Session, enrichment_id: int, **updates) -> NoteEnrichment:
    """Update a single enrichment field value."""
    field = db.query(NoteEnrichment).filter(NoteEnrichment.id == enrichment_id).first()
    if not field:
        raise ValueError(f"Enrichment {enrichment_id} not found")
    if "value_text" in updates:
        field.value_text = updates["value_text"]
    if "value_amount" in updates:
        field.value_amount = updates["value_amount"]
    if "value_bool" in updates:
        field.value_bool = updates["value_bool"]
    db.commit()
    db.refresh(field)
    return field


def get_enrichment_value(db: Session, project_id: int, note_ref: str, field_key: str):
    """Get a specific enrichment field value."""
    field = db.query(NoteEnrichment).filter(
        NoteEnrichment.project_id == project_id,
        NoteEnrichment.note_ref == note_ref,
        NoteEnrichment.field_key == field_key,
    ).first()
    if not field:
        return None
    if field.field_type == "amount":
        return field.value_amount
    return field.value_text
