select
    offer_id,
    application_id,
    cast(extended_at as timestamp)                     as extended_at,
    cast(responded_at as timestamp)                    as responded_at,
    lower(offer_status)                                as offer_status,
    cast(base_salary_usd as integer)                   as base_salary_usd,
    cast(sign_on_bonus_usd as integer)                 as sign_on_bonus_usd
from {{ source('ats_extract', 'offers') }}
