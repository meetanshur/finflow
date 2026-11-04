with txns as (
    select * from {{ ref('fct_transactions') }}
)

select
    merchant_group,
    count(*) as txn_count,
    count(distinct customer_id) as customers,
    sum(case when status = 'SUCCESS' and not is_refund then 1 else 0 end) as purchase_count,
    sum(case when status = 'SUCCESS' and not is_refund then amount_inr else 0 end) as purchases_inr,
    sum(case when is_refund then -amount_inr else 0 end) as refunds_inr,
    sum(case when status = 'SUCCESS' and not is_refund then amount_inr else 0 end)
      - sum(case when is_refund then -amount_inr else 0 end) as net_spend_inr,
    round(avg(case when status = 'SUCCESS' and not is_refund then amount_inr end), 2) as avg_ticket_inr,
    round(
        100 * sum(case when is_refund then -amount_inr else 0 end)
        / nullif(sum(case when status = 'SUCCESS' and not is_refund then amount_inr else 0 end), 0),
        2
    ) as refund_rate_pct
from txns
group by merchant_group