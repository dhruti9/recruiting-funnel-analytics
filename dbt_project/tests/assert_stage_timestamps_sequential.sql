-- Business rule: for every application that is not quarantined, each funnel stage is
-- entered no earlier than the stage before it, and is exited no earlier than it was entered.
-- Out-of-order applications must be caught by the quarantine flag, never reach KPIs.
with t as (
    select
        application_id,
        stage,
        entered_at,
        exited_at,
        lag(entered_at) over (partition by application_id order by stage_order) as prev_entered_at
    from {{ ref('fct_stage_transitions') }}
    where not is_quarantined
)
select *
from t
where entered_at < prev_entered_at
   or exited_at < entered_at
