{% macro to_inr(amount_col, rate_col, decimals=2) -%}
    round({{ amount_col }} * {{ rate_col }}, {{ decimals }})
{%- endmacro %}