from pyspark.sql import functions as F

SRC = "/Volumes/workspace/bronze/raw_files/raw_transactions.csv"
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

(df.write.format("delta")
   .mode("overwrite")
   .option("overwriteSchema", "true")
   .saveAsTable(TARGET))

print("rows:", spark.table(TARGET).count())
display(spark.table(TARGET))