-- returns bad rows; the test passes when this returns zero rows
select
    txn_id,
    txn_date,
    _ingested_at
from {{ ref('stg_transactions') }}
where txn_date > date_add(cast(_ingested_at as date), 7)