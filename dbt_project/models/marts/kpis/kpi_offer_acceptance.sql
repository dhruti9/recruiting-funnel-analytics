-- Offer acceptance rate = accepted / (accepted + declined). Rescinded and pending
-- offers are not candidate decisions and are excluded from the rate.
with offers as (
    select o.*, d.department_name
    from {{ ref('fct_offers') }} o
    join {{ ref('dim_department') }} d using (department_id)
)

select
    extended_quarter,
    coalesce(department_name, 'All departments')       as department_name,
    count(*)                                           as offers_extended,
    count(*) filter (where offer_status = 'accepted')  as accepted,
    count(*) filter (where offer_status = 'declined')  as declined,
    count(*) filter (where offer_status = 'rescinded') as rescinded,
    count(*) filter (where offer_status = 'pending')   as pending,
    round(
        count(*) filter (where offer_status = 'accepted')::double
        / nullif(count(*) filter (where offer_status in ('accepted', 'declined')), 0), 4
    )                                                  as offer_acceptance_rate
from offers
group by grouping sets ((extended_quarter, department_name), (extended_quarter))
