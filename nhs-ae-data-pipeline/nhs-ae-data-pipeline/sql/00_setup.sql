-- Layers: raw (as received) -> staging (cleaned, typed) -> mart (star schema for Power BI) ; audit (run + data quality log)
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS mart;
CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE IF NOT EXISTS raw.ae_monthly (
  period text, org_code text, parent_org text, org_name text,
  att_t1 text, att_t2 text, att_oth text, bk_t1 text, bk_t2 text, bk_oth text,
  o4_t1 text, o4_t2 text, o4_oth text, o4bk_t1 text, o4bk_t2 text, o4bk_oth text,
  dta_4_12 text, dta_12 text, adm_t1 text, adm_t2 text, adm_oth text, adm_other text,
  source_file text NOT NULL, loaded_at timestamptz DEFAULT now());

CREATE TABLE IF NOT EXISTS raw.load_log (
  file_name text, file_hash text PRIMARY KEY, row_count int, loaded_at timestamptz DEFAULT now());

CREATE TABLE IF NOT EXISTS audit.dq_results (
  run_id text, check_name text, severity text, failing_rows int, status text, checked_at timestamptz DEFAULT now());

CREATE TABLE IF NOT EXISTS audit.pipeline_runs (
  run_id text PRIMARY KEY, files_loaded int, rows_loaded int, seconds numeric, status text, finished_at timestamptz DEFAULT now());
