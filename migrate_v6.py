"""
V6 Database Migration Script
Run this ONCE to upgrade an existing tce.db to V6 schema.
Adds new columns to existing tables + creates new tables.
Safe to run multiple times (checks before adding).

Usage: python migrate_v6.py
"""
import sqlite3
import os
import shutil
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tce.db")


def get_columns(cursor, table):
    """Get existing column names for a table."""
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def get_tables(cursor):
    """Get all table names."""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return {row[0] for row in cursor.fetchall()}


def add_column(cursor, table, col, col_type, default=None):
    """Add a column if it doesn't exist."""
    existing = get_columns(cursor, table)
    if col not in existing:
        default_clause = f" DEFAULT {default}" if default is not None else ""
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}{default_clause}")
        print(f"  + {table}.{col} ({col_type})")
        return True
    return False


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"No database found at {DB_PATH}")
        print("Start the app normally — it will create a fresh DB with V6 schema.")
        return

    # Backup first
    backup = DB_PATH + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(DB_PATH, backup)
    print(f"Backup saved: {backup}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    tables = get_tables(cursor)
    changes = 0

    # ============================================================
    # 1. CLIENTS TABLE — new columns
    # ============================================================
    print("\n[clients] Adding new columns...")
    client_cols = [
        ("pan", "VARCHAR(15)", None),
        ("gstin", "VARCHAR(20)", None),
        ("principal_activity", "VARCHAR(300)", None),
        ("auditor_membership_no", "VARCHAR(15)", None),
        ("face_value", "REAL", "10"),
        ("authorised_shares", "INTEGER", "0"),
        ("authorised_capital", "REAL", "0"),
        ("subscribed_shares", "INTEGER", "0"),
        ("subscribed_capital", "REAL", "0"),
        ("paidup_shares", "INTEGER", "0"),
        ("paidup_capital", "REAL", "0"),
    ]
    for col, ctype, default in client_cols:
        if add_column(cursor, "clients", col, ctype, default):
            changes += 1

    # ============================================================
    # 2. DIRECTORS TABLE — new columns
    # ============================================================
    if "directors" in tables:
        print("\n[directors] Adding new columns...")
        dir_cols = [
            ("pan", "VARCHAR(15)", None),
            ("is_kmp", "BOOLEAN", "0"),
            ("signs_financials", "BOOLEAN", "0"),
            ("date_of_appointment", "DATE", None),
        ]
        for col, ctype, default in dir_cols:
            if add_column(cursor, "directors", col, ctype, default):
                changes += 1

    # ============================================================
    # 3. PROJECTS TABLE — new columns
    # ============================================================
    if "projects" in tables:
        print("\n[projects] Adding new columns...")
        proj_cols = [
            ("version", "INTEGER", "1"),
            ("policy_changed", "VARCHAR(5)", "'no'"),
        ]
        for col, ctype, default in proj_cols:
            if add_column(cursor, "projects", col, ctype, default):
                changes += 1

    # ============================================================
    # 4. NEW TABLES — create if missing
    # ============================================================

    # client_shareholders
    if "client_shareholders" not in tables:
        print("\n[client_shareholders] Creating table...")
        cursor.execute("""
            CREATE TABLE client_shareholders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL REFERENCES clients(id),
                name VARCHAR(200) NOT NULL,
                no_of_shares_cy INTEGER DEFAULT 0,
                no_of_shares_py INTEGER DEFAULT 0,
                face_value REAL DEFAULT 10,
                pct_holding_cy REAL DEFAULT 0,
                pct_holding_py REAL DEFAULT 0,
                is_promoter BOOLEAN DEFAULT 0,
                is_director BOOLEAN DEFAULT 0,
                din VARCHAR(10),
                pan VARCHAR(15)
            )
        """)
        changes += 1
        print("  + client_shareholders table created")

    # custom_coa_codes
    if "custom_coa_codes" not in tables:
        print("\n[custom_coa_codes] Creating table...")
        cursor.execute("""
            CREATE TABLE custom_coa_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL REFERENCES clients(id),
                code VARCHAR(25) NOT NULL,
                particulars VARCHAR(200) NOT NULL,
                parent_code VARCHAR(20),
                nature VARCHAR(5),
                fs_type VARCHAR(5),
                note_ref VARCHAR(10)
            )
        """)
        changes += 1
        print("  + custom_coa_codes table created")

    # client_policies
    if "client_policies" not in tables:
        print("\n[client_policies] Creating table...")
        cursor.execute("""
            CREATE TABLE client_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL REFERENCES clients(id),
                policy_number INTEGER NOT NULL,
                title VARCHAR(100) NOT NULL,
                body TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        changes += 1
        print("  + client_policies table created")

    # ============================================================
    # 5. REMOVE OLD KMP TABLE (replaced by director.is_kmp)
    # ============================================================
    # Don't drop — just note it's deprecated
    if "kmp" in tables:
        print("\n[kmp] Table exists (deprecated — KMP now derived from directors.is_kmp)")

    conn.commit()
    conn.close()

    print(f"\n{'='*50}")
    if changes > 0:
        print(f"Migration complete: {changes} changes applied.")
    else:
        print("Database already up to date — no changes needed.")
    print(f"Backup at: {backup}")
    print(f"{'='*50}")
    print("\nYou can now start the app: python run.py")


if __name__ == "__main__":
    migrate()
