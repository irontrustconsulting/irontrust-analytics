import sys
import site

# --- DEBUG: print Python interpreter info before anything else ---
print("PYTHON EXECUTABLE:", sys.executable)
print("PYTHON VERSION:", sys.version)
print("SITE-PACKAGES PATHS:", site.getsitepackages())
# -------------------------------------------------------------------

import os
import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from analytics_core.utils import create_spark_session
from analytics_core.feature_engineering import add_event_date


def _probe_versions(spark: SparkSession):
    """Print PySpark (Python) and JVM Spark versions and warn/fail on mismatch."""
    import pyspark  # from your venv site-packages

    py_ver = getattr(pyspark, "__version__", "unknown")
    jvm_ver = spark.version  # engine version on the cluster (JVM)

    print(f"[PROBE] PySpark (python): {py_ver}")
    print(f"[PROBE] Spark (JVM)    : {jvm_ver}")

    # Optional: extra context (best-effort; may vary by distro)
    try:
        jvm = spark.sparkContext._jvm
        hadoop_ver = jvm.org.apache.hadoop.util.VersionInfo.getVersion()
        print(f"[PROBE] Hadoop         : {hadoop_ver}")
        s3a_cls = jvm.org.apache.hadoop.fs.s3a.S3AFileSystem
        print(f"[PROBE] S3A class      : {s3a_cls.getName()}")
        print(f"[PROBE] Java runtime   : {jvm.java.lang.System.getProperty('java.runtime.version')}")
    except Exception as e:
        print(f"[PROBE] (optional details unavailable): {e}")

    # Compare major.minor to detect drift (e.g., 4.1 vs 3.5)
    def major_minor(v: str):
        parts = v.split(".")
        mm = []
        for p in parts[:2]:
            try:
                mm.append(int(p))
            except Exception:
                pass
        return tuple(mm) if mm else None

    mm_py = major_minor(py_ver)
    mm_jvm = major_minor(jvm_ver)

    mismatch = bool(mm_py and mm_jvm and mm_py != mm_jvm)
    if mismatch:
        print(f"[PROBE] WARNING: PySpark {py_ver} vs JVM Spark {jvm_ver} mismatch detected.")

    # Optional hard‑fail if you set an env flag
    if os.getenv("FAIL_ON_SPARK_MISMATCH", "0") == "1" and mismatch:
        raise RuntimeError(f"Spark version mismatch: PySpark {py_ver} vs JVM {jvm_ver}")


def main():
    # Arguments: tenant_id and bronze/silver paths
    parser = argparse.ArgumentParser()
    parser.add_argument("tenant_id")
    parser.add_argument("bronze_path")
    parser.add_argument("silver_path")
    args = parser.parse_args()
    tenant_id = args.tenant_id
    bronze_path = args.bronze_path
    silver_path = args.silver_path

    # Initialize Spark (your util)
    spark = create_spark_session(
        app_name=f"dns_flatten_{tenant_id}",
        packages=True,
    )

    # --- PROBE: print versions at runtime (venv vs cluster engine)
    _probe_versions(spark)
    # -------------------------------------------------------------

    # Read bronze JSON
    df = spark.read.json(bronze_path)
    df = add_event_date(df)

    questions = flatten_dns_questions(df).withColumn("tenant", F.lit(tenant_id))
    answers = flatten_dns_answers(df).withColumn("tenant", F.lit(tenant_id))

    # Write to silver with partitioning by tenant
    silver_base = f"s3a://{silver_path}/dns"

    questions.write.mode("append").partitionBy("tenant","event_date").parquet(f"{silver_base}/questions/")
    answers.write.mode("append").partitionBy("tenant","event_date").parquet(f"{silver_base}/answers/")

    spark.stop()


def flatten_dns_questions(df):
    return (
        df
        .withColumn("question", F.explode_outer("questions"))
        .select(
            F.col("event_ts"),
            F.col("event_date"),
            F.col("src_ip"),
            F.col("dst_ip"),
            F.col("id"),
            F.col("qr"),
            F.col("opcode"),
            F.col("rcode"),
            F.col("question.qname").alias("qname"),
            F.col("question.qtype").alias("qtype"),
            F.col("question.qclass").alias("qclass")
        )
    )


def flatten_dns_answers(df):
    return (
        df
        .withColumn("answer", F.explode_outer("answers"))
        .select(
            F.col("event_ts"),
            F.col("event_date"),
            F.col("src_ip"),
            F.col("dst_ip"),
            F.col("id"),
            F.col("qr"),
            F.col("opcode"),
            F.col("rcode"),
            F.col("answer.rrname").alias("rrname"),
            F.col("answer.rdata").alias("rdata"),
            F.col("answer.rtype").alias("rtype"),
            F.col("answer.rclass").alias("eclass"),
            F.col("answer.ttl").alias("ttl")
        )
    )


if __name__ == '__main__':
    main()