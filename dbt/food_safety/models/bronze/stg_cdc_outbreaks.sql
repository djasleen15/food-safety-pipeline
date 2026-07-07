with source as (
    select * from {{ source('raw', 'cdc_outbreaks') }}
),

cleaned as (
    select
        -- Build a surrogate key since CDC data has no unique ID
        row_number() over (order by year, month, state, etiology) as outbreak_id,
        year::integer                as outbreak_year,
        month::integer               as outbreak_month,
        state,
        primary_mode,
        etiology                     as pathogen_raw,
        etiology_status,
        setting,
        food_vehicle,
        food_contaminated_ingredient,
        ifsac_category               as food_category,
        -- Cast numeric fields
        try_cast(illnesses as integer)       as illnesses,
        try_cast(hospitalizations as integer) as hospitalizations,
        try_cast(deaths as integer)           as deaths,
        -- Build an approximate date from year and month
        -- We use day 1 as a placeholder since CDC only reports month-level
        to_date(
            year || '-' || lpad(month, 2, '0') || '-01',
            'YYYY-MM-DD'
        ) as outbreak_date
    from source
    where primary_mode = 'Food'
      and year is not null
      and etiology is not null
      and etiology != ''
)

select * from cleaned
