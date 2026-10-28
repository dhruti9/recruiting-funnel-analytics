with source as (
    select * from {{ source('ats_extract', 'applications') }}
)

select
    application_id,
    candidate_id,
    requisition_id,
    nullif(trim(source_id), '')                        as source_id,
    cast(applied_at as timestamp)                      as applied_at,
    lower(trim(current_stage))                         as current_stage,
    lower(trim(status))                                as application_status,
    nullif(trim(reject_reason), '')                    as reject_reason,
    cast(hired_at as timestamp)                        as hired_at_reported,
    cast(last_activity_at as timestamp)                as last_activity_at
from source
