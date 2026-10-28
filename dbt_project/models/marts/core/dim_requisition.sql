with reqs as (
    select * from {{ ref('int_requisitions__fill') }}
)

select
    r.requisition_id,
    r.job_title,
    r.department_id,
    d.department_name,
    r.recruiter_id,
    rec.recruiter_name,
    r.hiring_manager,
    r.location,
    r.job_level,
    r.headcount,
    r.requisition_status,
    r.opened_at,
    r.filled_at,
    r.closed_at,
    r.hires,
    r.first_hire_at,
    date_diff('day', r.opened_at, r.filled_at)         as time_to_fill_days,
    case when r.requisition_status = 'open'
        then date_diff('day', cast(r.opened_at as date), {{ as_of() }})
    end                                                as days_open,
    r.is_filled_date_recovered
from reqs r
left join {{ ref('stg_hris__departments') }} d using (department_id)
left join {{ ref('stg_hris__recruiters') }} rec using (recruiter_id)
