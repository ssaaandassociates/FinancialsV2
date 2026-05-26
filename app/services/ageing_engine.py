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


# =========================================================================
# TB-DERIVED AGEING (Section 5 — V9)
# Build ageing matrix DIRECTLY from TB ledgers mapped to BS-AS-02-03-XX / BS-EL-04-02-XX
# No separate AgeingData upload needed.
# =========================================================================

# Map from leaf-code suffix → (category, bucket_index) for TR
# Buckets: 0=<6M, 1=6M-1Y, 2=1-2Y, 3=2-3Y, 4=>3Y
_TR_LEAF_MAP = {
    "01": ("undisputed_good", 0),
    "02": ("undisputed_good", 1),
    "03": ("undisputed_good", 2),
    "04": ("undisputed_good", 3),
    "05": ("undisputed_good", 4),
    "06": ("undisputed_doubtful", 0),
    "07": ("undisputed_doubtful", 1),
    "08": ("undisputed_doubtful", 2),
    "09": ("undisputed_doubtful", 3),
    "10": ("undisputed_doubtful", 4),
    "11": ("disputed_good", 0),
    "12": ("disputed_good", 1),
    "13": ("disputed_good", 2),
    "14": ("disputed_good", 3),
    "15": ("disputed_good", 4),
    "16": ("disputed_doubtful", 0),
    "17": ("disputed_doubtful", 1),
    "18": ("disputed_doubtful", 2),
    "19": ("disputed_doubtful", 3),
    "20": ("disputed_doubtful", 4),
    "21": ("others", 0),  # 'TR Others' — put in <6M bucket, also flagged 'others'
}

# Map from leaf-code suffix → (category, bucket_index) for TP
# Buckets: 0=<1Y, 1=1-2Y, 2=2-3Y, 3=>3Y
_TP_LEAF_MAP = {
    "01": ("msme_undisputed", 0),
    "02": ("msme_undisputed", 1),
    "03": ("msme_undisputed", 2),
    "04": ("msme_undisputed", 3),
    "05": ("other_undisputed", 0),
    "06": ("other_undisputed", 1),
    "07": ("other_undisputed", 2),
    "08": ("other_undisputed", 3),
    "09": ("msme_disputed", 0),
    "10": ("msme_disputed", 1),
    "11": ("msme_disputed", 2),
    "12": ("msme_disputed", 3),
    "13": ("other_disputed", 0),
    "14": ("other_disputed", 1),
    "15": ("other_disputed", 2),
    "16": ("other_disputed", 3),
    "17": ("unbilled", 0),
}

TR_PREFIX = "BS-AS-02-03-"
TP_PREFIX = "BS-EL-04-02-"


def derive_tr_matrix_from_tb(db: Session, project_id: int) -> dict:
    """
    Build TR ageing matrix from TB ledgers mapped to BS-AS-02-03-XX codes.
    Returns: {"cy": {category: [b1,b2,b3,b4,b5,total], ...}, "py": {...}}
    """
    from app.models import TrialBalance
    tb_rows = db.query(TrialBalance).filter(
        TrialBalance.project_id == project_id,
        TrialBalance.coa_code.like("BS-AS-02-03-%")
    ).all()

    def empty_matrix():
        m = {
            "undisputed_good": [0, 0, 0, 0, 0],
            "undisputed_doubtful": [0, 0, 0, 0, 0],
            "disputed_good": [0, 0, 0, 0, 0],
            "disputed_doubtful": [0, 0, 0, 0, 0],
            "others": [0, 0, 0, 0, 0],
            "total": [0, 0, 0, 0, 0],
        }
        return m

    cy_m = empty_matrix()
    py_m = empty_matrix()

    for r in tb_rows:
        if not r.coa_code or len(r.coa_code) < len(TR_PREFIX) + 2:
            continue
        suffix = r.coa_code[len(TR_PREFIX):len(TR_PREFIX) + 2]
        mapping = _TR_LEAF_MAP.get(suffix)
        if not mapping:
            continue
        cat, idx = mapping
        cy_m[cat][idx] += r.cy_net or 0
        py_m[cat][idx] += r.py_net or 0
        cy_m["total"][idx] += r.cy_net or 0
        py_m["total"][idx] += r.py_net or 0

    # Row totals (append 6th cell = sum of all buckets)
    for m in (cy_m, py_m):
        for k in list(m.keys()):
            m[k] = m[k] + [sum(m[k])]
        m["grand_total"] = sum(m["total"][:-1])

    return {"cy": cy_m, "py": py_m, "source": "TB"}


def derive_tp_matrix_from_tb(db: Session, project_id: int) -> dict:
    """
    Build TP ageing matrix from TB ledgers mapped to BS-EL-04-02-XX codes.
    Returns: {"cy": {category: [b1,b2,b3,b4,total], ...}, "py": {...}}
    """
    from app.models import TrialBalance
    tb_rows = db.query(TrialBalance).filter(
        TrialBalance.project_id == project_id,
        TrialBalance.coa_code.like("BS-EL-04-02-%")
    ).all()

    def empty_matrix():
        return {
            "msme_undisputed": [0, 0, 0, 0],
            "other_undisputed": [0, 0, 0, 0],
            "msme_disputed": [0, 0, 0, 0],
            "other_disputed": [0, 0, 0, 0],
            "unbilled": [0, 0, 0, 0],
            "total": [0, 0, 0, 0],
        }

    cy_m = empty_matrix()
    py_m = empty_matrix()

    for r in tb_rows:
        if not r.coa_code or len(r.coa_code) < len(TP_PREFIX) + 2:
            continue
        suffix = r.coa_code[len(TP_PREFIX):len(TP_PREFIX) + 2]
        mapping = _TP_LEAF_MAP.get(suffix)
        if not mapping:
            continue
        cat, idx = mapping
        # TP amounts are credit; cy_net = debit - credit, so a credit balance is negative.
        # We want to show the credit balance as positive in the ageing matrix.
        amount_cy = -(r.cy_net or 0)
        amount_py = -(r.py_net or 0)
        cy_m[cat][idx] += amount_cy
        py_m[cat][idx] += amount_py
        cy_m["total"][idx] += amount_cy
        py_m["total"][idx] += amount_py

    for m in (cy_m, py_m):
        for k in list(m.keys()):
            m[k] = m[k] + [sum(m[k])]
        m["grand_total"] = sum(m["total"][:-1])

    return {"cy": cy_m, "py": py_m, "source": "TB"}


def has_any_tr_tp_mapping(db: Session, project_id: int) -> dict:
    """Quick check whether the project has any TB rows mapped to TR/TP leaf codes."""
    from app.models import TrialBalance
    tr_count = db.query(TrialBalance).filter(
        TrialBalance.project_id == project_id,
        TrialBalance.coa_code.like("BS-AS-02-03-%")
    ).count()
    tp_count = db.query(TrialBalance).filter(
        TrialBalance.project_id == project_id,
        TrialBalance.coa_code.like("BS-EL-04-02-%")
    ).count()
    return {"tr_ledgers": tr_count, "tp_ledgers": tp_count}
