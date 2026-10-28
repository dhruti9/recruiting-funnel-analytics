-- Active (undecided) applications as of the snapshot date, bucketed by days
-- since anyone last touched them.
with active as (
    select f.*, d.department_name
    from {{ ref('fct_applications') }} f
    left join {{ ref('dim_department') }} d using (department_id)
    where f.application_status = 'active'
)

select
    department_name,
    current_stage,
    {{ stage_order('current_stage') }}                 as stage_order,
    case
        when days_since_last_activity <= 7 then '0-7 days'
        when days_since_last_activity <= 14 then '8-14 days'
        when days_since_last_activity <= 30 then '15-30 days'
        when days_since_last_activity <= 60 then '31-60 days'
        else '60+ days'
    end                                                as aging_bucket,
    count(*)                                           as active_applications,
    round(avg(days_since_last_activity), 1)            as avg_days_since_last_activity,
    max(days_since_last_activity)                      as max_days_since_last_activity
from active
group by all
