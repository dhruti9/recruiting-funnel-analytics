select
    department_id,
    department_name,
    department_head,
    cost_center
from {{ source('ats_extract', 'departments') }}
