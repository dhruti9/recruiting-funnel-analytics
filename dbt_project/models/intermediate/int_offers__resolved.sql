-- Offer status as reported by Offer Management, corrected with ATS evidence:
-- if the candidate was hired the offer was accepted, whatever the offer system says.
with offers as (
    select * from {{ ref('stg_offers__offers') }}
),

apps as (
    select application_id, application_status, hired_at
    from {{ ref('int_applications__journey') }}
)

select
    o.offer_id,
    o.application_id,
    o.extended_at,
    o.responded_at,
    o.offer_status                                     as offer_status_reported,
    case
        when a.application_status = 'hired' then 'accepted'
        else o.offer_status
    end                                                as offer_status,
    a.application_status = 'hired'
        and o.offer_status <> 'accepted'               as is_status_inferred,
    o.base_salary_usd,
    o.sign_on_bonus_usd
from offers o
left join apps a using (application_id)
