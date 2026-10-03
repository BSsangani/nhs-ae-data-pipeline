import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = Path(os.getenv("NHS_AE_RAW_DIR", ROOT / "data" / "raw"))
SQL_DIR = ROOT / "sql"
EXPORT_DIR = ROOT / "powerbi" / "data"
# Connection string comes from an environment variable so no credentials are stored in code.
DB_URL = os.getenv("NHS_AE_DB_URL", "postgresql+psycopg2://nhs:nhs@localhost:5432/nhs_ae")
