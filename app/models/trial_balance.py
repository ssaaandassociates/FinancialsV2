from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class TrialBalance(Base):
    __tablename__ = "trial_balance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    ledger_name = Column(String(200), nullable=False)
    tally_group = Column(String(100))
    cy_debit = Column(Float, default=0)
    cy_credit = Column(Float, default=0)
    py_debit = Column(Float, default=0)
    py_credit = Column(Float, default=0)
    coa_code = Column(String(20), index=True)  # Assigned CoA code

    # Computed properties (not stored, calculated at runtime)
    @property
    def cy_net(self):
        """CY Net = Debit - Credit (before audit adjustments)"""
        return (self.cy_debit or 0) - (self.cy_credit or 0)

    @property
    def py_net(self):
        """PY Net = Debit - Credit"""
        return (self.py_debit or 0) - (self.py_credit or 0)

    project = relationship("Project", back_populates="trial_balances")

    def __repr__(self):
        return f"<TB {self.ledger_name} [{self.coa_code}]>"


class TBMapping(Base):
    """Stores auto-mapping suggestions: Tally group → CoA code"""
    __tablename__ = "tb_mapping_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tally_group = Column(String(100), nullable=False, index=True)
    suggested_coa_code = Column(String(20), nullable=False)
    confidence = Column(Float, default=1.0)  # 0.0 to 1.0

    def __repr__(self):
        return f"<Map {self.tally_group} → {self.suggested_coa_code}>"
