{{ config(
    materialized='incremental',
    unique_key='txn_id',
    incremental_strategy='merge',
    schema='gold'
) }}

select
    txn_id,
    customer_id,
    card_hash,
    txn_timestamp,
    txn_date,
    amount,
    currency,
    rate_to_inr,
    amount_inr,
    is_refund,
    merchant,
    merchant_group,
    category,
    channel,
    status,
    city,
    device,
    meta_valid,
    _silver_loaded_at
from {{ ref('int_transactions_enriched') }}

{% if is_incremental() %}
where _silver_loaded_at > (select max(_silver_loaded_at) from {{ this }})
{% endif %}