# api/app_config.py
import boto3
import json

class AppConfig:
    """Loads Athena app configuration from S3."""
    def __init__(self, config: dict):
        self.athena_database: str = config["athena_database"]
        self.athena_table: str = config["athena_table"]
        self.athena_output_bucket: str = config["athena_output_bucket"]
        self.default_limit: int = config.get("default_limit", 50)
        self.sql_template_bucket: str = config["sql_template_bucket"]
        self.sql_template_prefix: str = config["sql_template_prefix"]

    @classmethod
    def load_from_s3(cls, bucket: str, key: str = "config/app_config.json") -> "AppConfig":
        s3 = boto3.client("s3")
        obj = s3.get_object(Bucket=bucket, Key=key)
        data = json.loads(obj["Body"].read().decode("utf-8"))
        return cls(data)
