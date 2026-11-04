with txns as (
    select
        txn_id, customer_id, card_hash, txn_timestamp, amount_inr, city
    from {{ ref('fct_transactions') }}
    where status = 'SUCCESS' and not is_refund
),

high_amount as (
    select
        txn_id,
        customer_id,
        'high_amount' as rule_name,
        concat('amount_inr ', cast(amount_inr as string), ' >= ',
               cast({{ var('fraud_high_amount_inr') }} as string)) as rule_detail
    from txns
    where amount_inr >= {{ var('fraud_high_amount_inr') }}
),

with_previous as (
    select
        txn_id,
        customer_id,
        txn_timestamp,
        city,
        lag(txn_id)        over (partition by card_hash order by txn_timestamp) as prev_txn_id,
        lag(city)          over (partition by card_hash order by txn_timestamp) as prev_city,
        lag(txn_timestamp) over (partition by card_hash order by txn_timestamp) as prev_timestamp
    from txns
    where card_hash is not null
),

impossible_travel as (
    select
        txn_id,
        customer_id,
        'impossible_travel' as rule_name,
        concat(
            'card used in ', prev_city, ' then ', city, ' within ',
            cast(cast(round((unix_timestamp(txn_timestamp) - unix_timestamp(prev_timestamp)) / 60) as int) as string),
            ' min (previous txn ', prev_txn_id, ')'
        ) as rule_detail
    from with_previous
    where prev_city is not null
      and city is not null
      and city <> prev_city
      and unix_timestamp(txn_timestamp) - unix_timestamp(prev_timestamp)
          <= {{ var('fraud_travel_window_minutes') }} * 60
),

flags as (
    select * from high_amount
    union all
    select * from impossible_travel
)

select
    f.txn_id,
    f.customer_id,
    f.rule_name,
    f.rule_detail,
    t.txn_timestamp,
    t.amount_inr,
    t.merchant,
    t.city
from flags f
join {{ ref('fct_transactions') }} t
    on f.txn_id = t.txn_id
order by t.txn_timestamp