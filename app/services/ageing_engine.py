"""
Ageing Engine
Handles:
- Party-wise ageing data input (CRUD) for Trade Receivables and Trade Payables
- Ageing schedule generation for Schedule III disclosure
- Aggregation into 22 TR buckets / 17 TP buckets for CoA code mapping

TR Ageing Matrix:
                    <6M    6M-1Y   1-2Y    2-3Y    >3Y
Undisputed Good
Undisputed Doubtful
Disputed Good
Disputed Doubtful
Others

TP Ageing Matrix:
                    <1Y    1-2Y    2-3Y    >3Y
MSME Undisputed
Other Undisputed
MSME Disputed
Other Disputed
Unbilled
"""
import pandas as pd
from io import BytesIO
from sqlalchemy.orm import Session
from app.models import AgeingData, Project


def save_ageing_entry(
    db: Session, project_id: int,
    ageing_type: str,  # "TR" or "TP"
    party_name: str,
    buckets: dict,  # {"bucket_1": X, "bucket_2": Y, ...}
    period: str = "CY",
    is_msme: bool = False,
    is_disputed: bool = False,
    is_doubtful: bool = False,
) -> AgeingData:
    """Save a single party's ageing data."""
    entry = AgeingData(
        project_id=project_id,
        ageing_type=ageing_type.upper(),
        party_name=party_name,
        is_msme=is_msme,
        is_disputed=is_disputed,
        is_doubtful=is_doubtful,
        bucket_1=buckets.get("bucket_1", 0),
        bucket_2=buckets.get("bucket_2", 0),
        bucket_3=buckets.get("bucket_3", 0),
        bucket_4=buckets.get("bucket_4", 0),
        bucket_5=buckets.get("bucket_5", 0),
        period=period,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def upload_ageing_file(
    db: Session, project_id: int,
    file_bytes: bytes, filename: str,
    ageing_type: str,  # "TR" or "TP"
    period: str = "CY",
    replace: bool = True,
) -> dict:
    """
    Upload ageing data from Excel/CSV.
    Expected columns:
    TR: Party Name, MSME (Y/N), Disputed (Y/N), Doubtful (Y/N), <6M, 6M-1Y, 1-2Y, 2-3Y, >3Y
    TP: Party Name, MSME (Y/N), Disputed (Y/N), <1Y, 1-2Y, 2-3Y, >3Y
    """
    if filename.lower().endswith('.csv'):
        df = pd.read_csv(BytesIO(file_bytes))
    else:
        df = pd.read_excel(BytesIO(file_bytes), engine='openpyxl')

    # Normalize column names
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Find party name column
    name_col = None
    for candidate in ['party name', 'party', 'name', 'ledger', 'customer', 'vendor']:
        if candidate in df.columns:
            name_col = candidate
            break
    if not name_col:
        raise ValueError(f"No party name column found. Columns: {list(df.columns)}")

    if replace:
        db.query(AgeingData).filter(
            AgeingData.project_id == project_id,
            AgeingData.ageing_type == ageing_type.upper(),
            AgeingData.period == period,
        ).delete()

    rows_added = 0
    for _, row in df.iterrows():
        party = str(row[name_col]).strip()
        if not party or party.lower() in ('nan', 'none', ''):
            continue

        is_msme = str(row.get('msme', '')).strip().upper() in ('Y', 'YES', '1', 'TRUE')
        is_disputed = str(row.get('disputed', '')).strip().upper() in ('Y', 'YES', '1', 'TRUE')
        is_doubtful = str(row.get('doubtful', '')).strip().upper() in ('Y', 'YES', '1', 'TRUE')

        # Map bucket columns
        if ageing_type.upper() == "TR":
            bucket_names = ['<6m', '6m-1y', '1-2y', '2-3y', '>3y']
        else:
            bucket_names = ['<1y', '1-2y', '2-3y', '>3y']

        buckets = {}
        for i, bn in enumerate(bucket_names):
            # Try exact match then alternatives
            val = 0
            for alt in [bn, bn.replace('-', ' to '), bn.replace('>', 'above '), bn.replace('<', 'less than ')]:
                if alt in df.columns:
                    val = pd.to_numeric(row[alt], errors='coerce') or 0
                    break
            buckets[f"bucket_{i+1}"] = float(val)

        save_ageing_entry(
            db, project_id, ageing_type, party,
            buckets, period, is_msme, is_disputed, is_doubtful
        )
        rows_added += 1

    db.commit()
    return {"rows_imported": rows_added, "ageing_type": ageing_type, "period": period}


def get_ageing_data(db: Session, project_id: int,
                    ageing_type: str, period: str = "CY") -> list[dict]:
    """Get all ageing entries for a project/type/period."""
    rows = db.query(AgeingData).filter(
        AgeingData.project_id == project_id,
        AgeingData.ageing_type == ageing_type.upper(),
        AgeingData.period == period,
    ).all()
    return [
        {
            "id": r.id,
            "party_name": r.party_name,
            "is_msme": r.is_msme,
            "is_disputed": r.is_disputed,
            "is_doubtful": r.is_doubtful,
            "bucket_1": r.bucket_1,
            "bucket_2": r.bucket_2,
            "bucket_3": r.bucket_3,
            "bucket_4": r.bucket_4,
            "bucket_5": r.bucket_5,
        }
        for r in rows
    ]


def generate_tr_ageing_schedule(db: Session, project_id: int) -> dict:
    """
    Generate Trade Receivables ageing schedule for Schedule III.
    Returns CY and PY matrices.
    """
    result = {}

    for period in ["CY", "PY"]:
        rows = db.query(AgeingData).filter(
            AgeingData.project_id == project_id,
            AgeingData.ageing_type == "TR",
            AgeingData.period == period,
        ).all()

        matrix = {
            "undisputed_good": [0, 0, 0, 0, 0],
            "undisputed_doubtful": [0, 0, 0, 0, 0],
            "disputed_good": [0, 0, 0, 0, 0],
            "disputed_doubtful": [0, 0, 0, 0, 0],
            "others": [0, 0, 0, 0, 0],
        }

        for r in rows:
            buckets = [r.bucket_1, r.bucket_2, r.bucket_3, r.bucket_4, r.bucket_5]
            if r.is_disputed:
                key = "disputed_doubtful" if r.is_doubtful else "disputed_good"
            else:
                key = "undisputed_doubtful" if r.is_doubtful else "undisputed_good"
            for i in range(5):
                matrix[key][i] += buckets[i] or 0

        # Compute totals
        total = [0, 0, 0, 0, 0]
        for key, vals in matrix.items():
            for i in range(5):
                total[i] += vals[i]

        matrix["total"] = total
        matrix["grand_total"] = sum(total)

        # Add row totals
        for key in matrix:
            if key != "grand_total":
                matrix[key].append(sum(matrix[key]))  # position [5] = row total

        result[period.lower()] = matrix

    return result


def generate_tp_ageing_schedule(db: Session, project_id: int) -> dict:
    """
    Generate Trade Payables ageing schedule.
    """
    result = {}

    for period in ["CY", "PY"]:
        rows = db.query(AgeingData).filter(
            AgeingData.project_id == project_id,
            AgeingData.ageing_type == "TP",
            AgeingData.period == period,
        ).all()

        matrix = {
            "msme_undisputed": [0, 0, 0, 0],
            "other_undisputed": [0, 0, 0, 0],
            "msme_disputed": [0, 0, 0, 0],
            "other_disputed": [0, 0, 0, 0],
            "unbilled": [0, 0, 0, 0],
        }

        for r in rows:
            buckets = [r.bucket_1, r.bucket_2, r.bucket_3, r.bucket_4]
            if r.is_disputed:
                key = "msme_disputed" if r.is_msme else "other_disputed"
            else:
                key = "msme_undisputed" if r.is_msme else "other_undisputed"
            for i in range(4):
                matrix[key][i] += buckets[i] or 0

        total = [0, 0, 0, 0]
        for key, vals in matrix.items():
            for i in range(4):
                total[i] += vals[i]

        matrix["total"] = total
        matrix["grand_total"] = sum(total)

        # MSME vs Others totals
        msme_total = sum(matrix["msme_undisputed"]) + sum(matrix["msme_disputed"])
        other_total = sum(matrix["other_undisputed"]) + sum(matrix["other_disputed"]) + sum(matrix["unbilled"])
        matrix["msme_total"] = msme_total
        matrix["other_total"] = other_total

        # Row totals
        for key in matrix:
            if isinstance(matrix[key], list):
                matrix[key].append(sum(matrix[key]))

        result[period.lower()] = matrix

    return result
