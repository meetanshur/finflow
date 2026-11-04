with txns as (
    select * from {{ ref('fct_transactions') }}
),

customers as (
    select customer_id, segment, kyc_status, city as home_city
    from {{ ref('snap_customers') }}
    where dbt_valid_to is null
),

monthly as (
    select
        customer_id,
        date_trunc('month', txn_date) as txn_month,
        count(*) as txn_count,
        sum(case when status = 'SUCCESS' then 1 else 0 end) as successful_count,
        sum(case when status in ('FAILED','PENDING') then 1 else 0 end) as failed_or_pending_count,
        sum(case when status = 'SUCCESS' and not is_refund then amount_inr else 0 end) as purchases_inr,
        sum(case when is_refund then -amount_inr else 0 end) as refunds_inr,
        round(avg(case when status = 'SUCCESS' and not is_refund then amount_inr end), 2) as avg_ticket_inr,
        count(distinct merchant) as distinct_merchants,
        sum(case when currency <> 'INR' then 1 else 0 end) as foreign_currency_txns
    from txns
    group by customer_id, date_trunc('month', txn_date)
)

select
    m.customer_id,
    c.segment,
    c.kyc_status,
    c.home_city,
    cast(m.txn_month as date) as txn_month,
    m.txn_count,
    m.successful_count,
    m.failed_or_pending_count,
    round(100 * m.successful_count / m.txn_count, 2) as success_rate_pct,
    m.purchases_inr,
    m.refunds_inr,
    m.purchases_inr - m.refunds_inr as net_spend_inr,
    m.avg_ticket_inr,
    m.distinct_merchants,
    m.foreign_currency_txns
from monthly m
left join customers c on m.customer_id = c.customer_id