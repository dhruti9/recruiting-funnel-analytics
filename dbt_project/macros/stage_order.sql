{#- Maps an ATS stage name to its position in the funnel (NULL for terminal statuses). -#}
{% macro stage_order(col) -%}
    case {{ col }}
        when 'applied' then 1
        when 'recruiter_screen' then 2
        when 'hiring_manager_screen' then 3
        when 'onsite' then 4
        when 'offer' then 5
        when 'hired' then 6
    end
{%- endmacro %}

{% macro funnel_stages() -%}
    {{ return(['applied', 'recruiter_screen', 'hiring_manager_screen', 'onsite', 'offer', 'hired']) }}
{%- endmacro %}

{% macro as_of() -%}
    cast('{{ var("as_of_date") }}' as date)
{%- endmacro %}
