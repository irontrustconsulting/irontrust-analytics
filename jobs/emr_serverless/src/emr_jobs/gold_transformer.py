import sys
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.window import Window

from analytics_core.utils import create_spark_session
from analytics_core.feature_engineering import (
    add_entropy, add_qname_length, add_domain_parts, root_domain_cardinality, add_time_features
)
from analytics_core.aggregations import add_entropy_bin
from analytics_core.histograms import build_entropy_histograms

# ----------------------------
# Main
# ----------------------------
def main():
    tenant_id = sys.argv[1]
    silver_bucket = sys.argv[2]
    gold_bucket = sys.argv[3]

    HIGH_ENTROPY_THRESHOLD = 3.5
    HIGH_ENTROPY_ALERT = 0.10
    NXDOMAIN_ALERT = 0.15

    spark = create_spark_session("dns_gold_v2")

    # ----------------------------
    # Load Questions and Answers
    # ----------------------------
    questions_path = f"s3a://{silver_bucket}/dns/questions/"
    answers_path   = f"s3a://{silver_bucket}/dns/answers/"
    gold_base      = f"s3a://{gold_bucket}/dns/daily_aggregates/"

    df_q = spark.read.parquet(questions_path)
    df_q = df_q.filter(F.col("tenant") == tenant_id)
    df_q = df_q.filter(F.col("qname").isNotNull())  # Remove null qnames

    df_a = spark.read.parquet(answers_path)
    df_a = df_a.filter(F.col("tenant") == tenant_id)

    # Add has_answer flag to questions
    df_q = df_q.join(
        df_a.select("event_ts", "id").withColumn("has_answer", F.lit(1)),
        on=["event_ts", "id"],
        how="left"
    ).withColumn("has_answer", F.coalesce(F.col("has_answer"), F.lit(0)))

    # ----------------------------
    # Enrich Questions
    # ----------------------------
    df_q = add_qname_length(df_q)
    df_q = add_domain_parts(df_q)
    df_q = root_domain_cardinality(df_q)
    df_q = add_entropy(df_q)
    df_q = add_time_features(df_q)
    df_q = add_entropy_bin(df_q)

    qname_entropy_hist, subdomain_entropy_hist = build_entropy_histograms(df_q)

    # ----------------------------
    # Aggregates
    # ----------------------------
    agg_base = (
        df_q.groupBy("tenant", "event_date")
        .agg(
            F.count("*").alias("total_queries"),
            F.countDistinct("qname").alias("unique_qnames"),
            F.countDistinct("root_domain").alias("unique_root_domains"),
            F.countDistinct("subdomain").alias("unique_subdomains"),
            F.countDistinct("src_ip").alias("unique_src_ips"),
            F.avg("qname_entropy").alias("avg_qname_entropy"),
            F.max("qname_entropy").alias("max_qname_entropy"),
            F.avg("subdomain_entropy").alias("avg_subdomain_entropy"),
            F.max("subdomain_entropy").alias("max_subdomain_entropy"),
            F.avg("subdomain_label_count").alias("avg_subdomain_count"),
            F.max("subdomain_label_count").alias("max_subdomain_count"),
            F.sum("has_answer").alias("answered_queries")
        )
    )

    # High entropy KPIs
    q_flagged = df_q.withColumn(
        "is_high_entropy", F.col("qname_entropy") >= F.lit(HIGH_ENTROPY_THRESHOLD)
    )

    entropy_kpis = (
        q_flagged.groupBy("tenant", "event_date")
        .agg(
            F.sum(F.col("is_high_entropy").cast("int")).alias("high_entropy_query_count"),
            (F.sum(F.col("is_high_entropy").cast("int")) / F.count("*")).alias("high_entropy_query_ratio")
        )
    )

    # Max entropy QNAME
    max_entropy_qname = (
        df_q.withColumn(
            "rank", F.row_number().over(Window.partitionBy("tenant", "event_date").orderBy(F.desc("qname_entropy")))
        )
        .filter("rank = 1")
        .select("tenant", "event_date", F.col("qname").alias("max_entropy_qname"))
    )

    # NXDOMAIN ratio based on questions (and answers later if needed)
    nxd = (
        df_q.groupBy("tenant", "event_date")
        .agg(F.sum((F.col("rcode") == 3).cast("int")).alias("nxdomain_count"))
        .join(agg_base.select("tenant", "event_date", "total_queries"), ["tenant", "event_date"])
        .withColumn("nxdomain_ratio", F.col("nxdomain_count") / F.col("total_queries"))
    )

    # Top QNAMEs
    top_qnames = (
        df_q.groupBy("tenant", "event_date", "qname")
        .agg(F.count("*").alias("count"))
        .withColumn("rank", F.row_number().over(Window.partitionBy("tenant", "event_date").orderBy(F.desc("count"))))
        .filter(F.col("rank") <= 10)
        .groupBy("tenant", "event_date")
        .agg(F.collect_list(F.struct("qname", "count")).alias("top_qnames"))
    )

    # ----------------------------
    # Assemble Gold Table
    # ----------------------------
    agg_gold = (
        agg_base
        .join(entropy_kpis, ["tenant", "event_date"], "left")
        .join(max_entropy_qname, ["tenant", "event_date"], "left")
        .join(nxd, ["tenant", "event_date"], "left")
        .join(top_qnames, ["tenant", "event_date"], "left")
        .join(qname_entropy_hist, ["tenant", "event_date"], "left")
        .join(subdomain_entropy_hist, ["tenant", "event_date"], "left")
        .withColumn("alert_high_entropy", F.col("high_entropy_query_ratio") >= F.lit(HIGH_ENTROPY_ALERT))
        .withColumn("alert_nxdomain", F.col("nxdomain_ratio") >= F.lit(NXDOMAIN_ALERT))
    )

    # Write gold table
    agg_gold.write.mode("overwrite").partitionBy("tenant", "event_date").parquet(gold_base)

    spark.stop()


if __name__ == "__main__":
    main()
