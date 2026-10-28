-- Stage-to-stage conversion, overall and by source.
-- Applications still sitting in a stage are excluded from that stage's denominator.
with t as (
    select t.*, s.source_name
    from {{ ref('fct_stage_transitions') }} t
    join {{ ref('dim_source') }} s using (source_id)
    where t.stage <> 'hired'
)

select
    coalesce(source_name, 'All sources')               as source_name,
    stage                                              as from_stage,
    stage_order,
    count(*)                                           as entered,
    count(*) filter (where stage_outcome = 'in_progress') as still_in_stage,
    count(*) filter (where stage_outcome = 'advanced')    as advanced,
    round(
        count(*) filter (where stage_outcome = 'advanced')::double
        / nullif(count(*) filter (where stage_outcome <> 'in_progress'), 0), 4
    )                                                  as conversion_rate
from t
group by grouping sets ((source_name, stage, stage_order), (stage, stage_order))
