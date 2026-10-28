-- Entity resolution: the same person can exist as several ATS profiles.
-- Profiles sharing a normalized email are collapsed onto the earliest profile.
with candidates as (
    select * from {{ ref('stg_ats__candidates') }}
)

select
    candidate_id,
    first_value(candidate_id) over (
        partition by email_normalized order by created_at, candidate_id
    )                                                  as canonical_candidate_id,
    count(*) over (partition by email_normalized)      as profiles_for_person,
    first_name,
    last_name,
    email_normalized,
    phone_digits,
    city,
    state,
    created_at
from candidates
