-- Volume, quality, speed and cost of every candidate source.
-- Cost model: per-application spend + flat per-hire fees + agency % of base salary.
with apps as (
    select * from {{ ref('fct_applications') }}
),

by_source as (
    select
        s.source_id,
        s.source_name,
        s.source_type,
        count(*)                                       as applications,
        count(*) filter (where a.reached_recruiter_screen) as screens,
        count(*) filter (where a.reached_onsite)       as onsites,
        count(*) filter (where a.reached_offer)        as offers,
        count(*) filter (where a.is_hired)             as hires,
        median(a.time_to_hire_days) filter (where a.is_hired) as median_time_to_hire_days,
        count(*) * s.cost_per_application_usd
          + count(*) filter (where a.is_hired) * s.fee_per_hire_usd
          + coalesce(sum(a.base_salary_usd) filter (where a.is_hired), 0) * s.fee_pct_of_base_salary
                                                       as total_cost_usd
    from apps a
    join {{ ref('dim_source') }} s using (source_id)
    group by s.source_id, s.source_name, s.source_type,
             s.cost_per_application_usd, s.fee_per_hire_usd, s.fee_pct_of_base_salary
),

job_board_baseline as (
    select sum(hires)::double / sum(applications) as job_board_hire_rate
    from by_source where source_type = 'job_board'
)

select
    b.*,
    round(b.hires::double / nullif(b.applications, 0), 4) as hire_rate,
    round(1000.0 * b.hires / nullif(b.applications, 0), 1) as hires_per_1k_applications,
    round(b.onsites::double / nullif(b.screens, 0), 4) as screen_to_onsite_rate,
    round(b.total_cost_usd / nullif(b.hires, 0), 0)    as cost_per_hire_usd,
    round((b.hires::double / nullif(b.applications, 0)) / j.job_board_hire_rate, 2)
                                                       as hire_rate_vs_job_boards
from by_source b
cross join job_board_baseline j
