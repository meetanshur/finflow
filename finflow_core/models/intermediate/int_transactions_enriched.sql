{{ config(materialized='view') }}

select
    t.txn_id,
    t.customer_id,
    t.card_hash,
    t.card_masked,
    t.txn_timestamp,
    t.txn_date,
    t.amount,
    t.currency,
    f.rate_to_inr,
    {{ to_inr('t.amount', 'f.rate_to_inr') }} as amount_inr,
    t.is_refund,
    t.merchant,
    coalesce(m.merchant_group, 'Other') as merchant_group,
    t.category,
    t.channel,
    t.status,
    t.city,
    t.device,
    t.email_domain,
    t.meta_valid,
    t._silver_loaded_at
from {{ ref('stg_transactions') }} t
left join {{ ref('fx_rates') }} f
    on t.currency = f.currency
left join {{ ref('merchant_categories') }} m
    on t.merchant = m.merchant