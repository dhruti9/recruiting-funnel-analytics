select
    r.recruiter_id,
    r.recruiter_name,
    r.email,
    r.recruiter_title,
    r.primary_department_id,
    d.department_name                                  as primary_department_name,
    r.start_date,
    r.is_active
from {{ ref('stg_hris__recruiters') }} r
left join {{ ref('stg_hris__departments') }} d
    on r.primary_department_id = d.department_id
