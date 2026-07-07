with source as (
    select * from {{ source('raw', 'fda_recalls') }}
),

cleaned as (
    select
        recall_number,
        status,
        classification,
        product_type,
        product_description,
        reason_for_recall,
        recalling_firm,
        city,
        state,
        country,
        distribution_pattern,
        voluntary_mandated,
        -- Convert date strings from YYYYMMDD format to actual dates
        to_date(recall_initiation_date, 'YYYYMMDD') as recall_initiation_date,
        to_date(report_date, 'YYYYMMDD')             as report_date,
        to_date(center_classification_date, 'YYYYMMDD') as center_classification_date,
        -- Extract year and month for easier aggregation later
        year(to_date(recall_initiation_date, 'YYYYMMDD'))  as recall_year,
        month(to_date(recall_initiation_date, 'YYYYMMDD')) as recall_month,
        -- Flag Class I recalls as high severity
        case
            when classification = 'Class I' then true
            else false
        end as is_high_severity,
        ingested_at
    from source
    where product_type = 'Food'
      and recall_initiation_date is not null
      and recall_initiation_date != ''
)

select * from cleaned
