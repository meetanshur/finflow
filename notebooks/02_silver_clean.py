# Databricks notebook source
from pyspark.sql import functions as F
from pyspark.sql.window import Window

BRONZE = "workspace.bronze.raw_transactions"
SILVER = "workspace.silver.transactions"
QUARANTINE = "workspace.silver.quarantine_transactions"

# DD/MM/YYYY convention; first format that matches wins
DATE_FORMATS = ["dd/MM/yyyy HH:mm", "dd/MM/yyyy", "dd-MM-yyyy", "yyyy-MM-dd", "d MMM yyyy"]

MERCHANT_MAP = {
    "amazn": "Amazon", "amazon": "Amazon",
    "starbuks": "Starbucks", "starbucks": "Starbucks",
    "swiggy": "Swiggy", "zomato": "Zomato", "uber": "Uber",
    "myntra": "Myntra", "flipkart": "Flipkart", "netflix": "Netflix",
    "spotify": "Spotify", "croma": "Croma", "tanishq": "Tanishq",
    "paytm": "Paytm", "booking.com": "Booking.com",
    "apple store": "Apple Store", "reliance digital": "Reliance Digital",
}

raw = spark.table(BRONZE)
n_raw = raw.count()

# 1. trim everything; turn '', NULL, N/A, NONE into real nulls
data_cols = [c for c in raw.columns if not c.startswith("_")]

def blank_to_null(c):
    t = F.trim(F.col(c))
    return (F.when(t.isNull() | F.upper(t).isin("", "NULL", "N/A", "NONE"), F.lit(None))
             .otherwise(t).alias(c))

df = raw.select(*[blank_to_null(c) for c in data_cols], "_ingested_at", "_source_file")

# 2. deduplicate on txn_id (keep the latest ingested copy)
w = Window.partitionBy("txn_id").orderBy(F.col("_ingested_at").desc())
df = df.withColumn("_rn", F.row_number().over(w)).filter("_rn = 1").drop("_rn")
n_dedup = df.count()

# 3. parse amount and date (try_ functions return NULL instead of failing)
df = (df.withColumnRenamed("amount", "amount_raw")
        .withColumnRenamed("txn_date", "txn_date_raw"))

is_neg = F.col("amount_raw").rlike(r"^\(.*\)$") | F.col("amount_raw").contains("-")
amount_abs = F.expr("try_cast(regexp_replace(amount_raw, '[^0-9.]', '') AS DECIMAL(18,2))")
txn_ts = F.coalesce(*[F.expr(f"try_to_timestamp(txn_date_raw, '{f}')") for f in DATE_FORMATS])

df = (df
      .withColumn("amount_signed", F.when(is_neg, -amount_abs).otherwise(amount_abs))
      .withColumn("txn_ts", txn_ts)
      .withColumn("reject_reason",
                  F.when(F.col("txn_id").isNull(), "missing_txn_id")
                   .when(F.col("amount_raw").isNull(), "missing_amount")
                   .when(F.col("amount_signed").isNull(), "invalid_amount")
                   .when(F.col("txn_ts").isNull(), "invalid_date")))

bad = df.filter("reject_reason IS NOT NULL")
good = df.filter("reject_reason IS NULL")

# 4. quarantine: raw values, no PII columns
quarantine = bad.select(
    "txn_id", "customer_id", "txn_date_raw", "amount_raw", "currency",
    "merchant", "category", "channel", "status", "reject_reason",
    "_ingested_at", "_source_file")

# 5. silver: standardise, mask PII, parse JSON
map_df = spark.createDataFrame(list(MERCHANT_MAP.items()), ["merchant_key", "merchant_std"])

def digits(c):
    return F.regexp_replace(F.col(c), r"[^0-9]", "")

email_ok = F.col("email").rlike(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
meta = F.from_json("meta_json", "city STRING, device STRING")
has_card = F.length(digits("card_no")) >= 4

silver = (
    good.withColumn("merchant_key", F.lower("merchant"))
        .join(F.broadcast(map_df), "merchant_key", "left")
        .select(
            "txn_id", "customer_id",
            F.when(F.col("account_no").isNotNull(),
                   F.concat(F.lit("****"), F.substring("account_no", -4, 4))).alias("account_masked"),
            F.when(has_card, F.concat(F.lit("************"),
                   F.substring(digits("card_no"), -4, 4))).alias("card_masked"),
            F.when(has_card, F.sha2(digits("card_no"), 256)).alias("card_hash"),
            F.when(email_ok, F.sha2(F.lower("email"), 256)).alias("email_hash"),
            F.when(email_ok, F.lower(F.substring_index("email", "@", -1))).alias("email_domain"),
            "txn_ts",
            F.to_date("txn_ts").alias("txn_date"),
            F.col("amount_signed").alias("amount"),
            F.upper("currency").alias("currency"),
            F.coalesce("merchant_std", F.initcap("merchant"), F.lit("Unknown")).alias("merchant"),
            F.coalesce(F.initcap("category"), F.lit("Uncategorized")).alias("category"),
            F.upper("channel").alias("channel"),
            F.upper("status").alias("status"),
            meta.getField("city").alias("city"),
            meta.getField("device").alias("device"),
            meta.isNotNull().alias("meta_valid"),
            "_ingested_at", "_source_file",
            F.current_timestamp().alias("_silver_loaded_at"),
        )
)

# 6. write both tables
for frame, table in [(silver, SILVER), (quarantine, QUARANTINE)]:
    (frame.write.format("delta").mode("overwrite")
          .option("overwriteSchema", "true").saveAsTable(table))

n_silver = spark.table(SILVER).count()
n_quar = spark.table(QUARANTINE).count()
print(f"bronze rows:        {n_raw}")
print(f"duplicates removed: {n_raw - n_dedup}")
print(f"quarantined:        {n_quar}")
print(f"silver rows:        {n_silver}")
assert n_silver + n_quar == n_dedup, "row counts do not add up"

display(spark.table(QUARANTINE))
display(spark.table(SILVER))