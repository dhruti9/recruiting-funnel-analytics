-- Days from requisition open to the hire that filled it, by month filled and department.
with reqs as (
    select * from {{ ref('dim_requisition') }}
    where requisition_status = 'filled' and filled_at is not null
)

select
    cast(date_trunc('month', filled_at) as date)       as filled_month,
    coalesce(department_name, 'All departments')       as department_name,
    count(*)                                           as requisitions_filled,
    round(avg(time_to_fill_days), 1)                   as avg_time_to_fill_days,
    median(time_to_fill_days)                          as median_time_to_fill_days,
    quantile_cont(time_to_fill_days, 0.75)             as p75_time_to_fill_days
from reqs
group by grouping sets ((1, department_name), (1))
