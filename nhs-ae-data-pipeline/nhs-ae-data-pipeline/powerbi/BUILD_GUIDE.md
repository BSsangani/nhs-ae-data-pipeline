# Build the NHS A&E Performance dashboard in Power BI Desktop (about 2–3 hours)

The pipeline has already produced a clean **star schema** in `powerbi/data/`:

| File | Rows | What it is |
|---|---|---|
| `fact_ae_monthly.csv` | 9,623 | One row per provider per month: attendances, 4-hour breaches, 12-hour waits, admissions |
| `dim_date.csv` | 48 | Months Apr 2022 – Mar 2026, financial year, winter flag |
| `dim_provider.csv` | 221 | Trusts / sites, provider type, region key |
| `dim_region.csv` | 7 | NHS England regions |

## Step 1 – Load and model the data
1. Power BI Desktop → **Get data → Text/CSV**, load all four files.
2. In **Power Query**, check types: `month` = Date; keys = Whole number; `is_winter` = True/False. Close & Apply.
3. **Model view** – create relationships (single direction, many-to-one):
   - `fact_ae_monthly[date_key]` → `dim_date[date_key]`
   - `fact_ae_monthly[provider_key]` → `dim_provider[provider_key]`
   - `dim_provider[region_key]` → `dim_region[region_key]`
4. Select `dim_date` → **Mark as date table** (column `month`). Sort `month_label` by `month`.
5. Hide key columns from report view.
6. Add the measures from `DAX_measures.md`.

## Step 2 – Page 1: National Overview
- **Slicer:** `dim_date[financial_year]` (tile style).
- **KPI cards:** `% Within 4 Hours`, `Gap to Target (pts)`, `Attendances`, `12hr Waits from DTA`.
- **Line chart:** X = `dim_date[month]`, Y = `% Within 4 Hours` and `Type 1 % Within 4 Hours`; add **constant lines** at 78% (Interim Target) and 95% (Constitutional Standard) in the Analytics pane.
- **Column chart:** `12hr Waits from DTA` by month.
- Expected check: March 2026 should show **77.1%**; FY 2025/26 should show **74.9%**.

## Step 3 – Page 2: Regional Comparison
- **Bar chart:** `dim_region[region_name]` by `% Within 4 Hours`, sorted ascending, with a 78% constant line.
- **Matrix:** rows = region, columns = `financial_year`, values = `% Within 4 Hours`; **conditional formatting** background colour (red → green).
- Expected check: in 2025/26 London is highest (77.2%), North West lowest (72.4%).

## Step 4 – Page 3: Trust Explorer
- **Slicers:** `dim_provider[provider_type]` (set to Major A&E (Type 1)), `dim_region[region_name]`, `dim_provider[provider_name]` (searchable dropdown).
- **Line chart:** `% Within 4 Hours` and `England % Within 4 Hours` by month – selected trust vs England.
- **Table:** provider name, `Attendances`, `% Within 4 Hours`, `Provider Rank (worst first)`, sorted by rank; add data bars.
- Create a **bookmark** "Leicester spotlight" with University Hospitals of Leicester selected (expected: FY 2025/26 average around 62–63%).

## Step 5 – Finish
- Add a title bar, NHS-style colours (#005EB8 blue), and a text box: "Source: NHS England A&E Attendances and Emergency Admissions, Open Government Licence v3.0".
- Add **tooltips** and a **drill-through** page from region → trusts (optional, good interview talking point).
- Save as `NHS_AE_Dashboard.pbix`, take a screenshot of each page into `powerbi/screenshots/`, and add them to the README.
- Optional: publish to the Power BI Service (free account) and put the link in your README.

**Interview talking points:** why a star schema, why a separate date table, what DIVIDE does, how you checked your numbers against the pipeline (the expected checks above).
