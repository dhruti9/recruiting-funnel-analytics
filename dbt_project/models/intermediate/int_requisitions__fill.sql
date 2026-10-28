-- Requisition fill status. When HRIS is missing filled_at, use the date of the
-- hire that consumed the last headcount.
with reqs as (
    select * from {{ ref('stg_hris__requisitions') }}
),

hires as (
    select
        requisition_id,
        count(*)                                       as hires,
        min(hired_at)                                  as first_hire_at,
        max(hired_at)                                  as last_hire_at
    from {{ ref('int_applications__journey') }}
    where application_status = 'hired'
    group by 1
)

select
    r.*,
    coalesce(h.hires, 0)                               as hires,
    h.first_hire_at,
    case
        when r.requisition_status = 'filled'
            then coalesce(r.filled_at_reported, h.last_hire_at)
    end                                                as filled_at,
    r.requisition_status = 'filled'
        and r.filled_at_reported is null               as is_filled_date_recovered
from reqs r
left join hires h using (requisition_id)
