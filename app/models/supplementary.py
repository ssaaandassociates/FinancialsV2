"""
Supplementary Data Models
Stores additional data beyond Trial Balance that feeds into
specific disclosures: Ageing, Share Capital, Related Parties.
"""
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class AgeingData(Base):
    """
    Stores party-wise ageing data for Trade Receivables and Trade Payables.
    Each row = one party with amounts in each ageing bucket.
    """
    __tablename__ = "ageing_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    ageing_type = Column(String(5), nullable=False)  # "TR" or "TP"
    party_name = Column(String(200), nullable=False)
    is_msme = Column(Boolean, default=False)          # For TP: MSME flag
    is_disputed = Column(Boolean, default=False)       # Disputed or Undisputed
    is_doubtful = Column(Boolean, default=False)       # For TR: Good or Doubtful

    # TR Buckets: <6M, 6M-1Y, 1-2Y, 2-3Y, >3Y
    # TP Buckets: <1Y, 1-2Y, 2-3Y, >3Y
    bucket_1 = Column(Float, default=0)  # TR: <6M   | TP: <1Y
    bucket_2 = Column(Float, default=0)  # TR: 6M-1Y | TP: 1-2Y
    bucket_3 = Column(Float, default=0)  # TR: 1-2Y  | TP: 2-3Y
    bucket_4 = Column(Float, default=0)  # TR: 2-3Y  | TP: >3Y
    bucket_5 = Column(Float, default=0)  # TR only: >3Y

    # Period: CY or PY
    period = Column(String(2), default="CY")  # "CY" or "PY"

    def __repr__(self):
        return f"<Ageing {self.ageing_type} {self.party_name} [{self.period}]>"


class ShareEvent(Base):
    """
    Share capital movement events for reconciliation.
    Opening → Issues → Buybacks → Bonus → Rights → Closing
    """
    __tablename__ = "share_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    event_type = Column(String(20), nullable=False)  # opening/issue/bonus/rights/buyback/forfeiture
    event_date = Column(Date)
    share_class = Column(String(20), default="equity")  # equity / preference
    no_of_shares = Column(Integer, default=0)
    face_value = Column(Float, default=10)
    premium = Column(Float, default=0)
    total_amount = Column(Float, default=0)  # shares × (face + premium)
    period = Column(String(2), default="CY")  # CY or PY
    narration = Column(String(300))

    def __repr__(self):
        return f"<ShareEvent {self.event_type} {self.no_of_shares} shares [{self.period}]>"


class Shareholder(Base):
    """
    Shareholder data for >5% disclosure and promoter holding.
    """
    __tablename__ = "shareholders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    share_class = Column(String(20), default="equity")
    no_of_shares_cy = Column(Integer, default=0)
    no_of_shares_py = Column(Integer, default=0)
    pct_holding_cy = Column(Float, default=0)
    pct_holding_py = Column(Float, default=0)
    is_promoter = Column(Boolean, default=False)
    din_pan = Column(String(20))

    def __repr__(self):
        return f"<Shareholder {self.name} {self.no_of_shares_cy} shares>"


class RelatedParty(Base):
    """Related party master for AS-18 disclosure."""
    __tablename__ = "related_parties"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(String(50))  # KMP / Relative / Entity / Holding/Sub
    relationship = Column(String(100))
    pan_cin = Column(String(25))

    def __repr__(self):
        return f"<RP {self.name} [{self.category}]>"


class RPTransaction(Base):
    """Related party transaction amounts for the matrix."""
    __tablename__ = "rp_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    party_id = Column(Integer, ForeignKey("related_parties.id"), nullable=False)
    transaction_type = Column(String(50), nullable=False)  # Purchase/Sale/Loan/Remuneration etc
    cy_amount = Column(Float, default=0)
    py_amount = Column(Float, default=0)

    def __repr__(self):
        return f"<RPTxn {self.transaction_type} CY:{self.cy_amount}>"


class AccountingPolicy(Base):
    """Customizable accounting policies per project."""
    __tablename__ = "accounting_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    policy_number = Column(Integer, nullable=False)
    title = Column(String(100), nullable=False)
    body = Column(String(2000), nullable=False)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Policy {self.policy_number}. {self.title}>"


class DisclosureData(Base):
    """Additional disclosure data items."""
    __tablename__ = "disclosure_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    disclosure_ref = Column(String(5), nullable=False)
    sub_ref = Column(String(10))
    particulars = Column(String(300), nullable=False)
    cy_amount = Column(Float, default=0)
    py_amount = Column(Float, default=0)
    text_value = Column(String(2000))

    def __repr__(self):
        return f"<Disclosure {self.disclosure_ref} {self.particulars[:30]}>"


class ClosingStock(Base):
    """
    Closing stock values - NOT in TB, must be entered manually.
    Used in P&L (COGS/Changes in Inventory) and BS (Inventories note).
    """
    __tablename__ = "closing_stock"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    stock_type = Column(String(30), nullable=False)  # raw_material / wip / finished_goods / stock_in_trade / stores_spares
    cy_amount = Column(Float, default=0)
    py_amount = Column(Float, default=0)
    coa_code = Column(String(20))  # Maps to BS inventory code and PL closing stock code

    def __repr__(self):
        return f"<ClosingStock {self.stock_type} CY:{self.cy_amount}>"


class PPEScheduleEntry(Base):
    """
    PPE Gross Block + Depreciation schedule per asset class.
    Manual input for Gross/Dep split since TB shows only net.
    Includes CY and PY full schedule.
    """
    __tablename__ = "ppe_schedule"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    asset_class = Column(String(50), nullable=False)
    coa_code = Column(String(20))
    asset_type = Column(String(15), default="tangible")

    # CY Gross Block
    gross_opening = Column(Float, default=0)
    gross_additions = Column(Float, default=0)
    gross_disposals = Column(Float, default=0)

    # CY Depreciation
    dep_opening = Column(Float, default=0)
    dep_for_year = Column(Float, default=0)
    dep_on_disposals = Column(Float, default=0)

    # PY Gross Block
    py_gross_opening = Column(Float, default=0)
    py_gross_additions = Column(Float, default=0)
    py_gross_disposals = Column(Float, default=0)

    # PY Depreciation
    py_dep_opening = Column(Float, default=0)
    py_dep_for_year = Column(Float, default=0)
    py_dep_on_disposals = Column(Float, default=0)

    @property
    def gross_closing(self):
        return (self.gross_opening or 0) + (self.gross_additions or 0) - (self.gross_disposals or 0)

    @property
    def dep_closing(self):
        return (self.dep_opening or 0) + (self.dep_for_year or 0) - (self.dep_on_disposals or 0)

    @property
    def net_cy(self):
        return self.gross_closing - self.dep_closing

    @property
    def py_gross_closing(self):
        return (self.py_gross_opening or 0) + (self.py_gross_additions or 0) - (self.py_gross_disposals or 0)

    @property
    def py_dep_closing(self):
        return (self.py_dep_opening or 0) + (self.py_dep_for_year or 0) - (self.py_dep_on_disposals or 0)

    @property
    def net_py(self):
        return self.py_gross_closing - self.py_dep_closing

    def __repr__(self):
        return f"<PPE {self.asset_class} Net CY:{self.net_cy} PY:{self.net_py}>"


class NoteEnrichment(Base):
    """
    Per-note manual enrichments: overrides, additional text disclosures,
    Yes/No checklist responses, and custom line items.
    """
    __tablename__ = "note_enrichments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    note_ref = Column(String(10), nullable=False)  # A, B, C... or Rev, OI, Emp...
    field_key = Column(String(50), nullable=False)  # e.g., "security_nature", "director_guarantee"
    field_type = Column(String(15), default="text")  # text / yesno / amount / table_json
    field_label = Column(String(200))
    value_text = Column(String(2000))
    value_amount = Column(Float)
    value_bool = Column(Boolean)

    def __repr__(self):
        return f"<NoteEnrich {self.note_ref}.{self.field_key}>"


class SigningBlock(Base):
    """Signing details for the financial statements."""
    __tablename__ = "signing_block"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    auditor_firm = Column(String(200))
    auditor_frn = Column(String(20))
    partner_name = Column(String(100))
    partner_membership_no = Column(String(10))
    partner_udin = Column(String(20))
    director1_name = Column(String(100))
    director1_din = Column(String(10))
    director1_designation = Column(String(50), default="Director")
    director2_name = Column(String(100))
    director2_din = Column(String(10))
    director2_designation = Column(String(50), default="Director")
    place = Column(String(50))
    signing_date = Column(Date)

    def __repr__(self):
        return f"<SigningBlock {self.auditor_firm}>"


class CompanyProfile(Base):
    """
    Quick questionnaire at project setup to auto-enable/disable disclosure sections.
    Answers determine which notes need enrichment and which get nil paras.
    """
    __tablename__ = "company_profile"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    has_forex_transactions = Column(Boolean, default=False)
    has_related_party_txns = Column(Boolean, default=True)
    has_csr_obligation = Column(Boolean, default=False)
    has_subsidiary_holding = Column(Boolean, default=False)
    has_contingent_liabilities = Column(Boolean, default=False)
    has_msme_vendors = Column(Boolean, default=False)
    has_cwip = Column(Boolean, default=False)
    has_intangible_under_dev = Column(Boolean, default=False)
    has_loans_to_directors = Column(Boolean, default=False)
    has_scheme_of_arrangement = Column(Boolean, default=False)
    has_crypto_transactions = Column(Boolean, default=False)
    has_benami_property = Column(Boolean, default=False)

    def __repr__(self):
        return f"<CompanyProfile project={self.project_id}>"


class RatioPriorYear(Base):
    """
    PY-1 (Previous to Previous Year) values needed for average-based ratios.
    Only needed for first year — later years auto-pull from PY project.
    Ratios needing averages: Current Ratio, Debt-Equity, DSCR, ROE,
    Trade Receivables Turnover, Trade Payables Turnover, Inventory Turnover.
    """
    __tablename__ = "ratio_prior_year"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    # PY-1 BS values for averages
    total_equity_py1 = Column(Float, default=0)
    total_debt_py1 = Column(Float, default=0)
    total_current_assets_py1 = Column(Float, default=0)
    total_current_liabilities_py1 = Column(Float, default=0)
    trade_receivables_py1 = Column(Float, default=0)
    trade_payables_py1 = Column(Float, default=0)
    inventory_py1 = Column(Float, default=0)
    net_worth_py1 = Column(Float, default=0)
    capital_employed_py1 = Column(Float, default=0)

    def __repr__(self):
        return f"<RatioPY1 project={self.project_id}>"
