select
    o.offer_id,
    o.application_id,
    a.candidate_id,
    a.requisition_id,
    a.department_id,
    a.source_id,
    o.extended_at,
    cast(date_trunc('quarter', o.extended_at) as date) as extended_quarter,
    o.responded_at,
    o.offer_status,
    o.offer_status_reported,
    o.is_status_inferred,
    date_diff('day', o.extended_at, o.responded_at)    as days_to_respond,
    o.base_salary_usd,
    o.sign_on_bonus_usd
from {{ ref('int_offers__resolved') }} o
join {{ ref('fct_applications') }} a using (application_id)
