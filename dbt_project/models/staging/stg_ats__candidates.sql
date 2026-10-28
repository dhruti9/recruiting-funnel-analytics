with source as (
    select * from {{ source('ats_extract', 'candidates') }}
)

select
    candidate_id,
    trim(first_name)                                   as first_name,
    trim(last_name)                                    as last_name,
    email                                              as email_raw,
    lower(trim(email))                                 as email_normalized,
    regexp_replace(phone, '[^0-9]', '', 'g')           as phone_digits,
    city,
    state,
    cast(created_at as timestamp)                      as created_at
from source
