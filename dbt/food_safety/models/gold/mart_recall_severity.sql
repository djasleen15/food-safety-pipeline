with matched as (
    select * from {{ ref('int_outbreak_recall_matched') }}
),

by_severity as (
    select
        classification,
        is_high_severity,
        pathogen_category,
        count(*) as matched_outbreaks,
        round(avg(days_to_recall), 1) as avg_days_to_recall,
        median(days_to_recall) as median_days_to_recall,
        sum(illnesses) as total_illnesses,
        sum(hospitalizations) as total_hospitalizations,
        sum(deaths) as total_deaths
    from matched
    group by classification, is_high_severity, pathogen_category
)

select * from by_severity
order by avg_days_to_recall asc
