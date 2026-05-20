from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ProjectStatus(str, enum.Enum):
    SETUP = "setup"
    TB_UPLOADED = "tb_uploaded"
    MAPPED = "mapped"
    DATA_ENTERED = "data_entered"
    ENRICHED = "enriched"
    PREVIEWED = "previewed"
    EXPORTED = "exported"


class CompanyType(str, enum.Enum):
    SERVICE = "service"
    TRADING = "trading"
    MANUFACTURING = "manufacturing"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    financial_year = Column(String(10), nullable=False)
    bs_date_cy = Column(Date)
    bs_date_py = Column(Date)
    rounding = Column(String(20), default="Rupees")
    company_type = Column(String(20), default=CompanyType.TRADING.value)
    status = Column(String(20), default=ProjectStatus.SETUP.value)

    client = relationship("Client", back_populates="projects")
    trial_balances = relationship("TrialBalance", back_populates="project", cascade="all, delete-orphan")
    audit_entries = relationship("AuditEntry", back_populates="project", cascade="all, delete-orphan")

    @property
    def cy_date_formatted(self):
        """e.g., '31 March 2025' — works on both Windows and Linux"""
        if self.bs_date_cy:
            d = self.bs_date_cy
            return f"{d.day} {d.strftime('%B')} {d.year}"
        return ""

    @property
    def py_date_formatted(self):
        if self.bs_date_py:
            d = self.bs_date_py
            return f"{d.day} {d.strftime('%B')} {d.year}"
        return ""

    @property
    def bs_header_cy(self):
        return f"As at {self.cy_date_formatted}" if self.cy_date_formatted else "CY"

    @property
    def bs_header_py(self):
        return f"As at {self.py_date_formatted}" if self.py_date_formatted else "PY"

    @property
    def pl_header_cy(self):
        return f"For the year ended {self.cy_date_formatted}" if self.cy_date_formatted else "CY"

    @property
    def pl_header_py(self):
        return f"For the year ended {self.py_date_formatted}" if self.py_date_formatted else "PY"

    def __repr__(self):
        return f"<Project {self.client_id} FY:{self.financial_year}>"
