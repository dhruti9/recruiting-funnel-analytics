-- Source effectiveness must cover every application and every hire (no source lost
-- in the join, including unattributed applications).
select *
from (
    select
        (select sum(applications) from {{ ref('kpi_source_effectiveness') }}) as kpi_apps,
        (select count(*) from {{ ref('fct_applications') }})                 as fact_apps,
        (select sum(hires) from {{ ref('kpi_source_effectiveness') }})        as kpi_hires,
        (select count(*) from {{ ref('fct_applications') }} where is_hired)  as fact_hires
)
where kpi_apps <> fact_apps or kpi_hires <> fact_hires
