select
    interview_id,
    application_id,
    interview_stage,
    interview_type,
    cast(scheduled_at as timestamp)                    as scheduled_at,
    interviewer_name,
    cast(score as integer)                             as score,
    cast(feedback_submitted as boolean)                as is_feedback_submitted
from {{ source('ats_extract', 'interviews') }}
