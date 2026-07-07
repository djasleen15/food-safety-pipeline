with matched as (
    select * from {{ ref('int_outbreak_recall_matched') }}
),

by_year as (
    select
        outbreak_year,
        count(*) as matched_outbreaks,
        round(avg(days_to_recall), 1) as avg_days_to_recall,
        median(days_to_recall) as median_days_to_recall,
        sum(illnesses) as total_illnesses,
        sum(hospitalizations) as total_hospitalizations,
        -- Calculate a simple year over year change in avg lag
        round(avg(days_to_recall) - lag(avg(days_to_recall)) over (
            order by outbreak_year
        ), 1) as yoy_change_in_avg_days
    from matched
    group by outbreak_year
)

select * from by_year
order by outbreak_year asc
