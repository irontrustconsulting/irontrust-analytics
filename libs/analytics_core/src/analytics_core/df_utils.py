from pyspark.sql import DataFrame
from pyspark.sql.window import Window
from pyspark.sql.functions import (
    row_number,
    monotonically_increasing_id,
    col, explode, explode_outer, when, expr, lit, to_timestamp, concat_ws, sha2, sum as spark_sum,
    trim, lower, coalesce
)
from pyspark.sql.types import StringType, IntegerType, TimestampType, DataType
import math
from analytics_core.utils import get_logger
from analytics_core.feature_engineering import add_event_date
from pyspark.sql import functions as F  # <-- single import of F
import tldextract
import math
from collections import defaultdict

logger = get_logger(__name__)


def flatten_dns_questions(df: DataFrame) -> DataFrame:
    """
    Flatten dns.questions into a questions-only row set (one row per question).
    """
    cols_map = {
        "qname": F.col("question.qname"),
        "qtype": F.col("question.qtype"),
        "qclass": F.col("question.qclass")

    }
    
    return (
        df
        .withColumn("question", F.explode_outer("questions"))
        .withColumns(cols_map)
        )


def map_subdomains(df: DataFrame) -> dict:
    """
    Creates a map of root domain to list of all its subdomains from DNS queries in a PySpark DataFrame
    """
    unique_queries = df.select("qname").distinct().collect()
    subdomain_dict = {}
    for r in unique_queries:
        extracted = tldextract.extract(r.qname)
        root_domain = extracted.domain + "." + extracted.suffix
        subdomain = extracted.subdomain
        if root_domain not in subdomain_dict:
            subdomain_dict[root_domain] = [subdomain]
        elif subdomain not in subdomain_dict[root_domain]:
            subdomain_dict[root_domain].append(subdomain)
    return subdomain_dict


def deduplicate_by_hash(df: DataFrame, verbose: bool = False) -> DataFrame:
    """
    Deduplicates rows based on key columns (subset), retaining full rows.
    """
    before = df.count()
    
    df_h = (
    df
    .withColumn("qname_norm", trim(lower(col("qname"))))
    .withColumn("rrname_norm", trim(lower(col("rrname"))))
    .withColumn("rdata_norm",  trim(lower(coalesce(col("rdata"), lit("")))))
    .withColumn("name",  coalesce(col("qname_norm"), col("rrname_norm")))
    .withColumn("rrtype", coalesce(col("qtype"), col("rtype")))
    .withColumn(
        "silver_dedupe_hash",
        sha2(concat_ws("||",
            col("event_ts").cast("string"),
            col("id").cast("string"),
            col("qr").cast("string"),
            col("name"),
            col("rrtype").cast("string"),
            col("rdata_norm"),
            col("src_ip"),
            col("dst_ip"),
        ), 256)
        )
    )

    df_dedup = df_h.dropDuplicates(["silver_dedupe_hash"])


    after = df_dedup.count()
    if verbose:
        logger.info(f"[deduplicate_by_keys] Rows before: {before}, after: {after}")
        return df_dedup.drop("name","qname_norm","rrname_norm","rdata_norm","rrtype")
    
    return df_dedup.drop("name","qname_norm","rrname_norm","rdata_norm","rrtype")


def explode_and_normalise(
    df: DataFrame,
    exp_column: str,
    fields: list,
    placeholder: str = "-",
    require_key: bool = True,
    verbose: bool = False
) -> DataFrame:
    """
    Explodes a nested array column (e.g., 'questions' or 'answers') and normalizes selected fields.
    """
    before = df.count()

    df = df.withColumn(exp_column, explode(exp_column))

    if require_key:
        key_col = fields[0]
        df = df.filter(
            col(exp_column).isNotNull() & col(f"{exp_column}.{key_col}").isNotNull()
        )
    else:
        df = df.filter(col(exp_column).isNotNull())

    # Build multiple withColumn calls if your Spark doesn't support withColumns
    for field in fields:
        df = df.withColumn(
            field,
            when(col(f"{exp_column}.{field}").isNotNull(), col(f"{exp_column}.{field}")).otherwise(placeholder)
        )

    after = df.count()
    if verbose:
        logger.info(f"{exp_column} dataframe before exploding: {before}, after: {after}")

    return df.drop(exp_column)


def standardize_schema(
    df: DataFrame,
    schema_map: dict[str, DataType | type],
    *,
    timestamp_formats: dict[str, str] | None = None,
    use_try_cast: bool = True,
    verbose: bool = False,
) -> DataFrame:
    """
    Cast selected top-level columns to desired types.
    """
    timestamp_formats = timestamp_formats or {}

    for col_name, dtype in schema_map.items():
        if col_name not in df.columns:
            continue

        dtype_inst = dtype() if isinstance(dtype, type) else dtype
        dt_simple = dtype_inst.simpleString()

        if col_name in timestamp_formats:
            fmt = timestamp_formats[col_name]
            df = df.withColumn(col_name, to_timestamp(col(col_name), fmt))
            continue

        if use_try_cast:
            df = df.withColumn(col_name, expr(f"try_cast(`{col_name}` as {dt_simple})"))
        else:
            df = df.withColumn(col_name, col(col_name).cast(dtype_inst))

    if verbose:
        print("[standardize_schema] applied casts:", {k: (v.__name__ if isinstance(v, type) else v) for k, v in schema_map.items()})
    return df


def split_dataset(df: DataFrame, verbose: bool = False) -> list:
    """
    Splits the DNS dataset into questions and answers based on qr.
    """
    questions_df = df.filter(df["qr"] == 0)
    answers_df = df.filter(df["qr"] == 1)

    if verbose:
        full_count = df.count()
        q_count = questions_df.count()
        a_count = answers_df.count()
        logger.info(f"full dataset: {full_count}, questions: {q_count}, answers: {a_count}")

    return [questions_df, answers_df]


def shannon_entropy(s):
    if not s:
        return 0
    prob = [float(s.count(c)) / len(s) for c in set(s)]
    entropy = -sum(p * math.log2(p) for p in prob)
    return entropy

def map_dns_subdomains(domain_series):
    subdomain_map = defaultdict(set)
    for fqdn in domain_series.dropna().unique():
        extracted = tldextract.extract(fqdn)
        root_domain = f"{extracted.domain}.{extracted.suffix}"
        if extracted.subdomain:
            subdomain_map[root_domain].add(extracted.subdomain)
    return subdomain_map


def flatten_df(df: DataFrame) -> DataFrame:
    df_q_exp = df.withColumn("q_exp", F.explode_outer(F.col("questions")))
    q_cols_map = {
        "qname": F.col("q_exp.qname"),
        "qtype": F.col("q_exp.qtype"),
        "qclass": F.col("q_exp.qclass"),
    }

    a_cols_map = {
        "rrname": F.col("answers_exp.rrname"),
        "rtype": F.col("answers_exp.rtype"),
        "rclass": F.col("answers_exp.rclass"),
        "rdata": F.col("answers_exp.rdata"),
        "ttl": F.col("answers_exp.ttl"),
    }
    df_q_exp = df_q_exp.withColumns(q_cols_map)
    df_a_exp = df_q_exp.withColumn("answers_exp", F.explode_outer(F.col("answers")))
    df_a_exp = df_a_exp.withColumns(a_cols_map)

    """ tag empty, valid and invalid questions and answers"""
    df2 = df_a_exp
    df2 = df2.withColumn("is_valid_question",F.col("qname").isNotNull().cast("int"))
    df2 = df2.withColumn("is_valid_answer", F.col("rrname").isNotNull().cast("int"))
    
    return df2.drop(
        "questions","answers","q_exp","answers_exp"
    )


def convert_to_silver(df, tenant):
    df = add_event_date(df)
    df = deduplicate_by_hash(df, verbose=True)
    return (
        df
        .withColumn("tenant", F.lit(tenant))
        .select(
            "tenant","event_date","event_ts","src_ip","dst_ip","dst_port","id","opcode","qdcount","qr","rcode",
            "qname","qtype","qclass","is_valid_question","ancount","rclass","rdata","rrname","rtype","ttl","is_valid_answer"
        )

    )


def top_n(df, col, n=10, topn_type=None, target_col="topN"):
    """
    Compute top-N values within each (tenant, event_date) partition for the given column.
    The returned array-of-structs uses a generic field name 'name' so that different
    sources (e.g., qname vs root_qname) can be unioned by name.

    Parameters
    ----------
    df : DataFrame
        Source dataframe with columns: tenant, event_date, and `col`.
    col : str
        Column name to rank on (e.g., "qname" or "root_qname").
    n : int, optional
        Number of top items to keep per (tenant, event_date). Default 10.
    topn_type : str or None, optional
        Optional label to attach (e.g., "qname" or "root_qname") for downstream partitioning.
    target_col : str, optional
        Name of the aggregated array-of-structs column to output. Default "topN".

    Returns
    -------
    DataFrame
        Columns: tenant, event_date, target_col (array<struct<rank:int, name:string, query_count:long>>)
        and a topN_type column if provided.
    """
    # Per-(tenant,event_date,col) counts
    counts = (
        df.groupBy("tenant", "event_date", col)
          .agg(F.count(F.lit(1)).alias("cnt"))
    )

    # Deterministic ranking within each (tenant, event_date)
    w = Window.partitionBy("tenant", "event_date").orderBy(F.desc("cnt"), F.asc(F.col(col)))
    ranked = counts.withColumn("rank", F.row_number().over(w)) \
                   .filter(F.col("rank") <= F.lit(n))

    # Collect top-N into an ordered array; the struct standardizes the key to 'name'
    aggregated = (
        ranked.groupBy("tenant", "event_date")
              .agg(
                  F.sort_array(
                      F.collect_list(
                          F.struct(
                              F.col("rank").alias("rank"),
                              F.col(col).cast("string").alias("name"),  # <— generic field
                              F.col("cnt").alias("query_count"),
                              F.lit(None).cast("double").alias("entropy")
                              
                          )
                      ),
                      asc=True
                  ).alias(target_col)
              )
    )

    if topn_type is not None:
        aggregated = aggregated.withColumn("topN_type", F.lit(topn_type))

    return aggregated


def high_entropy_name(df: DataFrame) ->DataFrame:

    high_entropy_topN = (
        df
        .filter("is_high_entropy")  # assumes this boolean exists
        .groupBy("tenant", "event_date", "qname")
        .agg(
            F.count("*").alias("query_count"),
            F.max("qname_entropy").alias("entropy")
        )
        .withColumn(
            "rank",
            F.row_number().over(
                Window.partitionBy("tenant", "event_date")
                    .orderBy(F.col("entropy").desc_nulls_last())
            )
        )
        .filter(F.col("rank") <= 10)
        .groupBy("tenant", "event_date")
        .agg(
            F.sort_array(
                F.collect_list(
                    F.struct(
                        F.col("rank"),
                        F.col("qname").cast("string").alias("name"),
                        F.col("query_count"),
                        F.col("entropy").cast("double").alias("entropy")
                    )
                ),
                asc=True
            ).alias("topN")
        )
        .withColumn("topN_type", F.lit("high_entropy"))
    )
    return df


def compute_breakdowns(df: DataFrame) ->DataFrame:
    rcode_breakdown = (
    df
    .filter(F.col("qr") == 1)
    .groupBy("tenant", "event_date", "rcode")
        .agg(F.count("*").alias("count"))
        .groupBy("tenant", "event_date")
        .agg(
            F.collect_list(
                F.struct(
                    F.col("rcode").cast("int").alias("code"),
                    F.col("count"),
                )
            ).alias("breakdown")
        )
    ).withColumn("breakdown_type", F.lit("rcode_breakdown"))

    qtype_breakdown = (
        df
        .filter(F.col("qr") == 0)
        .groupBy("tenant", "event_date", "qtype")
        .agg(F.count("*").alias("count"))
        .groupBy("tenant", "event_date")
        .agg(
            F.collect_list(
                F.struct(
                    F.col("qtype").cast("int").alias("code"),
                    F.col("count"),
                )
            ).alias("breakdown")
        )
    ).withColumn("breakdown_type", F.lit("qtype_breakdown"))

    return qtype_breakdown.unionByName(rcode_breakdown)


def intent_from_thresholds(col_name: str, warn: float, alert: float):
    return (
        F.when(F.col(col_name) >= alert, F.lit("alert"))
         .when(F.col(col_name) >= warn, F.lit("warn"))
         .otherwise(F.lit("neutral"))
         )


def build_base_kpis(df: DataFrame) ->DataFrame:
    kpi_base = (
        df.groupBy("tenant", "event_date")
        .agg(
            F.count("*").alias("total_queries"),
            F.countDistinct("name").alias("unique_queries"),
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

    max_entropy_qname = (
        df
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
    kpi_base = kpi_base.join(max_entropy_qname,on=["tenant", "event_date"], how="left")

    return kpi_base


def build_risk_kpis(df: DataFrame) ->DataFrame:
    
    INTENT_THRESHOLDS = {
        "high_entropy_query_ratio": (0.15, 0.25),
        "max_qname_entropy": (3.8, 4.2),
        "nxdomain_ratio": (0.20, 0.40),
        "unique_query_ratio": (0.60, 0.80),
        "long_query_ratio": (0.15, 0.30),
        "invalid_char_ratio": (0.05, 0.10),
        "apex_ratio": (0.50, 0.70),
        "avg_query_length": (35, 45)
        }   
    
    risk_kpis = (
        df
        .groupBy("tenant", "event_date")
        .agg(
            F.sum(F.col("is_high_entropy").cast("int")).alias("high_entropy_query_count"),
            (F.sum(F.col("is_high_entropy").cast("int")) / F.count("*")).alias("high_entropy_query_ratio"),
            F.sum(F.col("is_apex").cast("int")).alias("apex_count"),
            F.sum(F.col("has_invalid_chars").cast("int")).alias("invalid_char_count"),
            F.sum((F.col("rcode") == 3).cast("int")).alias("nxdomain_count"),
            F.countDistinct("name").alias("unique_queries"),
            F.avg("qname_length").alias("avg_query_length"),
            F.max("qname_length").alias("max_query_length"),
            F.sum(F.when(F.col("qname_length") > 80, 1).otherwise(0)).alias("long_query_count"),
            F.max("qname_entropy").alias("max_qname_entropy"),
            F.count("*").alias("total_count")
        )
        .withColumn("apex_ratio", F.col("apex_count") / F.col("total_count"))
        .withColumn("invalid_char_ratio", F.col("invalid_char_count") / F.col("total_count"))
        .withColumn("nxdomain_ratio", F.col("nxdomain_count") / F.col("total_count"))
        .withColumn("unique_query_ratio", F.col("unique_queries") / F.col("total_count"))
        .withColumn("long_query_ratio", F.col("long_query_count") / F.col("total_count"))
        .drop("unique_queries")
    )

    

    for col_name, (warn, alert) in INTENT_THRESHOLDS.items():
        risk_kpis = risk_kpis.withColumn(
            f"{col_name}_intent",
            intent_from_thresholds(col_name, warn, alert)
        )

    return risk_kpis    