"""Extract: load new monthly NHS England A&E CSV files into the raw layer (incremental, idempotent)."""
import hashlib, logging
import pandas as pd
from sqlalchemy import text
from .config import RAW_DIR

log = logging.getLogger(__name__)
RAW_COLUMNS = {  # source column -> raw column
 "Period":"period","Org Code":"org_code","Parent Org":"parent_org","Org name":"org_name",
 "A&E attendances Type 1":"att_t1","A&E attendances Type 2":"att_t2","A&E attendances Other A&E Department":"att_oth",
 "A&E attendances Booked Appointments Type 1":"bk_t1","A&E attendances Booked Appointments Type 2":"bk_t2",
 "A&E attendances Booked Appointments Other Department":"bk_oth",
 "Attendances over 4hrs Type 1":"o4_t1","Attendances over 4hrs Type 2":"o4_t2","Attendances over 4hrs Other Department":"o4_oth",
 "Attendances over 4hrs Booked Appointments Type 1":"o4bk_t1","Attendances over 4hrs Booked Appointments Type 2":"o4bk_t2",
 "Attendances over 4hrs Booked Appointments Other Department":"o4bk_oth",
 "Patients who have waited 4-12 hs from DTA to admission":"dta_4_12","Patients who have waited 12+ hrs from DTA to admission":"dta_12",
 "Emergency admissions via A&E - Type 1":"adm_t1","Emergency admissions via A&E - Type 2":"adm_t2",
 "Emergency admissions via A&E - Other A&E department":"adm_oth","Other emergency admissions":"adm_other"}

def file_hash(path):
    return hashlib.md5(path.read_bytes()).hexdigest()

def read_source(path):
    df = pd.read_csv(path, dtype=str)
    unknown = [c for c in df.columns if c not in RAW_COLUMNS]
    missing = [c for c in RAW_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{path.name}: missing expected columns {missing}")
    if unknown:
        log.warning("%s: dropping %d unexpected column(s) %s", path.name, len(unknown), unknown)
    df = df[list(RAW_COLUMNS)].rename(columns=RAW_COLUMNS)
    df["source_file"] = path.name
    return df

def extract(engine, files=None):
    files = sorted(files or RAW_DIR.glob("*.csv"))
    with engine.begin() as con:
        loaded = {r[0] for r in con.execute(text("SELECT file_hash FROM raw.load_log"))}
    new = [f for f in files if file_hash(f) not in loaded]
    log.info("Extract: %d files found, %d already loaded, %d new", len(files), len(files)-len(new), len(new))
    rows = 0
    for f in new:
        df = read_source(f)
        with engine.begin() as con:
            df.to_sql("ae_monthly", con, schema="raw", if_exists="append", index=False)
            con.execute(text("INSERT INTO raw.load_log(file_name, file_hash, row_count) VALUES (:n,:h,:r)"),
                        {"n": f.name, "h": file_hash(f), "r": len(df)})
        rows += len(df)
    return {"files_found": len(files), "files_loaded": len(new), "rows_loaded": rows}
