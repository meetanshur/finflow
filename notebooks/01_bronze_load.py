from pyspark.sql import functions as F

SOURCE_FILE = "raw_transactions_batch2.csv"   # batch 1 was: raw_transactions.csv
WRITE_MODE = "append"                          # batch 1 was: overwrite

SRC = f"/Volumes/workspace/bronze/raw_files/{SOURCE_FILE}"
TARGET = "workspace.bronze.raw_transactions"

df = (
    spark.read
    .option("header", True)
    .option("inferSchema", False)   # Bronze keeps everything as strings
    .option("escape", '"')          # CSV uses "" for quotes inside the JSON column
    .csv(SRC)
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn("_source_file", F.col("_metadata.file_path"))
)

writer = df.write.format("delta").mode(WRITE_MODE)
if WRITE_MODE == "overwrite":
    writer = writer.option("overwriteSchema", "true")
writer.saveAsTable(TARGET)

print("file loaded:", SOURCE_FILE, "| mode:", WRITE_MODE)
print("rows in bronze now:", spark.table(TARGET).count())
display(spark.table(TARGET).groupBy("_source_file").count())