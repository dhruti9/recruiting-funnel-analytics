-- Grain: one row per application. The central fact table for funnel analysis.
with journey as (
    select * from {{ ref('int_applications__journey') }}
),

candidates as (
    select candidate_id, canonical_candidate_id from {{ ref('int_candidates__resolved') }}
),

reqs as (
    select requisition_id, department_id, recruiter_id, job_level
    from {{ ref('stg_hris__requisitions') }}
),

offers as (
    select * from {{ ref('int_offers__resolved') }}
),

interviews as (
    select application_id, count(*) as interviews, avg(score) as avg_interview_score
    from {{ ref('stg_scheduling__interviews') }}
    group by 1
)

select
    j.application_id,
    c.canonical_candidate_id                           as candidate_id,
    j.candidate_id                                     as ats_candidate_id,
    j.requisition_id,
    r.department_id,
    r.recruiter_id,
    r.job_level,
    coalesce(j.source_id, 'UNKNOWN')                   as source_id,
    j.applied_at,
    cast(date_trunc('month', j.applied_at) as date)    as applied_month,
    j.application_status,
    j.current_stage,
    j.reject_reason,
    {% for s in funnel_stages() -%}
    j.{{ s }}_entered_at is not null                   as reached_{{ s }},
    {% endfor -%}
    j.hired_at,
    j.application_status = 'hired'                     as is_hired,
    date_diff('day', j.applied_at, j.hired_at)         as time_to_hire_days,
    o.offer_id,
    o.offer_status,
    o.base_salary_usd,
    coalesce(i.interviews, 0)                          as interviews,
    round(i.avg_interview_score, 2)                    as avg_interview_score,
    j.last_activity_at,
    case when j.application_status = 'active'
        then date_diff('day', cast(j.last_activity_at as date), {{ as_of() }})
    end                                                as days_since_last_activity,
    -- data-quality flags (see dq_issue_log)
    j.application_status = 'rejected' and j.reject_reason is null as is_missing_reject_reason,
    j.source_id is null                                as is_missing_source,
    j.has_out_of_order_stages,
    j.is_hire_date_recovered,
    o.offer_id is not null and coalesce(i.interviews, 0) = 0 as is_offer_without_interviews
from journey j
left join candidates c using (candidate_id)
left join reqs r using (requisition_id)
left join offers o using (application_id)
left join interviews i using (application_id)
