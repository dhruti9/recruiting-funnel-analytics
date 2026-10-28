-- Upstream data-gap report: what is broken, in which system, how badly, who owns
-- the fix and what the fix is. Designed to be sent to system admins as-is.
with catalog as (
    select * from {{ ref('dq_issue_catalog') }}
),

owners as (
    select * from {{ ref('data_system_owners') }}
),

issue_counts as (
    select issue_type, count(*) as records_affected
    from {{ ref('dq_issue_log') }}
    group by 1
),

apps as (select * from {{ ref('fct_applications') }}),

-- the population each check is evaluated against
denominators as (
    select 'missing_reject_reason' as issue_type, count(*) filter (where application_status = 'rejected') as records_checked from apps
    union all select 'missing_source', count(*) from apps
    union all select 'out_of_order_stage', count(*) from apps
    union all select 'null_hire_date', count(*) filter (where is_hired) from apps
    union all select 'offer_without_interviews', count(*) filter (where offer_id is not null) from apps
    union all select 'hire_without_accepted_offer', count(*) filter (where is_hired and offer_id is not null) from apps
    union all select 'duplicate_candidate', count(*) from {{ ref('stg_ats__candidates') }}
    union all select 'duplicate_stage_transition', count(*) from {{ ref('stg_ats__stage_transitions') }}
    union all select 'filled_req_missing_date', count(*) filter (where requisition_status = 'filled') from {{ ref('stg_hris__requisitions') }}
)

select
    c.source_system,
    o.owning_team,
    o.system_admin,
    o.admin_email,
    c.source_table,
    c.issue_type,
    c.severity,
    c.description,
    c.recommended_fix,
    d.records_checked,
    coalesce(i.records_affected, 0)                    as records_affected,
    round(100.0 * coalesce(i.records_affected, 0) / nullif(d.records_checked, 0), 2) as pct_affected,
    o.remediation_sla_days,
    {{ as_of() }} + to_days(o.remediation_sla_days)    as fix_due_by,
    row_number() over (
        order by case c.severity when 'high' then 1 when 'medium' then 2 else 3 end,
                 coalesce(i.records_affected, 0)::double / nullif(d.records_checked, 0) desc
    )                                                  as priority_rank
from catalog c
join owners o using (source_system)
join denominators d using (issue_type)
left join issue_counts i using (issue_type)
