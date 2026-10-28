{% docs __overview__ %}
# Recruiting Funnel Analytics

An end-to-end, tested analytics pipeline over applicant-tracking-system (ATS) data.

**Layers**

| Layer | Purpose |
|---|---|
| `staging` | One model per raw table: renamed, typed, no rows removed. Upstream problems are *flagged*, not hidden. |
| `intermediate` | Business logic: candidate de-duplication, stage sequencing and durations, recovered hire / fill dates, corrected offer status. |
| `marts.core` | Star schema: `fct_applications`, `fct_stage_transitions`, `fct_offers` and dimensions. |
| `marts.kpis` | One model per recruiting KPI, ready for the dashboard. |
| `marts.data_quality` | Issue log, upstream data-gap report and per-system scorecard. |

**Test philosophy.** Tests at `warn` severity describe known problems in source systems; they
never block a merge and are routed to owners via `dq_upstream_gap_report`. Tests at
`error` severity are guarantees this project makes about its own outputs and block CI.
{% enddocs %}
