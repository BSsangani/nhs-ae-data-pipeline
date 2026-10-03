"""Data quality checks on the staging layer. Critical failures stop the pipeline before marts are rebuilt."""
import logging
from sqlalchemy import text
log = logging.getLogger(__name__)

CHECKS = [  # (name, severity, SQL returning the number of failing rows)
 ("no duplicate provider-month rows", "critical",
  "SELECT COUNT(*) FROM (SELECT month, org_code FROM staging.ae_monthly GROUP BY 1,2 HAVING COUNT(*)>1) d"),
 ("no negative counts", "critical",
  "SELECT COUNT(*) FROM staging.ae_monthly WHERE LEAST(att_t1,att_t2,att_oth,bk_t1,bk_t2,bk_oth,o4_t1,o4_t2,o4_oth,dta_12)<0"),
 ("4-hour breaches never exceed attendances", "critical",
  "SELECT COUNT(*) FROM staging.ae_monthly WHERE o4_t1+o4bk_t1 > att_t1+bk_t1"),
 ("every month parsed to a valid date", "critical",
  "SELECT COUNT(*) FROM staging.ae_monthly WHERE month IS NULL"),
 ("provider rows reconcile to published TOTAL rows (type 1 attendances)", "critical",
  """SELECT COUNT(*) FROM (
       SELECT p.source_file FROM staging.ae_monthly p
       JOIN staging.published_totals t USING (source_file)
       GROUP BY p.source_file, t.att_t1 HAVING SUM(p.att_t1) <> t.att_t1) x"""),
 ("every source file has a published TOTAL row", "warning",
  "SELECT COUNT(*) FROM (SELECT file_name FROM raw.load_log EXCEPT SELECT source_file FROM staging.published_totals) x"),
 ("region name present", "warning", "SELECT COUNT(*) FROM staging.ae_monthly WHERE region IS NULL OR region=''"),
]

def run_checks(engine, run_id):
    results, failed = [], []
    with engine.begin() as con:
        for name, sev, sql in CHECKS:
            n = con.execute(text(sql)).scalar()
            status = "pass" if n == 0 else ("fail" if sev == "critical" else "warn")
            con.execute(text("INSERT INTO audit.dq_results(run_id, check_name, severity, failing_rows, status) VALUES (:r,:c,:s,:n,:st)"),
                        {"r": run_id, "c": name, "s": sev, "n": n, "st": status})
            results.append((name, sev, n, status)); log.info("DQ %-70s %s (%d)", name, status.upper(), n)
            if status == "fail": failed.append(name)
    if failed:
        raise RuntimeError(f"Critical data quality checks failed: {failed}")
    return results
