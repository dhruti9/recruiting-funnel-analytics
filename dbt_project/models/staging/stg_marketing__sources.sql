select
    source_id,
    source_name,
    source_type,
    cast(cost_per_application_usd as double)           as cost_per_application_usd,
    cast(fee_per_hire_usd as double)                   as fee_per_hire_usd,
    cast(fee_pct_of_base_salary as double)             as fee_pct_of_base_salary
from {{ source('ats_extract', 'sources') }}
