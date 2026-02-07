import io
import boto3
import pyarrow.parquet as pq


s3 = boto3.client("s3")


def read_single_parquet_row(bucket: str, prefix: str) -> dict:
    """
    Reads a single-row Spark parquet output (one partition/day/tenant)
    and returns a Python-native dict.
    """

    # 1) List parquet files under the prefix
    resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

    if "Contents" not in resp:
        raise FileNotFoundError(f"No objects found under {prefix}")

    parquet_keys = [
        obj["Key"]
        for obj in resp["Contents"]
        if obj["Key"].endswith(".parquet")
    ]

    if not parquet_keys:
        raise FileNotFoundError(f"No parquet files under {prefix}")

    # 2) Read the first parquet file (Spark gold = 1 row)
    key = parquet_keys[0]

    obj = s3.get_object(Bucket=bucket, Key=key)
    table = pq.read_table(io.BytesIO(obj["Body"].read()))

    # 3) Convert PyArrow → pure Python (CRITICAL)
    record = {
        col: table.column(col)[0].as_py()
        for col in table.schema.names
    }

    return record
