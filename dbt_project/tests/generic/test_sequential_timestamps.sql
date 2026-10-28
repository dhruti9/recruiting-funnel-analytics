{#-
  Within each `partition_by` group, ordering rows by `order_by` (the logical
  sequence, e.g. funnel stage order) must never make `column_name` go backwards in time.
-#}
{% test sequential_timestamps(model, column_name, partition_by, order_by) %}
with ordered as (
    select
        {{ partition_by }} as grp,
        {{ order_by }} as seq,
        {{ column_name }} as ts,
        lag({{ column_name }}) over (partition by {{ partition_by }} order by {{ order_by }}) as prev_ts
    from {{ model }}
)
select * from ordered where ts < prev_ts
{% endtest %}
