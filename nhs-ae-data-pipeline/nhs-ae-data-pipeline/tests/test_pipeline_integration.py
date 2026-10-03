"""End-to-end test: runs the pipeline on 2 sample files into a separate test database.
Skipped automatically when no PostgreSQL test database is available."""
import os, shutil, subprocess, sys, pytest
from pathlib import Path
from sqlalchemy import create_engine, text

TEST_DB = os.getenv("NHS_AE_TEST_DB_URL", "postgresql+psycopg2://nhs:nhs@localhost:5432/nhs_ae_test")
ROOT = Path(__file__).resolve().parents[1]

def db_available():
    try:
        create_engine(TEST_DB).connect().close(); return True
    except Exception:
        return False

@pytest.mark.skipif(not db_available(), reason="no PostgreSQL test database")
def test_pipeline_end_to_end(tmp_path):
    eng = create_engine(TEST_DB)
    with eng.begin() as c: c.execute(text("DROP SCHEMA IF EXISTS raw, staging, mart, audit CASCADE"))
    # one clean file + the file with stray columns
    for f in ["April-2022-revised-130624-F4scP.csv", "Monthly-AE-September-2024.csv"]:
        shutil.copy(ROOT / "data" / "raw" / f, tmp_path / f)
    env = {**os.environ, "NHS_AE_DB_URL": TEST_DB, "NHS_AE_RAW_DIR": str(tmp_path)}
    for _ in range(2):  # second run must load nothing new (idempotent)
        subprocess.run([sys.executable, "-m", "pipeline.run"], cwd=ROOT, env=env, check=True)
    with eng.connect() as c:
        assert c.execute(text("SELECT COUNT(*) FROM raw.load_log")).scalar() == 2
        assert c.execute(text("SELECT COUNT(DISTINCT month) FROM staging.ae_monthly")).scalar() == 2
        assert c.execute(text("SELECT COUNT(*) FROM staging.ae_monthly WHERE upper(org_code)='TOTAL'")).scalar() == 0
        assert c.execute(text("SELECT COUNT(*) FROM audit.dq_results WHERE status='fail'")).scalar() == 0
        runs = c.execute(text("SELECT files_loaded FROM audit.pipeline_runs ORDER BY finished_at")).scalars().all()
        assert runs == [2, 0]
