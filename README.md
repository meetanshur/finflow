# FinFlow

A beginner-friendly finance ELT pipeline built only with free tools.
Messy card and UPI transactions go in; clean, tested, analysis-ready marts come out.

![CI](https://github.com/meetanshur/finflow/actions/workflows/ci.yml/badge.svg)

## Architecture

```
Python generator -> S3 (moto, local) -> Databricks Volume
   -> Bronze (raw strings) -> Silver (PySpark: clean, mask, quarantine)
   -> dbt: staging -> intermediate -> Gold marts
```

Everything after the Volume runs as one Databricks Job (`bronze_load -> silver_clean -> dbt_build`).

## Tech stack

| Layer | Tool |
|---|---|
| Raw data | Python, pandas/csv, boto3 |
| Object storage | moto S3 server (local) |
| Lakehouse | Databricks Free Edition, Unity Catalog, Delta |
| Cleaning | PySpark notebooks |
| Modelling | dbt-core + dbt-databricks |
| Orchestration | Databricks Jobs |
| CI | GitHub Actions |

## What each layer does

- **Bronze** (`workspace.bronze.raw_transactions`): raw CSV as strings plus `_ingested_at` and `_source_file`. The source file and write mode are job parameters.
- **Silver** (`workspace.silver`): trims and normalises text, parses 5 date formats and accounting-style amounts, removes duplicates, masks card and account numbers, hashes emails, and sends unusable rows to `quarantine_transactions`.
- **Staging / intermediate** (dbt views): typed models, FX conversion to INR from a seed, merchant grouping.
- **Gold** (dbt tables in `workspace.gold`):
  - `fct_transactions`: incremental merge on `txn_id`, using `_ingested_at` as the watermark
  - `mart_daily_customer_spend`
  - `mart_merchant_category_summary`
  - `mart_fraud_flag_candidates`: high-amount and impossible-travel rules (thresholds are dbt vars)
  - `mart_monthly_account_kpis`: joined to the current row of the SCD2 customer snapshot

## dbt features used

Sources, `ref()`, views vs tables, seeds, a `generate_schema_name` macro, a `to_inr` macro, generic and singular tests, an incremental model, a snapshot (SCD2), and project vars.

## Project layout

```
src/            data generators and S3 upload
notebooks/      Databricks notebooks (Bronze, Silver)
finflow_core/   dbt project (models, seeds, snapshots, macros, tests)
jobs/           exported Databricks job definition
.github/        CI workflow
```

## Run it yourself

1. Create a venv and `pip install -r requirements.txt`.
2. `python src/generate_data.py`, then start `moto_server -p 9000` and run `python src/upload_to_minio.py`.
3. Upload the CSV to the Databricks Volume `workspace.bronze.raw_files`.
4. Create `finflow_core/profiles.yml` (it is gitignored) with your own Databricks host, warehouse path and token.
5. Run the Databricks Job, or locally: `cd finflow_core`, then `dbt seed`, `dbt snapshot`, `dbt run`, `dbt test`.

## Security notes

- No credentials are committed. `.env` and `profiles.yml` are gitignored.
- CI uses a dummy dbt profile and only runs `dbt parse`, so it never touches Databricks.
- All data is synthetic. Card numbers are public test numbers.
