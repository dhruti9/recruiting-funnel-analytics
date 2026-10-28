-- One row per detected data-quality issue instance, tagged with the upstream
-- system that produced it. Feeds the upstream data-gap report.
with apps as (
    select * from {{ ref('fct_applications') }}
),

issues as (
    select 'missing_reject_reason' as issue_type, application_id as record_id, requisition_id
    from apps where is_missing_reject_reason

    union all
    select 'missing_source', application_id, requisition_id
    from apps where is_missing_source

    union all
    select 'out_of_order_stage', application_id, requisition_id
    from apps where has_out_of_order_stages

    union all
    select 'null_hire_date', application_id, requisition_id
    from apps where is_hire_date_recovered

    union all
    select 'offer_without_interviews', application_id, requisition_id
    from apps where is_offer_without_interviews

    union all
    select 'hire_without_accepted_offer', o.offer_id, a.requisition_id
    from {{ ref('int_offers__resolved') }} o
    join apps a using (application_id)
    where o.is_status_inferred

    union all
    select 'duplicate_candidate', candidate_id, null
    from {{ ref('int_candidates__resolved') }}
    where candidate_id <> canonical_candidate_id

    union all
    select 'duplicate_stage_transition', t.transition_id, a.requisition_id
    from {{ ref('stg_ats__stage_transitions') }} t
    join apps a using (application_id)
    where t.is_duplicate_event

    union all
    select 'filled_req_missing_date', requisition_id, requisition_id
    from {{ ref('int_requisitions__fill') }}
    where is_filled_date_recovered
)

select
    md5(i.issue_type || '|' || i.record_id)            as issue_id,
    i.issue_type,
    c.source_system,
    c.source_table,
    c.severity,
    i.record_id,
    i.requisition_id,
    r.recruiter_id                                     as responsible_recruiter_id,
    {{ as_of() }}                                      as detected_on
from issues i
join {{ ref('dq_issue_catalog') }} c using (issue_type)
left join {{ ref('stg_hris__requisitions') }} r using (requisition_id)
