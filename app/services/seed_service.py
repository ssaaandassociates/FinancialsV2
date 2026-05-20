from sqlalchemy.orm import Session
from app.models.coa import CoAMaster
from app.models.trial_balance import TBMapping
from app.core.coa_data import COA_MASTER_DATA, TALLY_MAPPING_RULES


def seed_coa(db: Session):
    existing = db.query(CoAMaster).count()
    if existing > 0:
        return f"CoA already seeded ({existing} codes)"

    codes = []
    for row in COA_MASTER_DATA:
        code, level, particulars, schedule_ref, nature, fs_type, note_ref, tally_group, parent_code, remarks = row
        codes.append(CoAMaster(
            code=code, level=level, particulars=particulars,
            schedule_ref=schedule_ref, nature=nature, fs_type=fs_type,
            note_ref=note_ref, tally_group=tally_group,
            parent_code=parent_code, remarks=remarks
        ))

    db.add_all(codes)
    db.commit()
    return f"Seeded {len(codes)} CoA codes"


def seed_mapping_rules(db: Session):
    existing = db.query(TBMapping).count()
    if existing > 0:
        return f"Mapping rules already seeded ({existing} rules)"

    rules = []
    for tally_group, coa_code, confidence in TALLY_MAPPING_RULES:
        rules.append(TBMapping(
            tally_group=tally_group,
            suggested_coa_code=coa_code,
            confidence=confidence
        ))

    db.add_all(rules)
    db.commit()
    return f"Seeded {len(rules)} mapping rules"


def seed_all(db: Session):
    r1 = seed_coa(db)
    r2 = seed_mapping_rules(db)
    return {"coa": r1, "mapping": r2}
