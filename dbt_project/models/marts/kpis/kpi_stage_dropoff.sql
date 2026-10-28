-- Where candidates leave the funnel, and why.
with t as (
    select * from {{ ref('fct_stage_transitions') }} where stage <> 'hired'
),

reasons as (
    select
        current_stage                                  as stage,
        reject_reason,
        count(*)                                       as n,
        row_number() over (partition by current_stage order by count(*) desc) as rn
    from {{ ref('fct_applications') }}
    where application_status = 'rejected' and reject_reason is not null
    group by 1, 2
),

agg as (
    select
        stage,
        stage_order,
        count(*)                                       as entered,
        count(*) filter (where stage_outcome = 'advanced')    as advanced,
        count(*) filter (where stage_outcome = 'rejected')    as rejected,
        count(*) filter (where stage_outcome = 'withdrawn')   as withdrawn,
        count(*) filter (where stage_outcome = 'declined')    as offer_declined,
        count(*) filter (where stage_outcome = 'in_progress') as still_in_stage
    from t
    group by 1, 2
)

select
    a.*,
    a.rejected + a.withdrawn + a.offer_declined        as dropped,
    round((a.rejected + a.withdrawn + a.offer_declined)::double
          / nullif(a.entered - a.still_in_stage, 0), 4) as dropoff_rate,
    r.reject_reason                                    as top_reject_reason
from agg a
left join reasons r on r.stage = a.stage and r.rn = 1
