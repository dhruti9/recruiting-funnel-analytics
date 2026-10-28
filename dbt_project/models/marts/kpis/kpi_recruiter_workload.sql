-- Load and throughput per recruiter as of the snapshot date (trailing 12 months).
with reqs as (
    select * from {{ ref('dim_requisition') }}
),

apps as (
    select * from {{ ref('fct_applications') }}
),

req_stats as (
    select
        recruiter_id,
        count(*) filter (where requisition_status = 'open')  as open_requisitions,
        count(*) filter (where requisition_status = 'filled'
            and filled_at >= {{ as_of() }} - interval 365 day) as reqs_filled_ttm,
        median(time_to_fill_days) filter (where filled_at >= {{ as_of() }} - interval 365 day)
                                                       as median_time_to_fill_days_ttm
    from reqs
    group by 1
),

app_stats as (
    select
        recruiter_id,
        count(*) filter (where application_status = 'active') as active_applications,
        count(*) filter (where application_status = 'active' and days_since_last_activity > 30)
                                                       as stale_applications,
        count(*) filter (where is_hired and hired_at >= {{ as_of() }} - interval 365 day) as hires_ttm,
        count(*) filter (where applied_at >= {{ as_of() }} - interval 365 day) as applications_ttm
    from apps
    group by 1
)

select
    r.recruiter_id,
    r.recruiter_name,
    r.recruiter_title,
    r.primary_department_name,
    r.is_active,
    coalesce(q.open_requisitions, 0)                   as open_requisitions,
    coalesce(a.active_applications, 0)                 as active_applications,
    coalesce(a.stale_applications, 0)                  as stale_applications,
    coalesce(a.applications_ttm, 0)                    as applications_ttm,
    coalesce(a.hires_ttm, 0)                           as hires_ttm,
    coalesce(q.reqs_filled_ttm, 0)                     as reqs_filled_ttm,
    q.median_time_to_fill_days_ttm
from {{ ref('dim_recruiter') }} r
left join req_stats q using (recruiter_id)
left join app_stats a using (recruiter_id)
