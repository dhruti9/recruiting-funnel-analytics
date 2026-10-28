select
    recruiter_id,
    recruiter_name,
    lower(email)                                       as email,
    primary_department_id,
    title                                              as recruiter_title,
    cast(start_date as date)                           as start_date,
    cast(is_active as boolean)                         as is_active
from {{ source('ats_extract', 'recruiters') }}
