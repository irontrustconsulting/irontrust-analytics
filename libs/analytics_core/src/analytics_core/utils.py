from pyspark.sql import SparkSession
import os
import glob

import logging

def create_spark_session(app_name="__name__", aws_profile=None, packages=None, jars=None):
    try:
        spark.stop()
    except Exception:
        pass

    builder = (
        SparkSession.builder
        .appName(app_name)
        .master("local[*]")
        .config("spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version", "2")
        .config("spark.hadoop.fs.s3a.fast.upload", "true")
        .config("spark.sql.parquet.compression.codec", "snappy")
    )

    if aws_profile:
        os.environ["AWS_PROFILE"] = aws_profile
        builder = builder \
            .config("spark.hadoop.fs.s3a.aws.credentials.provider", 
                    "com.amazonaws.auth.profile.ProfileCredentialsProvider") \
            .config("spark.hadoop.fs.s3a.profiledns ", aws_profile)

    if packages:
        builder = builder.config("spark.jars.packages","org.apache.hadoop:hadoop-aws:3.4.1")

    if jars:
        jars = glob.glob(jars)
        if not jars:
            raise ValueError(f"No JARs found in path pattern: {jars}")
        builder = builder.config("spark.jars", ",".join(jars))

    # Add any extra configs
    '''
    for key, value in extra_configs.items():
        builder = builder.config(key, value)
    '''

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("FATAL")
    return spark


def get_logger(name: str = "dns_analytics", level: int = logging.INFO) -> logging.Logger:

    logger = logging.getLogger(name)

    if not logger.handlers:  # Avoid duplicate handlers in notebooks
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(level)
    logger.propagate = False
    return logger