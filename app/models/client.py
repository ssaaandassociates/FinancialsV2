from sqlalchemy import Column, Integer, String, Date, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    cin = Column(String(25))
    pan = Column(String(15))
    gstin = Column(String(20))
    date_of_incorporation = Column(Date)
    registered_office = Column(String(500))   # Full address
    principal_activity = Column(String(300))   # Main business objective
    auditor_name = Column(String(200))
    auditor_frn = Column(String(20))
    authorized_capital = Column(Float, default=0)
    paid_up_capital = Column(Float, default=0)
    face_value = Column(Float, default=10)
    tax_rate = Column(Float, default=0.2987)

    projects = relationship("Project", back_populates="client", cascade="all, delete-orphan")
    directors = relationship("Director", back_populates="client", cascade="all, delete-orphan")
    kmp_list = relationship("KMP", back_populates="client", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Client {self.name}>"


class Director(Base):
    """Directors at client level — carries across FYs."""
    __tablename__ = "directors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String(200), nullable=False)
    din = Column(String(10))
    designation = Column(String(50), default="Director")  # Director / Managing Director / Whole-time Director
    date_of_appointment = Column(Date)
    is_active = Column(Boolean, default=True)

    client = relationship("Client", back_populates="directors")

    def __repr__(self):
        return f"<Director {self.name} DIN:{self.din}>"


class KMP(Base):
    """Key Managerial Personnel at client level."""
    __tablename__ = "kmp"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String(200), nullable=False)
    designation = Column(String(50))  # CEO / CFO / CS / Manager
    pan = Column(String(15))
    is_active = Column(Boolean, default=True)

    client = relationship("Client", back_populates="kmp_list")

    def __repr__(self):
        return f"<KMP {self.name} {self.designation}>"
