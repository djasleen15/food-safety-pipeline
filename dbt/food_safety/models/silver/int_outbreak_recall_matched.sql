with outbreaks as (
    select * from {{ ref('stg_cdc_outbreaks') }}
),

recalls as (
    select * from {{ ref('stg_fda_recalls') }}
),

pathogen_map as (
    select * from {{ ref('pathogen_mapping') }}
),

matched as (
    select
        o.outbreak_id,
        o.outbreak_date,
        o.outbreak_year,
        o.outbreak_month,
        o.state,
        o.pathogen_raw,
        o.food_category,
        o.illnesses,
        o.hospitalizations,
        o.deaths,
        r.recall_number,
        r.recall_initiation_date,
        r.recalling_firm,
        r.classification,
        r.is_high_severity,
        r.product_description,
        r.reason_for_recall,
        p.pathogen_category,
        datediff('day', o.outbreak_date, r.recall_initiation_date) as days_to_recall
    from outbreaks o
    inner join pathogen_map p
        on contains(lower(o.pathogen_raw), lower(p.pathogen_keyword))
    inner join recalls r
        on contains(lower(r.reason_for_recall), lower(p.fda_keyword))
        and r.recall_initiation_date >= o.outbreak_date
        and r.recall_initiation_date <= dateadd('day', 180, o.outbreak_date)
),

-- Keep only the earliest recall per outbreak
-- This is the most defensible match since proximity in time
-- is the strongest signal of a causal relationship
best_match as (
    select *,
        row_number() over (
            partition by outbreak_id
            order by days_to_recall asc, recall_number asc
        ) as rn
    from matched
)

select
    outbreak_id,
    outbreak_date,
    outbreak_year,
    outbreak_month,
    state,
    pathogen_raw,
    food_category,
    illnesses,
    hospitalizations,
    deaths,
    recall_number,
    recall_initiation_date,
    recalling_firm,
    classification,
    is_high_severity,
    product_description,
    reason_for_recall,
    pathogen_category,
    days_to_recall
from best_match
where rn = 1