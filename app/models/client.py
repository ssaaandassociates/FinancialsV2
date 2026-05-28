"""
Client-level models: Client, Director, KMP, Shareholder, CustomCoA, ClientPolicy
All at CLIENT level (carry across FYs).
"""
from sqlalchemy import Column, Integer, String, Date, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Multi-tenant scope. Nullable so existing single-tenant data still loads;
    # in production every client is created with a firm_id. All queries filter by it.
    firm_id = Column(Integer, ForeignKey("firms.id"), nullable=True, index=True)
    name = Column(String(200), nullable=False)
    cin = Column(String(25))
    pan = Column(String(15))
    gstin = Column(String(20))
    date_of_incorporation = Column(Date)
    registered_office = Column(String(500))
    principal_activity = Column(String(300))

    # Auditor
    auditor_name = Column(String(200))
    auditor_frn = Column(String(20))
    auditor_membership_no = Column(String(15))

    # Share Capital Structure
    face_value = Column(Float, default=10)
    authorised_shares = Column(Integer, default=0)
    authorised_capital = Column(Float, default=0)   # auto = authorised_shares × face_value
    subscribed_shares = Column(Integer, default=0)
    subscribed_capital = Column(Float, default=0)
    paidup_shares = Column(Integer, default=0)
    paidup_capital = Column(Float, default=0)

    # Legacy fields (kept for backward compat)
    authorized_capital = Column(Float, default=0)
    paid_up_capital = Column(Float, default=0)
    tax_rate = Column(Float, default=0.2987)

    projects = relationship("Project", back_populates="client", cascade="all, delete-orphan")
    directors = relationship("Director", back_populates="client", cascade="all, delete-orphan")
    shareholders = relationship("ClientShareholder", back_populates="client", cascade="all, delete-orphan")
    custom_codes = relationship("CustomCoACode", back_populates="client", cascade="all, delete-orphan")
    policies = relationship("ClientPolicy", back_populates="client", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Client {self.name}>"


class Director(Base):
    """
    Directors at client level.
    Flags: is_kmp (auto-appears in KMP list), signs_financials (auto-populates signing block)
    """
    __tablename__ = "directors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String(200), nullable=False)
    din = Column(String(10))
    designation = Column(String(50), default="Director")
    date_of_appointment = Column(Date)
    pan = Column(String(15))
    is_kmp = Column(Boolean, default=False)
    signs_financials = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    client = relationship("Client", back_populates="directors")

    def __repr__(self):
        return f"<Director {self.name} DIN:{self.din}>"


class ClientShareholder(Base):
    """
    Shareholders at CLIENT level (not project level).
    If is_director=True, auto-linked to Directors table.
    Share Capital = no_of_shares × face_value (auto-computed).
    """
    __tablename__ = "client_shareholders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String(200), nullable=False)
    no_of_shares_cy = Column(Integer, default=0)
    no_of_shares_py = Column(Integer, default=0)
    face_value = Column(Float, default=10)
    pct_holding_cy = Column(Float, default=0)
    pct_holding_py = Column(Float, default=0)
    is_promoter = Column(Boolean, default=False)
    is_director = Column(Boolean, default=False)
    din = Column(String(10))
    pan = Column(String(15))

    client = relationship("Client", back_populates="shareholders")

    @property
    def share_capital_cy(self):
        return (self.no_of_shares_cy or 0) * (self.face_value or 0)

    @property
    def share_capital_py(self):
        return (self.no_of_shares_py or 0) * (self.face_value or 0)

    def __repr__(self):
        return f"<Shareholder {self.name} {self.no_of_shares_cy} shares>"


class CustomCoACode(Base):
    """
    User-defined CoA codes at client level.
    Follows same BS-XX-XX-XX pattern. Available for all client's projects.
    """
    __tablename__ = "custom_coa_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    code = Column(String(25), nullable=False)
    particulars = Column(String(200), nullable=False)
    parent_code = Column(String(20))   # Parent major group
    nature = Column(String(5))         # Dr / Cr
    fs_type = Column(String(5))        # BS / PL
    note_ref = Column(String(10))

    client = relationship("Client", back_populates="custom_codes")

    def __repr__(self):
        return f"<CustomCoA {self.code} {self.particulars}>"


class ClientPolicy(Base):
    """
    Accounting policies at CLIENT level (carry across FYs).
    Projects inherit these unless "policy_changed" flag is set.
    """
    __tablename__ = "client_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    policy_number = Column(Integer, nullable=False)
    title = Column(String(100), nullable=False)
    body = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)

    client = relationship("Client", back_populates="policies")

    def __repr__(self):
        return f"<ClientPolicy {self.policy_number}. {self.title}>"
