with matched as (
    select * from {{ ref('int_outbreak_recall_matched') }}
),

by_pathogen as (
    select
        pathogen_category,
        -- Extract the primary pathogen from the raw field
        -- CDC uses semicolons to separate multiple pathogens
        -- We take the first one as the primary
        split_part(pathogen_raw, ';', 1) as primary_pathogen,
        count(*) as matched_outbreaks,
        round(avg(days_to_recall), 1) as avg_days_to_recall,
        median(days_to_recall) as median_days_to_recall,
        min(days_to_recall) as min_days_to_recall,
        max(days_to_recall) as max_days_to_recall,
        sum(illnesses) as total_illnesses,
        sum(hospitalizations) as total_hospitalizations,
        sum(deaths) as total_deaths
    from matched
    group by pathogen_category, split_part(pathogen_raw, ';', 1)
)

select * from by_pathogen
order by avg_days_to_recall asc
