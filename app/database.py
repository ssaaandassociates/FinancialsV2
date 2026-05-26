from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.models.client import Client, Director, ClientShareholder, CustomCoACode, ClientPolicy
    from app.models.project import Project
    from app.models.coa import CoAMaster
    from app.models.trial_balance import TrialBalance, TBMapping
    from app.models.audit_entry import AuditEntry
    from app.models.supplementary import (
        AgeingData, ShareEvent, Shareholder, RelatedParty,
        RPTransaction, AccountingPolicy, DisclosureData,
        ClosingStock, PPEScheduleEntry, NoteEnrichment, SigningBlock,
        CompanyProfile, RatioPriorYear,
    )
    Base.metadata.create_all(bind=engine)
