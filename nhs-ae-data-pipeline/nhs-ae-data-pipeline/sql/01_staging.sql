-- Clean and type the raw data. Rebuilt in full on every run (small data, simplest correct approach).
DROP TABLE IF EXISTS staging.ae_monthly;
DROP TABLE IF EXISTS staging.published_totals;

CREATE TEMP TABLE typed AS
SELECT
  source_file,
  -- NHS England files contain summary rows with inconsistent labels ('TOTAL', 'Total ', 'TOTAl' ...),
  -- sometimes hidden under a normal month label, so detect them on both fields.
  (period NOT ILIKE 'MSitAE-%' OR upper(trim(org_code)) = 'TOTAL')          AS is_total,
  CASE WHEN period ILIKE 'MSitAE-%'
       THEN to_date(initcap(replace(trim(period), 'MSitAE-', '')), 'FMMonth-YYYY') END AS month,
  trim(org_code)                                  AS org_code,
  upper(trim(parent_org))                         AS region,     -- region names arrive with trailing spaces
  upper(trim(org_name))                           AS provider_name,
  COALESCE(NULLIF(trim(att_t1),'')::numeric,0)::bigint   AS att_t1,
  COALESCE(NULLIF(trim(att_t2),'')::numeric,0)::bigint   AS att_t2,
  COALESCE(NULLIF(trim(att_oth),'')::numeric,0)::bigint  AS att_oth,
  COALESCE(NULLIF(trim(bk_t1),'')::numeric,0)::bigint    AS bk_t1,
  COALESCE(NULLIF(trim(bk_t2),'')::numeric,0)::bigint    AS bk_t2,
  COALESCE(NULLIF(trim(bk_oth),'')::numeric,0)::bigint   AS bk_oth,
  COALESCE(NULLIF(trim(o4_t1),'')::numeric,0)::bigint    AS o4_t1,
  COALESCE(NULLIF(trim(o4_t2),'')::numeric,0)::bigint    AS o4_t2,
  COALESCE(NULLIF(trim(o4_oth),'')::numeric,0)::bigint   AS o4_oth,
  COALESCE(NULLIF(trim(o4bk_t1),'')::numeric,0)::bigint  AS o4bk_t1,
  COALESCE(NULLIF(trim(o4bk_t2),'')::numeric,0)::bigint  AS o4bk_t2,
  COALESCE(NULLIF(trim(o4bk_oth),'')::numeric,0)::bigint AS o4bk_oth,
  COALESCE(NULLIF(trim(dta_4_12),'')::numeric,0)::bigint AS dta_4_12,
  COALESCE(NULLIF(trim(dta_12),'')::numeric,0)::bigint   AS dta_12,
  COALESCE(NULLIF(trim(adm_t1),'')::numeric,0)::bigint   AS adm_t1,
  COALESCE(NULLIF(trim(adm_t2),'')::numeric,0)::bigint   AS adm_t2,
  COALESCE(NULLIF(trim(adm_oth),'')::numeric,0)::bigint  AS adm_oth,
  COALESCE(NULLIF(trim(adm_other),'')::numeric,0)::bigint AS adm_other
FROM raw.ae_monthly;

CREATE TABLE staging.published_totals AS
SELECT source_file, att_t1 FROM typed WHERE is_total;

CREATE TABLE staging.ae_monthly AS
SELECT * FROM typed WHERE NOT is_total;
ALTER TABLE staging.ae_monthly DROP COLUMN is_total;
DROP TABLE typed;
