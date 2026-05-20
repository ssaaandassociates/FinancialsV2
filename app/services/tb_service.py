"""
Trial Balance Service
Handles TB file parsing, storage, and retrieval.
"""
import pandas as pd
from io import BytesIO
from sqlalchemy.orm import Session
from app.models import TrialBalance, Project


COLUMN_ALIASES = {
    'ledger_name': ['ledger', 'ledger name', 'account', 'account name', 'particulars'],
    'tally_group': ['tally group', 'group', 'primary group', 'group name'],
    'cy_debit': ['cy debit', 'current year debit', 'debit cy', 'debit'],
    'cy_credit': ['cy credit', 'current year credit', 'credit cy', 'credit'],
    'py_debit': ['py debit', 'previous year debit', 'debit py', 'prior debit'],
    'py_credit': ['py credit', 'previous year credit', 'credit py', 'prior credit'],
    'coa_code': ['coa code', 'code', 'mapping code', 'schedule code'],
}


def _find_column(df_cols, target_key: str):
    """Find actual column in df matching target aliases (case-insensitive)"""
    aliases = COLUMN_ALIASES.get(target_key, [])
    normalized = {str(c).strip().lower(): c for c in df_cols}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    return None


def parse_tb_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Parse uploaded TB file into standardized DataFrame."""
    if filename.lower().endswith('.csv'):
        df = pd.read_csv(BytesIO(file_bytes))
    else:
        df = pd.read_excel(BytesIO(file_bytes), engine='openpyxl')

    # Map columns to standard names
    col_map = {}
    for target in COLUMN_ALIASES:
        found = _find_column(df.columns, target)
        if found:
            col_map[found] = target
    df = df.rename(columns=col_map)

    # Validate required
    required = ['ledger_name', 'cy_debit', 'cy_credit']
    missing = [r for r in required if r not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Found: {list(df.columns)}")

    # Fill missing optional columns
    for opt in ['tally_group', 'py_debit', 'py_credit', 'coa_code']:
        if opt not in df.columns:
            df[opt] = None

    # Clean numeric columns
    for num_col in ['cy_debit', 'cy_credit', 'py_debit', 'py_credit']:
        df[num_col] = pd.to_numeric(df[num_col], errors='coerce').fillna(0)

    # Clean string columns
    df['ledger_name'] = df['ledger_name'].astype(str).str.strip()
    df['tally_group'] = df['tally_group'].fillna('').astype(str).str.strip()
    df['coa_code'] = df['coa_code'].fillna('').astype(str).str.strip()

    # Drop empty rows
    df = df[df['ledger_name'].str.len() > 0]
    df = df[~df['ledger_name'].str.lower().isin(['nan', 'none', ''])]

    return df[['ledger_name', 'tally_group', 'cy_debit', 'cy_credit',
               'py_debit', 'py_credit', 'coa_code']].reset_index(drop=True)


def save_tb_to_db(db: Session, project_id: int, tb_df: pd.DataFrame,
                  replace: bool = True) -> dict:
    """Save parsed TB to DB for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    if replace:
        db.query(TrialBalance).filter(TrialBalance.project_id == project_id).delete()

    rows_added = 0
    for _, row in tb_df.iterrows():
        tb_row = TrialBalance(
            project_id=project_id,
            ledger_name=row['ledger_name'],
            tally_group=row.get('tally_group') or '',
            cy_debit=float(row['cy_debit'] or 0),
            cy_credit=float(row['cy_credit'] or 0),
            py_debit=float(row['py_debit'] or 0),
            py_credit=float(row['py_credit'] or 0),
            coa_code=row.get('coa_code') or None,
        )
        db.add(tb_row)
        rows_added += 1

    project.status = "tb_uploaded"
    db.commit()

    # Totals for validation
    cy_dr = float(tb_df['cy_debit'].sum())
    cy_cr = float(tb_df['cy_credit'].sum())
    py_dr = float(tb_df['py_debit'].sum())
    py_cr = float(tb_df['py_credit'].sum())

    return {
        "rows_saved": rows_added,
        "cy_debit_total": round(cy_dr, 2),
        "cy_credit_total": round(cy_cr, 2),
        "cy_difference": round(cy_dr - cy_cr, 2),
        "py_debit_total": round(py_dr, 2),
        "py_credit_total": round(py_cr, 2),
        "py_difference": round(py_dr - py_cr, 2),
        "cy_balanced": abs(cy_dr - cy_cr) < 0.01,
        "py_balanced": abs(py_dr - py_cr) < 0.01,
    }


def get_tb_for_project(db: Session, project_id: int) -> list[dict]:
    """Return all TB rows for a project."""
    rows = db.query(TrialBalance).filter(TrialBalance.project_id == project_id).all()
    return [
        {
            "id": r.id,
            "ledger_name": r.ledger_name,
            "tally_group": r.tally_group,
            "cy_debit": r.cy_debit,
            "cy_credit": r.cy_credit,
            "cy_net": r.cy_net,
            "py_debit": r.py_debit,
            "py_credit": r.py_credit,
            "py_net": r.py_net,
            "coa_code": r.coa_code,
        }
        for r in rows
    ]


def get_unmapped_ledgers(db: Session, project_id: int) -> list[dict]:
    """Return TB rows without a CoA code."""
    rows = db.query(TrialBalance).filter(
        TrialBalance.project_id == project_id,
        (TrialBalance.coa_code.is_(None)) | (TrialBalance.coa_code == '')
    ).all()
    return [
        {
            "id": r.id,
            "ledger_name": r.ledger_name,
            "tally_group": r.tally_group,
            "cy_net": r.cy_net,
        }
        for r in rows
    ]
