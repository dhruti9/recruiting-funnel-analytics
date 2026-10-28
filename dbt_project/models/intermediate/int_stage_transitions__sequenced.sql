-- Orders each application's forward funnel moves by *logical* stage order,
-- measures time spent in each stage, and flags timestamps that go backwards.
with events as (
    select * from {{ ref('stg_ats__stage_transitions') }}
    where not is_duplicate_event
),

terminal as (
    select application_id, min(transitioned_at) as terminal_at
    from events
    where to_stage in ('rejected', 'withdrawn', 'declined')
    group by 1
),

forward as (
    select
        e.application_id,
        e.transition_id,
        e.to_stage                                     as stage,
        e.to_stage_order                               as stage_order,
        e.transitioned_at                              as entered_at,
        lag(e.transitioned_at) over w                  as previous_stage_entered_at,
        lead(e.transitioned_at) over w                 as next_stage_entered_at,
        lead(e.to_stage) over w                        as next_stage
    from events e
    where e.to_stage_order is not null
    window w as (partition by e.application_id order by e.to_stage_order)
),

flagged as (
    select
        f.*,
        t.terminal_at,
        coalesce(f.entered_at < f.previous_stage_entered_at, false)
            or coalesce(f.next_stage_entered_at is null and t.terminal_at < f.entered_at, false) as is_out_of_order,
        coalesce(f.next_stage_entered_at, case when f.stage <> 'hired' then t.terminal_at end) as exited_at
    from forward f
    left join terminal t using (application_id)
)

select
    *,
    bool_or(is_out_of_order) over (partition by application_id) as application_has_out_of_order,
    case
        when bool_or(is_out_of_order) over (partition by application_id) then null
        else round(date_diff('second', entered_at, exited_at) / 86400.0, 2)
    end                                                as days_in_stage
from flagged
