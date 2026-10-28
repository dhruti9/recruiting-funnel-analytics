-- Reconciliation: the number of candidates who entered stage N+1 must equal the number
-- who advanced out of stage N, for every source. Guards against fan-out / dropped joins.
with c as (
    select
        source_name,
        stage_order,
        entered,
        advanced,
        lead(entered) over (partition by source_name order by stage_order) as next_entered
    from {{ ref('kpi_stage_conversion') }}
)
select *
from c
where next_entered is not null
  and next_entered <> advanced
