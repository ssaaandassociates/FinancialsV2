"""
Multi-tenant models — SaaS migration.

Design (per product decisions):
  - One firm per user  → firm_id lives directly on User (no join table)
  - No roles yet       → every member of a firm is equal
  - User.id matches the Supabase Auth user UUID (string), so the frontend
    can pass the Supabase session and the backend resolves the same user.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Firm(Base):
    __tablename__ = "firms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    gstin = Column(String, nullable=True)
    primary_email = Column(String, nullable=True)
    subscription_plan = Column(String, default="free")  # free / pro (future use)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="firm")
    # clients relationship is declared on Client via backref-free explicit query


class User(Base):
    __tablename__ = "users"

    # Supabase Auth UID (UUID string). We store it as the PK so the backend
    # and Supabase agree on identity without a second mapping table.
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=True)
    firm_id = Column(Integer, ForeignKey("firms.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    firm = relationship("Firm", back_populates="users")
