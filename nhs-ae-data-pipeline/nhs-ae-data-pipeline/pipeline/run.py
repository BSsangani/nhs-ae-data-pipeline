"""Orchestrates the pipeline: extract -> staging -> data quality -> marts -> Power BI export."""
import logging, time, uuid, sys
import pandas as pd
from sqlalchemy import create_engine, text
from .config import DB_URL, SQL_DIR, EXPORT_DIR, ROOT
from .extract import extract
from .quality import run_checks

def run_sql(engine, name):
    raw = engine.raw_connection()   # plain DB-API cursor so '%' in SQL is not treated as a parameter
    try:
        with raw.cursor() as cur:
            cur.execute((SQL_DIR / name).read_text())
        raw.commit()
    finally:
        raw.close()

def export_marts(engine):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    counts = {}
    for t in ["dim_date", "dim_region", "dim_provider", "fact_ae_monthly"]:
        df = pd.read_sql(f"SELECT * FROM mart.{t}", engine); df.to_csv(EXPORT_DIR / f"{t}.csv", index=False); counts[t] = len(df)
    return counts

def main():
    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(ROOT / "logs" / "pipeline.log")])
    log = logging.getLogger("pipeline"); run_id = str(uuid.uuid4())[:8]; t0 = time.time()
    engine = create_engine(DB_URL)
    run_sql(engine, "00_setup.sql")
    ext = extract(engine)
    run_sql(engine, "01_staging.sql")
    run_checks(engine, run_id)
    run_sql(engine, "02_marts.sql")
    exported = export_marts(engine)
    secs = round(time.time() - t0, 1)
    with engine.begin() as con:
        con.execute(text("INSERT INTO audit.pipeline_runs(run_id, files_loaded, rows_loaded, seconds, status) VALUES (:r,:f,:n,:s,'success')"),
                    {"r": run_id, "f": ext["files_loaded"], "n": ext["rows_loaded"], "s": secs})
    log.info("Run %s finished in %ss | %s | exported %s", run_id, secs, ext, exported)

if __name__ == "__main__":
    main()
