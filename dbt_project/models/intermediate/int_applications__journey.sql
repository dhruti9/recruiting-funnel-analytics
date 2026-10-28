-- One row per application with the timestamp at which each funnel stage was reached
-- and the terminal outcome. Recovers hire dates that the ATS failed to populate.
with apps as (
    select * from {{ ref('stg_ats__applications') }}
),

stages as (
    select * from {{ ref('int_stage_transitions__sequenced') }}
),

pivoted as (
    select
        application_id,
        {% for s in funnel_stages() -%}
        min(case when stage = '{{ s }}' then entered_at end) as {{ s }}_entered_at,
        {% endfor -%}
        max(stage_order)                               as furthest_stage_order,
        bool_or(application_has_out_of_order)          as has_out_of_order_stages,
        max(terminal_at)                               as terminal_at
    from stages
    group by 1
)

select
    a.application_id,
    a.candidate_id,
    a.requisition_id,
    a.source_id,
    a.applied_at,
    a.current_stage,
    a.application_status,
    a.reject_reason,
    a.hired_at_reported,
    coalesce(a.hired_at_reported, p.hired_entered_at)  as hired_at,
    a.hired_at_reported is null
        and a.application_status = 'hired'             as is_hire_date_recovered,
    a.last_activity_at,
    {% for s in funnel_stages() -%}
    p.{{ s }}_entered_at,
    {% endfor -%}
    p.furthest_stage_order,
    p.terminal_at,
    coalesce(p.has_out_of_order_stages, false)         as has_out_of_order_stages
from apps a
left join pivoted p using (application_id)
