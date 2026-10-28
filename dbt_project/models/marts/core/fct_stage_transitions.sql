-- Grain: one row per application per funnel stage entered.
-- Durations are NULL for applications with out-of-order timestamps (quarantined).
with stages as (
    select * from {{ ref('int_stage_transitions__sequenced') }}
),

apps as (
    select application_id, requisition_id, department_id, recruiter_id, source_id, application_status
    from {{ ref('fct_applications') }}
)

select
    s.transition_id,
    s.application_id,
    a.requisition_id,
    a.department_id,
    a.recruiter_id,
    a.source_id,
    s.stage,
    s.stage_order,
    s.entered_at,
    s.exited_at,
    s.next_stage,
    case
        when s.next_stage is not null then 'advanced'
        when s.stage = 'hired' then 'hired'
        when s.exited_at is null then 'in_progress'
        when a.application_status = 'offer_declined' then 'declined'
        else a.application_status
    end                                                as stage_outcome,
    s.days_in_stage,
    s.is_out_of_order,
    s.application_has_out_of_order                     as is_quarantined
from stages s
join apps a using (application_id)
