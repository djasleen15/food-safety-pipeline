with matched as (
    select * from {{ ref('int_outbreak_recall_matched') }}
),

by_category as (
    select
        coalesce(food_category, 'Unknown') as food_category,
        pathogen_category,
        count(*) as matched_outbreaks,
        round(avg(days_to_recall), 1) as avg_days_to_recall,
        median(days_to_recall) as median_days_to_recall,
        sum(illnesses) as total_illnesses,
        sum(hospitalizations) as total_hospitalizations,
        sum(deaths) as total_deaths
    from matched
    group by coalesce(food_category, 'Unknown'), pathogen_category
)

select * from by_category
order by avg_days_to_recall asc
