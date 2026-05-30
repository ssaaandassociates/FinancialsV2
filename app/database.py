from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from app.config import DATABASE_URL, IS_SQLITE

# SQLite needs check_same_thread=False for FastAPI's threaded access.
# Postgres must NOT receive that arg.
#
# When connecting through Supabase's connection pooler (pgbouncer, host
# *.pooler.supabase.com), we let pgbouncer do the pooling and disable
# SQLAlchemy's own pool via NullPool. Stacking two poolers causes
# "prepared statement already exists" errors in transaction mode and
# stale-connection issues. pool_pre_ping still guards against dead sockets.
if IS_SQLITE:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
else:
    _use_pooler = "pooler.supabase.com" in DATABASE_URL
    if _use_pooler:
        engine = create_engine(
            DATABASE_URL,
            poolclass=NullPool,
            pool_pre_ping=True,
            echo=False,
        )
    else:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False,
        )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Import all models so create_all sees every table
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
    # Multi-tenant tables (new in SaaS migration)
    from app.models.tenancy import Firm, User
    Base.metadata.create_all(bind=engine)
