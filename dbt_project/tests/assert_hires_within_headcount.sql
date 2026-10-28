-- A requisition can never have more hires than approved headcount.
select requisition_id, headcount, hires
from {{ ref('dim_requisition') }}
where hires > headcount
