-- Star schema for Power BI: one fact table (provider x month) and three dimensions.
DROP TABLE IF EXISTS mart.fact_ae_monthly, mart.dim_provider, mart.dim_region, mart.dim_date CASCADE;

CREATE TABLE mart.dim_date AS
SELECT DISTINCT
  to_char(month,'YYYYMMDD')::int                                   AS date_key,
  month,
  extract(year FROM month)::int                                    AS year,
  extract(month FROM month)::int                                   AS month_num,
  to_char(month,'Mon YYYY')                                        AS month_label,
  CASE WHEN extract(month FROM month) >= 4
       THEN extract(year FROM month)::int ELSE extract(year FROM month)::int - 1 END AS fy_start,
  CASE WHEN extract(month FROM month) >= 4
       THEN extract(year FROM month)::int || '/' || right((extract(year FROM month)::int+1)::text,2)
       ELSE (extract(year FROM month)::int-1) || '/' || right(extract(year FROM month)::text,2) END AS financial_year,
  extract(month FROM month) IN (12,1,2,3)                          AS is_winter
FROM staging.ae_monthly;
ALTER TABLE mart.dim_date ADD PRIMARY KEY (date_key);

CREATE TABLE mart.dim_region AS
SELECT row_number() OVER (ORDER BY region)::int AS region_key,
       region AS region_code,
       initcap(replace(region,'NHS ENGLAND ','')) AS region_name
FROM (SELECT DISTINCT region FROM staging.ae_monthly) r;
ALTER TABLE mart.dim_region ADD PRIMARY KEY (region_key);

-- Latest name and region per provider (names and regions can change over time)
CREATE TABLE mart.dim_provider AS
WITH latest AS (
  SELECT DISTINCT ON (org_code) org_code, provider_name, region
  FROM staging.ae_monthly ORDER BY org_code, month DESC),
type1 AS (SELECT org_code, SUM(att_t1) AS t1 FROM staging.ae_monthly GROUP BY org_code)
SELECT row_number() OVER (ORDER BY l.org_code)::int AS provider_key,
       l.org_code, initcap(l.provider_name) AS provider_name, r.region_key,
       CASE WHEN t.t1 > 0 THEN 'Major A&E (Type 1)' ELSE 'UTC / Other A&E' END AS provider_type
FROM latest l JOIN mart.dim_region r ON r.region_code = l.region JOIN type1 t USING (org_code);
ALTER TABLE mart.dim_provider ADD PRIMARY KEY (provider_key);

CREATE TABLE mart.fact_ae_monthly AS
SELECT to_char(s.month,'YYYYMMDD')::int                         AS date_key,
       p.provider_key,
       s.att_t1+s.att_t2+s.att_oth+s.bk_t1+s.bk_t2+s.bk_oth      AS attendances,
       s.att_t1+s.bk_t1                                          AS attendances_type1,
       s.o4_t1+s.o4_t2+s.o4_oth+s.o4bk_t1+s.o4bk_t2+s.o4bk_oth   AS over_4hrs,
       s.o4_t1+s.o4bk_t1                                         AS over_4hrs_type1,
       s.dta_4_12                                                AS waits_4_12hr_dta,
       s.dta_12                                                  AS waits_12hr_dta,
       s.adm_t1+s.adm_t2+s.adm_oth                               AS emergency_admissions_via_ae,
       s.adm_other                                               AS other_emergency_admissions
FROM staging.ae_monthly s JOIN mart.dim_provider p USING (org_code);
ALTER TABLE mart.fact_ae_monthly ADD PRIMARY KEY (date_key, provider_key);
ALTER TABLE mart.fact_ae_monthly ADD FOREIGN KEY (date_key) REFERENCES mart.dim_date;
ALTER TABLE mart.fact_ae_monthly ADD FOREIGN KEY (provider_key) REFERENCES mart.dim_provider;

-- Reporting view used for checks and quick analysis
CREATE OR REPLACE VIEW mart.v_national_monthly AS
SELECT d.month, SUM(f.attendances) AS attendances,
       ROUND(100.0*(SUM(f.attendances)-SUM(f.over_4hrs))/SUM(f.attendances),1) AS pct_within_4hrs,
       SUM(f.waits_12hr_dta) AS waits_12hr_dta
FROM mart.fact_ae_monthly f JOIN mart.dim_date d USING (date_key)
GROUP BY d.month ORDER BY d.month;
