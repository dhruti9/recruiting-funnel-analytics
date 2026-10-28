-- One row per *person* (duplicate ATS profiles merged).
with resolved as (
    select * from {{ ref('int_candidates__resolved') }}
),

apps as (
    select r.canonical_candidate_id, count(*) as applications, min(a.applied_at) as first_applied_at
    from {{ ref('stg_ats__applications') }} a
    join resolved r using (candidate_id)
    group by 1
)

select
    r.canonical_candidate_id                           as candidate_id,
    r.first_name,
    r.last_name,
    r.email_normalized                                 as email,
    r.city,
    r.state,
    r.created_at,
    r.profiles_for_person                              as ats_profile_count,
    r.profiles_for_person > 1                          as had_duplicate_profiles,
    coalesce(a.applications, 0)                        as applications,
    a.first_applied_at
from resolved r
left join apps a using (canonical_candidate_id)
where r.candidate_id = r.canonical_candidate_id
