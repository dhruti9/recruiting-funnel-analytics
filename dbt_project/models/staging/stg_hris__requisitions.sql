with source as (
    select * from {{ source('ats_extract', 'requisitions') }}
)

select
    requisition_id,
    trim(job_title)                                    as job_title,
    department_id,
    recruiter_id,
    hiring_manager,
    location,
    job_level,
    cast(headcount as integer)                         as headcount,
    cast(opened_at as timestamp)                       as opened_at,
    lower(status)                                      as requisition_status,
    cast(filled_at as timestamp)                       as filled_at_reported,
    cast(closed_at as timestamp)                       as closed_at
from source
