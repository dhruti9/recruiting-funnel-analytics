-- Business rule: every hire must have an offer, and that offer must be accepted.
select application_id, offer_id, offer_status
from {{ ref('fct_applications') }}
where is_hired
  and (offer_id is null or offer_status <> 'accepted')
