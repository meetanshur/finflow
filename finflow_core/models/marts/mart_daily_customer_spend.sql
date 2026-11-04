with txns as (
    select * from {{ ref('fct_transactions') }}
)

select
    customer_id,
    txn_date,
    count(*) as txn_count,
    sum(case when status = 'SUCCESS' and not is_refund then 1 else 0 end) as purchase_count,
    sum(case when status = 'SUCCESS' and not is_refund then amount_inr else 0 end) as purchases_inr,
    sum(case when is_refund then -amount_inr else 0 end) as refunds_inr,
    sum(case when status = 'SUCCESS' and not is_refund then amount_inr else 0 end)
      - sum(case when is_refund then -amount_inr else 0 end) as net_spend_inr,
    sum(case when status in ('FAILED', 'PENDING') then 1 else 0 end) as failed_or_pending_count
from txns
group by customer_id, txn_date