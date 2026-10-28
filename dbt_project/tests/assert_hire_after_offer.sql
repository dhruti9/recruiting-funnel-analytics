-- A candidate cannot be hired before their offer was extended.
select a.application_id, o.extended_at, a.hired_at
from {{ ref('fct_applications') }} a
join {{ ref('fct_offers') }} o using (application_id)
where a.is_hired
  and not a.has_out_of_order_stages
  and a.hired_at < o.extended_at
