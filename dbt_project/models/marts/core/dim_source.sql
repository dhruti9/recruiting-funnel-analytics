-- Candidate sources plus an explicit 'Unattributed' member so applications with a
-- missing source still join (and show up in reporting instead of silently dropping).
select * from {{ ref('stg_marketing__sources') }}
union all
select 'UNKNOWN', 'Unattributed', 'unknown', 0, 0, 0
