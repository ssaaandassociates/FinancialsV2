from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class AuditEntry(Base):
    __tablename__ = "audit_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    entry_no = Column(Integer, nullable=False)
    date = Column(Date)
    narration = Column(String(500))
    dr_coa_code = Column(String(20), nullable=False)
    cr_coa_code = Column(String(20), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(20), default="proposed")  # proposed / approved / rejected
    approved_by = Column(String(100))

    project = relationship("Project", back_populates="audit_entries")

    def __repr__(self):
        return f"<Audit #{self.entry_no}: Dr:{self.dr_coa_code} Cr:{self.cr_coa_code} Rs.{self.amount}>"
