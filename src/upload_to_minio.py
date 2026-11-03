"""Upload the raw CSV to MinIO (S3-compatible) with boto3.

Run from the project root:  python src/upload_to_minio.py
Needs MinIO running and a .env file (see .env.example).
"""
import os
from datetime import date
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

BUCKET = os.environ["MINIO_BUCKET"]

# endpoint_url is the ONLY difference from talking to real AWS S3.
s3 = boto3.client(
    "s3",
    endpoint_url=os.environ["MINIO_ENDPOINT"],
    aws_access_key_id=os.environ["MINIO_ACCESS_KEY"],
    aws_secret_access_key=os.environ["MINIO_SECRET_KEY"],
    region_name="us-east-1",
)


def ensure_bucket():
    try:
        s3.head_bucket(Bucket=BUCKET)
    except ClientError:
        s3.create_bucket(Bucket=BUCKET)
        print(f"Created bucket {BUCKET}")


def main():
    local_file = ROOT / "data" / "raw_transactions.csv"
    key = f"raw/transactions/ingest_date={date.today():%Y-%m-%d}/raw_transactions.csv"

    ensure_bucket()
    s3.upload_file(str(local_file), BUCKET, key)
    print(f"Uploaded {local_file.name} -> s3://{BUCKET}/{key}")

    # verify: the object in S3 must be the same size as the local file
    s3_size = s3.head_object(Bucket=BUCKET, Key=key)["ContentLength"]
    local_size = local_file.stat().st_size
    print(f"Local size: {local_size} bytes | S3 size: {s3_size} bytes")
    assert s3_size == local_size, "Size mismatch, upload is corrupt"

    print("Objects under raw/:")
    for obj in s3.list_objects_v2(Bucket=BUCKET, Prefix="raw/").get("Contents", []):
        print(f"  {obj['Key']}  ({obj['Size']} bytes)")


if __name__ == "__main__":
    main()