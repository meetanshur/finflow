# Databricks notebook source
from datetime import datetime, timezone

EXPORT_DIR = "/Volumes/workspace/gold/exports"
run_ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

EXPORTS = {
    "clean_transactions": """
        SELECT * EXCEPT (card_hash, _silver_loaded_at)
        FROM workspace.gold.fct_transactions
        ORDER BY txn_timestamp, txn_id""",
    "rejected_transactions": """
        SELECT * FROM workspace.silver.quarantine_transactions
        ORDER BY txn_id""",
    "fraud_flag_candidates": """
        SELECT * FROM workspace.gold.mart_fraud_flag_candidates
        ORDER BY txn_timestamp""",
    "monthly_account_kpis": """
        SELECT * FROM workspace.gold.mart_monthly_account_kpis
        ORDER BY customer_id""",
}

for name, sql in EXPORTS.items():
    pdf = spark.sql(sql).toPandas()
    for fname in (f"{name}_latest.csv", f"{name}_{run_ts}.csv"):
        # utf-8-sig so Excel shows special characters correctly
        pdf.to_csv(f"{EXPORT_DIR}/{fname}", index=False, encoding="utf-8-sig")
    print(f"{name}: {len(pdf)} rows -> {name}_latest.csv and {name}_{run_ts}.csv")