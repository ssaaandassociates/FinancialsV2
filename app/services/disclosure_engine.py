"""
Disclosure Engine
Handles:
- Additional Disclosures (A through T) per Schedule III
- Accounting Policies (customizable per project with defaults)
"""
from sqlalchemy.orm import Session
from app.models import DisclosureData, AccountingPolicy

# ============================================================
# DEFAULT ACCOUNTING POLICIES
# ============================================================
DEFAULT_POLICIES = [
    (1, "Basis of Preparation",
     "The financial statements are prepared under historical cost convention on accrual basis, "
     "in accordance with Indian GAAP and Accounting Standards specified u/s 133 of Companies Act 2013 "
     "read with Rule 7 of Companies (Accounts) Rules 2014."),
    (2, "Use of Estimates",
     "The preparation of financial statements requires management to make estimates and assumptions "
     "that affect the reported amounts. Actual results could differ from those estimates."),
    (3, "Revenue Recognition",
     "Revenue is recognized when significant risks and rewards of ownership are transferred to the buyer, "
     "the amount can be reliably measured, and it is probable that economic benefits will flow to the company."),
    (4, "Property, Plant and Equipment",
     "PPE is stated at cost less accumulated depreciation and impairment losses. Cost includes purchase price, "
     "duties, and directly attributable costs of bringing the asset to working condition."),
    (5, "Depreciation",
     "Depreciation on tangible assets is provided on Written Down Value (WDV) method at rates prescribed "
     "under Schedule II to the Companies Act 2013, based on useful life of the assets."),
    (6, "Intangible Assets",
     "Intangible assets are recognized when it is probable that future economic benefits will flow "
     "to the company and the cost can be measured reliably. They are amortized over their useful life."),
    (7, "Investments",
     "Long-term investments are stated at cost, less provision for permanent diminution in value. "
     "Current investments are carried at lower of cost and fair value."),
    (8, "Inventories",
     "Inventories are valued at lower of cost and net realizable value. Cost is determined on "
     "First-In-First-Out (FIFO) / Weighted Average basis."),
    (9, "Employee Benefits",
     "Short-term employee benefits are recognized at undiscounted amounts. "
     "Contribution to Provident Fund and ESI are charged to P&L. "
     "Liability for gratuity is determined based on actuarial valuation as per AS-15."),
    (10, "Borrowing Costs",
     "Borrowing costs directly attributable to acquisition, construction or production of qualifying "
     "assets are capitalized as part of the cost of that asset as per AS-16. Other borrowing costs "
     "are recognized as an expense in the period in which they are incurred."),
    (11, "Taxation",
     "Current tax is determined as per the provisions of the Income Tax Act, 1961. "
     "Deferred tax is recognized on timing differences between taxable income and accounting income "
     "as per AS-22, using substantially enacted tax rates."),
    (12, "Provisions and Contingencies",
     "Provisions are recognized when there is a present obligation as a result of past events, "
     "a probable outflow of resources is expected, and the amount can be reliably estimated (AS-29). "
     "Contingent liabilities are disclosed in the notes."),
    (13, "Foreign Currency Transactions",
     "Foreign currency transactions are recorded at the exchange rate prevailing on the date of "
     "transaction. Monetary assets and liabilities denominated in foreign currencies are translated "
     "at the closing rate. Exchange differences are recognized in P&L as per AS-11."),
    (14, "Earnings Per Share",
     "Basic EPS is computed by dividing net profit after tax available to equity shareholders by "
     "the weighted average number of equity shares outstanding during the year. "
     "Diluted EPS considers the effect of all dilutive potential equity shares."),
    (15, "Cash Flow Statement",
     "Cash flow statement is prepared using the indirect method as per AS-3, "
     "segregating cash flows into operating, investing, and financing activities."),
    (16, "Impairment of Assets",
     "At each balance sheet date, the carrying amounts of assets are reviewed for impairment. "
     "If any indication of impairment exists, the recoverable amount is estimated as per AS-28."),
]

# Disclosure structure A-T
DISCLOSURE_STRUCTURE = [
    ("A", "CIF VALUE OF IMPORTS", [
        ("(i)", "Raw Materials"), ("(ii)", "Components & Spares"), ("(iii)", "Capital Goods"),
    ]),
    ("B", "EXPENDITURE IN FOREIGN CURRENCY", [
        ("(i)", "Royalty/Know-how"), ("(ii)", "Professional Fees"),
        ("(iii)", "Interest"), ("(iv)", "Others"),
    ]),
    ("C", "EARNINGS IN FOREIGN EXCHANGE", [
        ("(i)", "Export of Goods (FOB)"), ("(ii)", "Professional Fees"),
        ("(iii)", "Interest & Dividend"), ("(iv)", "Others"),
    ]),
    ("D", "IMPORTED vs INDIGENOUS CONSUMPTION", [
        ("", "Imported - Amount"), ("", "Imported - %"),
        ("", "Indigenous - Amount"), ("", "Indigenous - %"),
    ]),
    ("E", "DIVIDENDS IN FOREIGN CURRENCY", [
        ("", "No. of NR Shareholders"), ("", "Shares Held"), ("", "Amount Remitted"),
    ]),
    ("F", "SHARES HELD BY PROMOTERS", [("", "See Share Capital Note A")]),
    ("G", "CWIP AGEING SCHEDULE", [("", "See PPE Schedule")]),
    ("H", "INTANGIBLE UNDER DEVELOPMENT AGEING", [("", "See PPE Schedule")]),
    ("I", "BENAMI PROPERTY", [("", "Details of proceedings / held property if any")]),
    ("J", "STRUCK-OFF COMPANIES (Sec 248)", [("", "Name / Nature / Balance")]),
    ("K", "CHARGES NOT REGISTERED WITH ROC", [("", "Beyond statutory period")]),
    ("L", "COMPLIANCE WITH LAYERS (Sec 2(87))", [("", "Compliance status")]),
    ("M", "UTILISATION OF BORROWED / SHARE PREMIUM FUNDS", [
        ("", "Purpose other than for which taken"),
    ]),
    ("N", "UNDISCLOSED INCOME", [("", "Surrendered or disclosed during the year")]),
    ("O", "CRYPTO CURRENCY / VIRTUAL CURRENCY", [("", "Details of transactions")]),
    ("P", "WILFUL DEFAULTER", [("", "Declared as wilful defaulter by any Bank/FI")]),
    ("Q", "CSR DETAILED DISCLOSURE (Sec 135)", [
        ("(i)", "Amount required to be spent"), ("(ii)", "Amount spent"),
        ("(iii)", "Unspent - Ongoing projects"), ("(iv)", "Unspent - Other than ongoing"),
    ]),
    ("R", "LOANS / ADVANCES (Sec 186)", [
        ("(i)", "Loans to promoters/directors/KMP/related parties"),
        ("(ii)", "Investments by company in body corporate"),
        ("(iii)", "Guarantee / security provided"),
    ]),
    ("S", "EVENTS AFTER BALANCE SHEET DATE", [("", "Material events requiring disclosure")]),
    ("T", "SEGMENT REPORTING", [("", "If applicable per AS-17")]),
]


# ============================================================
# ACCOUNTING POLICIES SERVICE
# ============================================================

def seed_default_policies(db: Session, project_id: int) -> int:
    """Seed default accounting policies for a project if none exist."""
    existing = db.query(AccountingPolicy).filter(
        AccountingPolicy.project_id == project_id
    ).count()
    if existing > 0:
        return existing

    for num, title, body in DEFAULT_POLICIES:
        db.add(AccountingPolicy(
            project_id=project_id,
            policy_number=num, title=title, body=body,
        ))
    db.commit()
    return len(DEFAULT_POLICIES)


def get_policies(db: Session, project_id: int) -> list[dict]:
    """Get all accounting policies for a project."""
    seed_default_policies(db, project_id)
    policies = db.query(AccountingPolicy).filter(
        AccountingPolicy.project_id == project_id,
        AccountingPolicy.is_active == True,
    ).order_by(AccountingPolicy.policy_number).all()
    return [
        {
            "id": p.id, "number": p.policy_number,
            "title": p.title, "body": p.body, "is_active": p.is_active,
        }
        for p in policies
    ]


def update_policy(db: Session, policy_id: int, **updates) -> AccountingPolicy:
    """Update a policy's title, body, or active status."""
    policy = db.query(AccountingPolicy).filter(AccountingPolicy.id == policy_id).first()
    if not policy:
        raise ValueError(f"Policy {policy_id} not found")
    for key in ('title', 'body', 'is_active'):
        if key in updates and updates[key] is not None:
            setattr(policy, key, updates[key])
    db.commit()
    db.refresh(policy)
    return policy


def add_custom_policy(db: Session, project_id: int, title: str, body: str) -> AccountingPolicy:
    """Add a custom accounting policy."""
    max_num = db.query(AccountingPolicy).filter(
        AccountingPolicy.project_id == project_id
    ).count()
    policy = AccountingPolicy(
        project_id=project_id,
        policy_number=max_num + 1,
        title=title, body=body,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


# ============================================================
# ADDITIONAL DISCLOSURES SERVICE
# ============================================================

def seed_disclosure_structure(db: Session, project_id: int) -> int:
    """Seed disclosure items for a project from the standard structure."""
    existing = db.query(DisclosureData).filter(
        DisclosureData.project_id == project_id
    ).count()
    if existing > 0:
        return existing

    count = 0
    for ref, section_title, items in DISCLOSURE_STRUCTURE:
        for sub_ref, particulars in items:
            db.add(DisclosureData(
                project_id=project_id,
                disclosure_ref=ref, sub_ref=sub_ref,
                particulars=particulars,
            ))
            count += 1
    db.commit()
    return count


def get_disclosures(db: Session, project_id: int) -> dict:
    """Get all disclosure data grouped by section."""
    seed_disclosure_structure(db, project_id)
    rows = db.query(DisclosureData).filter(
        DisclosureData.project_id == project_id
    ).order_by(DisclosureData.id).all()

    sections = {}
    for ref, title, _ in DISCLOSURE_STRUCTURE:
        section_items = [r for r in rows if r.disclosure_ref == ref]
        sections[ref] = {
            "title": title,
            "items": [
                {
                    "id": r.id, "sub_ref": r.sub_ref,
                    "particulars": r.particulars,
                    "cy_amount": r.cy_amount, "py_amount": r.py_amount,
                    "text_value": r.text_value,
                }
                for r in section_items
            ],
        }
    return sections


def update_disclosure(db: Session, item_id: int, **updates) -> DisclosureData:
    """Update a disclosure item's amounts or text."""
    item = db.query(DisclosureData).filter(DisclosureData.id == item_id).first()
    if not item:
        raise ValueError(f"Disclosure item {item_id} not found")
    for key in ('cy_amount', 'py_amount', 'text_value', 'particulars'):
        if key in updates and updates[key] is not None:
            setattr(item, key, updates[key])
    db.commit()
    db.refresh(item)
    return item
