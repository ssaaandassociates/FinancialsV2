from sqlalchemy import Column, Integer, String
from app.database import Base


class CoAMaster(Base):
    __tablename__ = "coa_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    level = Column(Integer, nullable=False)  # 1=Section, 2=Head, 3=Sub-head, 4=Line item
    particulars = Column(String(200), nullable=False)
    schedule_ref = Column(String(20))   # e.g. "A(a)", "Part I-1(b)"
    nature = Column(String(5))          # Dr / Cr / Dr/Cr
    fs_type = Column(String(5))         # BS / PL
    note_ref = Column(String(10))       # e.g. "A", "B", "Rev", "OE"
    tally_group = Column(String(50))    # Suggested Tally group for auto-mapping
    parent_code = Column(String(20))    # For hierarchy (e.g. BS-EL-01-02-01 → BS-EL-01-02)
    remarks = Column(String(200))

    def __repr__(self):
        return f"<CoA {self.code}: {self.particulars}>"
