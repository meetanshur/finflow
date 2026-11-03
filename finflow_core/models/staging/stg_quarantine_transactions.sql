select
    txn_id,
    customer_id,
    txn_date_raw,
    amount_raw,
    currency,
    merchant,
    category,
    channel,
    status,
    reject_reason,
    _ingested_at
from {{ source('silver', 'quarantine_transactions') }}