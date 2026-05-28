import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DB_PATH = os.path.join(DATA_DIR, "tce.db")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# DATABASE_URL precedence:
#   1. Explicit env var (Railway / Supabase Postgres in production)
#   2. Local SQLite fallback (development)
#
# Supabase/Heroku-style URLs sometimes start with "postgres://"; SQLAlchemy + psycopg
# require "postgresql://". Normalise it here so either form works.
_env_db_url = os.getenv("DATABASE_URL", "").strip()
if _env_db_url:
    if _env_db_url.startswith("postgres://"):
        _env_db_url = _env_db_url.replace("postgres://", "postgresql://", 1)
    DATABASE_URL = _env_db_url
else:
    DATABASE_URL = f"sqlite:///{DB_PATH}"

# Convenience flag used by database.py to decide connect_args
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# Access code for the simple login gate (overridable via env in production)
ACCESS_CODE = os.getenv("ACCESS_CODE", "ssaa2025")
