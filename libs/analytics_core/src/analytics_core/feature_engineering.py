
# src/dns_exfiltration/feature_engineering.py
# Feature engineering utilities for DNS analytics (PySpark), Python 3.12+

from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType,
    StringType,
    StructType,
    StructField,
)
from collections import Counter
import math
from typing import Optional
from analytics_core.udfs import (
    domain_parts_udf, shannon_entropy_norm_udf_v1, shannon_entropy_bits_udf_v1, has_invalid_chars_udf_v1
)

# ---------------------------------------------------------------------
# tldextract setup (no network; uses built-in snapshot of suffix list)
# ---------------------------------------------------------------------
# try:
#    import tldextract
#    _extractor = tldextract.TLDExtract(suffix_list_urls=None)
#except Exception:
#    _extractor = None  # UDFs will return NULL where extractor is unavailable


# ---------------------------------------------------------------------
# Core: Shannon entropy (bits per character)
# ---------------------------------------------------------------------
def _compute_entropy(s: Optional[str]) -> Optional[float]:
    """
    Shannon entropy (bits per character) over characters in `s`.
    Returns:
      - None if input is None
      - 0.0 if empty after stripping
    Clamps tiny floating-point artifacts to 0.0 (avoids -0.0).
    """
    if s is None:
        return None
    s = s.strip()
    if not s:
        return 0.0

    counts = Counter(s)
    N = len(s)
    probs = [c / N for c in counts.values()]
    H = -sum(p * math.log2(p) for p in probs)

    # Clamp to non-negative and avoid -0.0 representation
    if H < 0:
        H = 0.0
    H = round(H, 6)
    if H == 0.0:
        return 0.0

    return float(H)

entropy_udf = F.udf(_compute_entropy, DoubleType())


def add_entropy(df, src_col: str = "qname", out_col: str = "qname_entropy"):
    """
    Add Shannon entropy of `src_col` (as-is) into column `out_col`.
    Assumes silver layer already normalized names (lowercased, no trailing dot).
    """
    return df.withColumn(out_col, entropy_udf(F.col(src_col)))


# ---------------------------------------------------------------------
# QNAME length (total) and per-label length stats
# ---------------------------------------------------------------------
def add_qname_length(df, src_col: str = "qname", out_col: str = "qname_length"):
    """
    Adds total length of `src_col` (including dots as present).
    """

    # 1. Remove trailing dot (.) from qname
    df = df.withColumn(src_col, F.regexp_replace(F.col(src_col), r"\.$", ""))

    # 2. compute qname length
    df = df.withColumn(out_col, F.length(F.col(src_col)))

    return df


def add_qname_label_lengths(
    df,
    src_col: str = "qname",
    out_array_col: str = "qname_label_lengths",
    out_max_col: str = "qname_label_len_max",
    out_mean_col: str = "qname_label_len_mean",
    out_min_col: str = "qname_label_len_min",
):
    """
    Splits qname on '.' and computes per-label lengths, ignoring empty labels
    (e.g., trailing dot -> ''), then aggregates max/mean/min.

    Assumes qname is normalized; this function still guards against trailing dots.
    """
    # Split on dots
    labels = F.split(F.col(src_col), r"\.")
    # Filter out empty labels: filter(x -> x != '')
    non_empty_labels = F.expr(f"filter({src_col}_labels, x -> x <> '')").alias(None)  # placeholder since we can't refer to temp name
    # Use inline transform/filter without temp names:
    labels_clean = F.expr(f"filter(split({src_col}, '\\\\.'), x -> x <> '')")
    lengths = F.transform(labels_clean, lambda x: F.length(x))

    df2 = df.withColumn(out_array_col, lengths)

    # Aggregate lengths
    sum_lengths = F.aggregate(F.col(out_array_col), F.lit(0), lambda acc, x: acc + x)
    count_labels = F.size(F.col(out_array_col))

    return (
        df2.withColumn(out_max_col, F.when(count_labels > 0, F.array_max(F.col(out_array_col))).otherwise(F.lit(None)))
           .withColumn(out_min_col, F.when(count_labels > 0, F.array_min(F.col(out_array_col))).otherwise(F.lit(None)))
           .withColumn(out_mean_col, F.when(count_labels > 0, sum_lengths / count_labels).otherwise(F.lit(None)))
    )


# ---------------------------------------------------------------------
# Root domain & parts via tldextract
# ---------------------------------------------------------------------

def add_domain_parts(
    df,
    src_col: str = "qname",
    out_struct_col: str = "domain_parts",
    subdomain_col: str = "subdomain",
    domain_col: str = "domain",
    suffix_col: str = "suffix",
    registered_col: str = "root_domain",
    label_count_col: str ="subdomain_label_count"
):
    """
    Adds a struct column with (subdomain, domain, suffix, registered_domain),
    then expands into separate columns for convenience.
    """
    df2 = df.withColumn(out_struct_col, domain_parts_udf(F.col(src_col)))
    return (df2
        .withColumn(subdomain_col,  F.col(f"{out_struct_col}.subdomain"))
        .withColumn(domain_col,     F.col(f"{out_struct_col}.domain"))
        .withColumn(suffix_col,     F.col(f"{out_struct_col}.suffix"))
        .withColumn(registered_col, F.col(f"{out_struct_col}.root_domain"))
        .withColumn(label_count_col, F.col(f"{out_struct_col}.subdomain_count"))
        .drop(out_struct_col)
    )


# ---------------------------------------------------------------------
#  entropy (dots removed)
# ---------------------------------------------------------------------


def add_entropy(df):
    """
    Adds 'subdomain_entropy' computed from the subdomain part of `src_col`.
    Entropy is over characters excluding dots. Rows with no subdomain yield NULL.
    """
     #q = q.withColumn("qname_entropy", shannon_entropy_udf(F.col("qname")))
    df= df.withColumn("qname_entropy", shannon_entropy_bits_udf_v1(F.col("qname")))
    df = df.withColumn("qname_entropy_norm", shannon_entropy_norm_udf_v1(F.col("qname")))

    #q = q.withColumn("subdomain_entropy", shannon_entropy_udf(F.col("subdomain")))
    df = (
         df
         .withColumn("subdomain_entropy", shannon_entropy_bits_udf_v1(F.col("subdomain")))
         .withColumn("is_apex_v1", F.col("subdomain").isNull() | (F.col("subdomain") == ""))
         .withColumn("has_invalid_chars_v1", has_invalid_chars_udf_v1(F.col("qname")))
    )
    df = df.withColumn("subdomain_entropy_norm", shannon_entropy_norm_udf_v1(F.col("subdomain")))
    
    return df


def root_domain_cardinality(df):
    # Step 1: Compute root domain cardinality
  
    df_root_domain_cardinality = df.groupBy("root_domain").agg(
        F.countDistinct("subdomain").alias("root_domain_cardinality")
    )

    # Step 2: Join root domain cardinality with the original DataFrame (q)
    df = df.join(
        df_root_domain_cardinality,
        on="root_domain",   # Join on root domain
        how="left"          # Left join to keep all rows from original DataFrame
    )

    return df

'''
def add_subdomain_cardinality_window(
    df,
    time_col: str = "event_ts",
    window_duration: str = "1 day",
    slide_duration: str | None = None,
    root_col: str = "root_domain",
    src_col: str = "qname",
    sub_col: str | None = None,
    out_col: str = "root_subdomain_cardinality_window",
    group_cols: list[str] | None = None,
    use_approx: bool = False,
    rsd: float = 0.05,
    min_length: int = 1,
    remove_wildcards: bool = False,
    fillna_zero: bool = True,
):
    """
    Time-windowed DISTINCT subdomain cardinality per (group_cols + root_domain + window).
    Normalizes subdomains and excludes NULL/empty/wildcard-only cases.
    """
    # Ensure we have a subdomain column
    tmp_sub_col = None
    if sub_col is None or (sub_col not in df.columns):
        tmp_sub_col = "__tmp_subdomain__"
        df = add_subdomain_column(df, src_col=src_col, out_col=tmp_sub_col)
        sub_col = tmp_sub_col

    win = F.window(F.col(time_col), window_duration, slide_duration) if slide_duration else F.window(F.col(time_col), window_duration)
    keys = (list(group_cols) if group_cols else []) + [root_col, "window"]

    labels_expr = (
        f"filter("
        f"split(lower({sub_col}), '\\\\.+'), "
        f"x -> x <> ''" + ( " and x <> '*'" if remove_wildcards else "" ) +
        f")"
    )
    sub_norm = F.expr(f"array_join({labels_expr}, '.')")

    df_w = (df
            .withColumn("window", win)
            .withColumn("__sub_norm__", sub_norm)
            .withColumn("__sub_len__", F.length(F.col("__sub_norm__")))
            .filter(F.col(root_col).isNotNull())
            .filter(F.col("__sub_norm__").isNotNull())
            .filter(F.col("__sub_len__") >= F.lit(min_length))
    )

    if use_approx:
        agg = (df_w
               .groupBy(*[F.col(k) for k in keys])
               .agg(F.approx_count_distinct(F.col("__sub_norm__"), rsd=rsd).alias(out_col)))
    else:
        agg = (df_w
               .groupBy(*[F.col(k) for k in keys])
               .agg(F.countDistinct(F.col("__sub_norm__")).alias(out_col)))

    result = df_w.join(agg, on=keys, how="left")
    if fillna_zero:
        result = result.fillna({out_col: 0})

    # Cleanup temp
    if tmp_sub_col is not None:
        result = result.drop(tmp_sub_col)
    result = result.drop("__sub_norm__", "__sub_len__")

    return result

'''
def add_domain_suffix_label_stats(
    df,
    domain_col: str = "domain",
    suffix_col: str = "suffix",
    out_mean_col: str = "domain_suffix_len_mean",
    out_max_col: str = "domain_suffix_len_max",
    out_min_col: str = "domain_suffix_len_min",
    subdomain_col: str = "subdomain",
):
    """
    Computes label length stats over domain + suffix only.
    If subdomain is NULL, these reflect exactly the two labels.
    If subdomain exists, these reflect domain+suffix (excluding subdomain).
    """
    dom_len = F.length(F.coalesce(F.col(domain_col), F.lit("")))
    suf_len = F.length(F.coalesce(F.col(suffix_col), F.lit("")))

    # Count how many of domain/suffix are non-empty (handle rare missing suffix or domain)
    non_empty = (F.when(dom_len > 0, F.lit(1)).otherwise(F.lit(0))
                 + F.when(suf_len > 0, F.lit(1)).otherwise(F.lit(0)))

    total = dom_len + suf_len

    df2 = (df
           .withColumn(out_mean_col, F.when(non_empty > 0, total / non_empty).otherwise(F.lit(None)))
           .withColumn(out_max_col, F.greatest(dom_len, suf_len))
           .withColumn(out_min_col, F.least(
               F.when(dom_len > 0, dom_len).otherwise(F.lit(None)),
               F.when(suf_len > 0, suf_len).otherwise(F.lit(None))
           ))
    )
    return df2


'''
def add_subdomain_label_count(
    df,
    sub_col: str | None = "subdomain",
    src_col: str = "qname",
    out_col: str = "subdomain_label_count",
    remove_wildcards: bool = False,
):
    """
    Per-row count of labels in the subdomain.
    - If subdomain is NULL/empty -> 0
    - Normalizes: lowercases, collapses multiple dots, strips leading/trailing dots
    - Optionally removes '*' labels

    Parameters:
      - sub_col: column with subdomain; if None or missing, derives from qname via tldextract.
      - src_col: qname (used only if sub_col is None).
      - remove_wildcards: if True, exclude '*' labels from the count.
    """
    # Ensure we have a subdomain column
    tmp_sub_col = None
    if (sub_col is None) or (sub_col not in df.columns):
        tmp_sub_col = "__tmp_subdomain__"
        df = add_subdomain_column(df, src_col=src_col, out_col=tmp_sub_col)
        sub_col = tmp_sub_col

    # Treat the literal string "NULL" as NULL if present in dirty data
    # and trim whitespace
    sub_clean_base = F.when(
        F.col(sub_col).isNull() | (F.lower(F.col(sub_col)) == F.lit("null")),
        F.lit(None)
    ).otherwise(F.trim(F.col(sub_col)))

    # Build an array of normalized labels:
    # - lower(subdomain)
    # - split on one-or-more dots (handles "a..b")
    # - filter out empty labels
    # - optionally filter out '*' labels
    labels_expr = (
        f"filter("
        f"split(lower({sub_col}), '\\\\.+'), "
        f"x -> x <> ''" + ( " and x <> '*'" if remove_wildcards else "" ) +
        f")"
    )
    labels = F.expr(labels_expr)

    # If subdomain is NULL/empty -> 0, else size(labels)
    df2 = (
        df.withColumn("__subdomain_base__", sub_clean_base)
          .withColumn(out_col,
              F.when(
                  F.col("__subdomain_base__").isNull() | (F.length(F.col("__subdomain_base__")) == 0),
                  F.lit(0)
              ).otherwise(F.size(labels))
          )
          .drop("__subdomain_base__")
    )

    # Drop temporary derived subdomain if we created it
    if tmp_sub_col is not None:
        df2 = df2.drop(tmp_sub_col)

    return df2'''


def add_event_date(df):
    return (
        df
        .withColumn(
            "event_ts",
            F.coalesce(
                # ISO-8601 timestamps
                F.to_timestamp(
                    "timestamp",
                    "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
                ),
                # Unix epoch seconds
                F.to_timestamp(
                    F.from_unixtime(F.col("timestamp").cast("double"))
                )
            )
        )
        .drop("timestamp")
        .withColumn("event_date", F.to_date("event_ts"))
    )


def add_time_features(df):
    # Adding time-based features: Hour of Day, Day of Week
    q = df
    q = q.withColumn("hour_of_day", F.hour(F.col("event_ts"))) \
        .withColumn("day_of_week", F.dayofweek(F.col("event_ts")))

    # Adding frequency of each qname (number of queries per qname)
    q_freq = q.groupBy("qname").agg(F.countDistinct("id").alias("query_frequency"))
    q = q.join(q_freq, on="qname", how="left")

    # Adding distinct source IP count per qname
    q_ip_count = q.groupBy("qname").agg(F.countDistinct("src_ip").alias("unique_src_ips"))
    q = q.join(q_ip_count, on="qname", how="left")

    return q
