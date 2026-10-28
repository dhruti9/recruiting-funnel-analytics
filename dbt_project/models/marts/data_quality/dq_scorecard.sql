-- One health score per upstream system: average share of records passing each check.
select
    source_system,
    owning_team,
    system_admin,
    count(*)                                           as checks,
    sum(records_affected)                              as open_issues,
    round(100 - avg(pct_affected), 2)                  as quality_score,
    case
        when 100 - avg(pct_affected) >= 99 then 'healthy'
        when 100 - avg(pct_affected) >= 95 then 'needs attention'
        else 'critical'
    end                                                as health_status,
    count(*) filter (where severity = 'high' and records_affected > 0) as open_high_severity_checks
from {{ ref('dq_upstream_gap_report') }}
group by 1, 2, 3
