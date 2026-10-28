{#- Model-level test: every row must satisfy `expression`. -#}
{% test expression_is_true(model, expression) %}
select *
from {{ model }}
where not ({{ expression }})
{% endtest %}
