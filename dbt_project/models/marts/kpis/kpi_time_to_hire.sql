-- Days from application to hire, by month hired and source.
with hires as (
    select f.*, s.source_name
    from {{ ref('fct_applications') }} f
    join {{ ref('dim_source') }} s using (source_id)
    where f.is_hired
)

select
    cast(date_trunc('month', hired_at) as date)        as hired_month,
    coalesce(source_name, 'All sources')               as source_name,
    count(*)                                           as hires,
    round(avg(time_to_hire_days), 1)                   as avg_time_to_hire_days,
    median(time_to_hire_days)                          as median_time_to_hire_days
from hires
group by grouping sets ((1, source_name), (1))
