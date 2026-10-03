# DAX measures for the NHS A&E Power BI dashboard
Create a table called `_Measures` (Home → Enter data → OK) and add each measure below (Modeling → New measure).

```DAX
Attendances = SUM ( fact_ae_monthly[attendances] )

Over 4 Hours = SUM ( fact_ae_monthly[over_4hrs] )

% Within 4 Hours =
DIVIDE ( [Attendances] - [Over 4 Hours], [Attendances] )

Type 1 % Within 4 Hours =
DIVIDE (
    SUM ( fact_ae_monthly[attendances_type1] ) - SUM ( fact_ae_monthly[over_4hrs_type1] ),
    SUM ( fact_ae_monthly[attendances_type1] )
)

Interim Target = 0.78

Constitutional Standard = 0.95

Gap to Target (pts) = ( [% Within 4 Hours] - [Interim Target] ) * 100

12hr Waits from DTA = SUM ( fact_ae_monthly[waits_12hr_dta] )

Emergency Admissions = SUM ( fact_ae_monthly[emergency_admissions_via_ae] ) + SUM ( fact_ae_monthly[other_emergency_admissions] )

-- Same month last year (dim_date holds one row per month, so the prior year is found with an explicit filter)
Attendances PY =
VAR y = MAX ( dim_date[year] )
VAR m = MAX ( dim_date[month_num] )
RETURN
    CALCULATE ( [Attendances], FILTER ( ALL ( dim_date ), dim_date[year] = y - 1 && dim_date[month_num] = m ) )

Attendances YoY % = DIVIDE ( [Attendances] - [Attendances PY], [Attendances PY] )

England % Within 4 Hours =
CALCULATE ( [% Within 4 Hours], REMOVEFILTERS ( dim_provider ), REMOVEFILTERS ( dim_region ) )

Provider Rank (worst first) =
RANKX ( ALLSELECTED ( dim_provider[provider_name] ), [% Within 4 Hours], , ASC, DENSE )
```

Format: `% Within 4 Hours`, `Type 1 % Within 4 Hours`, `Interim Target`, `England % Within 4 Hours` and `Attendances YoY %` as **Percentage, 1 decimal place**; counts as **Whole number with thousands separator**.
