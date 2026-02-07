import sys
import math
from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from pyspark.sql.types import DoubleType, StringType, StructType, StructField
from pyspark.sql.window import Window

from analytics_core.utils import create_spark_session
from analytics_core.feature_engineering import (
     add_entropy, add_qname_length, add_domain_parts, root_domain_cardinality, add_time_features,


)
from analytics_core.aggregations import add_entropy_bin
from analytics_core.histograms import build_entropy_histograms

# ----------------------------
# Main
# ----------------------------
def main():
    # Spark session
    

    # Arguments
    tenant_id = sys.argv[1]
    silver_bucket = sys.argv[2]
    gold_bucket = sys.argv[3]  

    questions_path = f"s3a://{silver_bucket}/dns/questions/"
    answers_path = f"s3a://{silver_bucket}/dns/answers/"
    gold_base = f"s3a://{gold_bucket}/dns"

    HIGH_ENTROPY_THRESHOLD = 3.5
    HIGH_ENTROPY_ALERT = 0.10   # 10%
    NXDOMAIN_ALERT     = 0.15   # 15% (example)

    spark = create_spark_session("dns_enrichment_stage1")
    df_q = spark.read.parquet(questions_path)
    df_tenant_q = df_q.filter(
        (F.col("tenant") == tenant_id)
        #(F.col("event_date") == event_date)
    )
    df_tenant_q.filter(F.col("qname").isNotNull()).show(5,False)

    # ----------------------------
    # Enrich Questions
    # ----------------------------

    df_tenant_q = add_qname_length(df_tenant_q)
    df_tenant_q = add_domain_parts(df_tenant_q)
    df_tenant_q = root_domain_cardinality(df_tenant_q)
    df_tenant_q = add_entropy(df_tenant_q)
    df_tenant_q = add_time_features(df_tenant_q)

    df_tenant_q = add_entropy_bin(df_tenant_q)
    qname_entropy_hist, subdomain_entropy_hist = build_entropy_histograms(df_tenant_q)
    
    # Build the base aggregates

    agg_base = (
    df_tenant_q.groupBy("tenant", "event_date")
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
         F.max("subdomain_label_count").alias("max_subdomain_count")
         )
     )
    
    q_flagged = df_tenant_q.withColumn(
        "is_high_entropy",
        F.col("qname_entropy") >= F.lit(HIGH_ENTROPY_THRESHOLD)
    )

    entropy_kpis = (
        q_flagged
        .groupBy("tenant", "event_date")
        .agg(
            F.sum(F.col("is_high_entropy").cast("int")).alias("high_entropy_query_count"),
            (F.sum(F.col("is_high_entropy").cast("int")) / F.count("*"))
                .alias("high_entropy_query_ratio")
        )
    )

    entropy_kpis_v1 = (
        df_tenant_q.groupBy("tenant", "event_date")
        .agg(
            F.sum(F.col("is_apex_v1").cast("int")).alias("apex_count"),
            F.sum(F.col("has_invalid_chars_v1").cast("int")).alias("invalid_char_count"),
            F.count("*").alias("total_count")
        )
        .withColumn("apex_pct_v1", F.round(100.0 * F.col("apex_count") / F.col("total_count"), 2))
        .withColumn("invalid_char_pct_v1", F.round(100.0 * F.col("invalid_char_count") / F.col("total_count"), 2))
        .select("tenant", "event_date", "apex_pct_v1", "invalid_char_pct_v1")
    )

    max_entropy_qname = (
    df_tenant_q
    .withColumn(
        "rank",
        F.row_number().over(
            Window.partitionBy("tenant", "event_date")
                  .orderBy(F.desc("qname_entropy"))
        )
    )
    .filter("rank = 1")
    .select(
        "tenant",
        "event_date",
        F.col("qname").alias("max_entropy_qname")
        )
    )

    qname_counts = (
    df_tenant_q.groupBy("tenant", "event_date", "qname")
     .agg(F.count("*").alias("query_count"))
     )

    top_qnames = (
        df_tenant_q.groupBy("tenant", "event_date", "qname")
        .agg(F.count("*").alias("count"))
        .withColumn(
            "rank",
            F.row_number().over(
                Window.partitionBy("tenant", "event_date").orderBy(F.desc("count"))
            )
        )
        .filter(F.col("rank") <= 10)
        .groupBy("tenant", "event_date")
        .agg(
            F.collect_list(
                F.struct(
                    F.col("rank"),
                    F.col("qname"),
                    F.col("count").alias("query_count")
                )
            ).alias("top_qnames")
        )
        # ✅ sort by rank client‑safe, then drop rank
        .withColumn(
            "top_qnames",
            F.expr("""
            transform(
                array_sort(top_qnames),
                x -> struct(x.qname as qname, x.query_count as query_count)
            )
            """)
        )
    )

    high_entropy_topN = (
    q_flagged
    .filter("is_high_entropy")
    .groupBy("tenant", "event_date", "qname")
    .agg(
        F.count("*").alias("query_count"),
        F.max("qname_entropy").alias("entropy")
    )
    .withColumn(
        "rank",
        F.row_number().over(
            Window.partitionBy("tenant", "event_date")
                .orderBy(F.desc("entropy"))
        )
    )
    .filter("rank <= 10")
    .groupBy("tenant", "event_date")
    .agg(
        F.collect_list(
            F.struct("qname", "entropy", "query_count")
        ).alias("high_entropy_qnames_topN")
        )
    )

    rcode_breakdown = (
    df_tenant_q.groupBy("tenant", "event_date", "rcode")
     .agg(F.count("*").alias("count"))
     .groupBy("tenant", "event_date")
     .agg(
         F.collect_list(
             F.struct(
                 F.col("rcode").cast("int").alias("rcode"),
                 F.col("count")
             )
         ).alias("rcode_breakdown"))
         )

    qtype_breakdown = (
        df_tenant_q.groupBy("tenant", "event_date", "qtype")
        .agg(F.count("*").alias("count"))
        .groupBy("tenant", "event_date")
        .agg(
            F.collect_list(
                F.struct(
                    F.col("qtype").cast("int").alias("qtype"),
                    F.col("count")
                )
            ).alias("qtype_breakdown")
        )
    )
 
    nxd = (
         df_tenant_q.groupBy("tenant", "event_date")
        .agg(F.sum((F.col("rcode") == 3).cast("int")).alias("nxdomain_count"))
     ).join(
         agg_base.select("tenant","event_date","total_queries"),
         ["tenant","event_date"],
         "left"
    ).withColumn(
        "nxdomain_ratio",
        (F.col("nxdomain_count") / F.col("total_queries")).cast("double")
    ).drop("total_queries")

    qtype_breakdown = (
        df_tenant_q.groupBy("tenant", "event_date", "qtype")
        .agg(F.count("*").alias("count"))
        .groupBy("tenant", "event_date")
        .agg(
            F.collect_list(
                F.struct(
                    F.col("qtype").cast("int").alias("qtype"),
                    F.col("count")
                    )
            ).alias("qtype_breakdown")
        )
    )

    top_root_domains = (
    df_tenant_q.groupBy("tenant", "event_date", "root_domain")
     .agg(F.count("*").alias("query_count"))
     .withColumn(
         "rank",
         F.row_number().over(
             Window.partitionBy("tenant", "event_date")
                   .orderBy(F.desc("query_count"))
         )
     )
     .filter(F.col("rank") <= 10)
     .groupBy("tenant", "event_date")
     .agg(
         F.collect_list(
             F.struct(
                 F.col("root_domain"),
                 F.col("query_count"),
                 F.col("rank")
             )
         ).alias("top_root_domains")
     )
    )

    agg_gold = (
        agg_base
        .join(top_qnames, ["tenant", "event_date"], "left")
        .join(rcode_breakdown, ["tenant", "event_date"], "left")
        .join(qtype_breakdown, ["tenant", "event_date"], "left")
        .join(qname_entropy_hist, ["tenant", "event_date"], "left")
        .join(subdomain_entropy_hist, ["tenant", "event_date"], "left")
        .join(top_root_domains, ["tenant", "event_date"], "left")
        .join(entropy_kpis, ["tenant", "event_date"], "left")
        .join(max_entropy_qname, ["tenant", "event_date"], "left")
        .join(high_entropy_topN, ["tenant", "event_date"], "left")
        .join(nxd, ["tenant", "event_date"], "left")
        .withColumn("alert_high_entropy", F.col("high_entropy_query_ratio") >= F.lit(HIGH_ENTROPY_ALERT))
        .withColumn("alert_nxdomain", F.col("nxdomain_ratio") >= F.lit(NXDOMAIN_ALERT))
        .withColumn("tenant", F.col("tenant")).withColumn("event_date", F.col("event_date"))
    )

    gold_base_path = "s3a://irontrust-analytics-gold/dns/daily_aggregates/"
    agg_gold.write.mode("overwrite").partitionBy("tenant", "event_date").parquet(gold_base_path)

    '''
    # ----------------------------
    # Enrich Answers
    # ----------------------------
    df_a = spark.read.parquet(answers_path)
    df_a = df_a.withColumn("tenant", lit(tenant_id))
    df_a = df_a.withColumn("rrname", lower(col("rrname")))
    df_a = df_a.withColumn("answer_length", length(col("rrname")))
    df_a = df_a.withColumn("label_count", size(split(col("rrname"), "\\.")))
    df_a = df_a.withColumn("entropy", entropy_udf(col("rrname")))
    df_a = df_a.withColumn("domain_parts", domain_udf(col("rrname")))
    df_a = df_a.withColumn("ttl_bucket", ttl_bucket_udf(col("ttl")))

    df_a = df_a.select(
        "*",
        col("domain_parts.tld").alias("tld"),
        col("domain_parts.sld").alias("sld"),
        col("domain_parts.registered_domain").alias("registered_domain"),
        col("domain_parts.subdomain").alias("subdomain")
    )

    df_a.write.mode("append").partitionBy("tenant").parquet(f"{gold_base}/answers/")
    '''

    spark.stop()

if __name__ == '__main__':
    main()
