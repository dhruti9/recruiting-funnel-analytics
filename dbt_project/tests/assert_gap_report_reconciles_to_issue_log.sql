-- The upstream gap report must account for every row in the issue log.
select *
from (
    select
        (select count(*) from {{ ref('dq_issue_log') }})                        as issue_log_rows,
        (select sum(records_affected) from {{ ref('dq_upstream_gap_report') }}) as gap_report_total
)
where issue_log_rows <> gap_report_total
