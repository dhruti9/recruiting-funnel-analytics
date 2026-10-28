-- Raw stage-change events. Exact duplicates from re-syncs are flagged here and
-- removed downstream so the issue stays visible to the data-gap report.
with source as (
    select * from {{ source('ats_extract', 'stage_transitions') }}
),

renamed as (
    select
        transition_id,
        application_id,
        nullif(lower(trim(from_stage)), '')            as from_stage,
        lower(trim(to_stage))                          as to_stage,
        cast(transitioned_at as timestamp)             as transitioned_at
    from source
)

select
    *,
    {{ stage_order('to_stage') }}                      as to_stage_order,
    to_stage in ('rejected', 'withdrawn', 'declined', 'hired') as is_terminal,
    row_number() over (
        partition by application_id, to_stage, transitioned_at
        order by transition_id
    ) > 1                                              as is_duplicate_event
from renamed
