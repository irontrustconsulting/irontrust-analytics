from pyspark.sql import functions as F, types as T


BITS_BINS = [
    ("0.0–0.5",  0.0, 0.5),
    ("0.5–1.0",  0.5, 1.0),
    ("1.0–1.5",  1.0, 1.5),
    ("1.5–2.0",  1.5, 2.0),
    ("2.0–2.5",  2.0, 2.5),
    ("2.5–3.0",  2.5, 3.0),
    ("3.0–4.0",  3.0, 4.0),
    ("4.0–5.0",  4.0, 5.0),
    ("5.0+",     5.0, float("inf")),
]

def build_case_for_bins(col, bins):
    case_expr = None
    for label, left, right in bins:
        cond = (col >= F.lit(left)) & (col < F.lit(right))
        case_expr = F.when(cond, F.lit(label)) if case_expr is None else case_expr.when(cond, F.lit(label))
    return case_expr.otherwise(F.lit(None)).cast(T.StringType())

def build_bins_df(spark, bins):
    # ord gives you a stable sort key
    schema = T.StructType([
        T.StructField("bin", T.StringType(), False),
        T.StructField("ord", T.IntegerType(), False),
    ])
    data = [(label, i) for i, (label, _, _) in enumerate(bins)]
    return spark.createDataFrame(data, schema)

def add_entropy_bin(df):
    q = df
    q_binned = (

        q
        .withColumn("qname_entropy_bin", build_case_for_bins(F.col("qname_entropy"), BITS_BINS))
        .withColumn("subdomain_entropy_bin", build_case_for_bins(F.col("subdomain_entropy"), BITS_BINS))
    )
    return q_binned

# 2) Build the zero filled array of bins
def bins_array_literal(bins=BITS_BINS) -> F.Column:
    """
    Returns a Column containing an ordered array of structs [{ord, bin}].
    No SparkSession needed.
    """
    elems = [F.struct(F.lit(i).alias("ord"), F.lit(label).alias("bin"))
             for i, (label, _, _) in enumerate(bins)]
    return F.array(*elems)



# 3) Aggregate counts per bin
def build_histogram_from_binned(
    df_events,
    bin_col: str,                 # "qname_entropy_bin" OR "subdomain_entropy_bin"
    tenant_col: str = "tenant",
    date_col: str = "event_date",
    exclude_filter: F.Column = None,   # e.g., ~F.col("is_apex_v1") for subdomain
    out_col_name: str = "histogram"
):
    """
    Build a stable, ordered, zero-filled histogram array<struct<bin,count>> 
    for a pre-binned column in df_events (e.g., "qname_entropy_bin").
    """
    # A) Prepare the tenant/date table
    td = df_events.select(tenant_col, date_col).distinct()

    # B) Prepare the ordered bins array and posexplode into (ord, bin)
    bins_arr = bins_array_literal(BITS_BINS)
    td_bins = (
        td.select(tenant_col, date_col, bins_arr.alias("bins"))
          .select(tenant_col, date_col, F.posexplode("bins").alias("ord", "b"))
          .select(tenant_col, date_col, "ord", F.col("b.bin").alias("bin"))
    )

    # C) Optionally exclude rows (e.g., apex) before counting
    df_filtered = df_events if exclude_filter is None else df_events.filter(exclude_filter)

    # D) Count per (tenant, date, bin)
    # Note: some rows may have bin_col = NULL (e.g., subdomain apex). These won't appear in counts (desired).
    counts = (
        df_filtered
        .groupBy(tenant_col, date_col, bin_col)
        .agg(F.count(F.lit(1)).alias("count"))
        .withColumnRenamed(bin_col, "bin")
    )

    # E) Left join counts onto full td × bins → zero fill and collect ordered array
    filled = (
        td_bins
        .join(counts, on=[tenant_col, date_col, "bin"], how="left")
        .select(tenant_col, date_col, "ord", "bin", F.coalesce("count", F.lit(0)).alias("count"))
    )

    out = (
        filled
        .groupBy(tenant_col, date_col)
        .agg(
            F.sort_array(
                F.collect_list(F.struct(F.col("ord"), F.col("bin"), F.col("count"))), asc=True
            ).alias("tmp")
        )
        .select(
            tenant_col, date_col,
            F.expr("transform(tmp, x -> named_struct('bin', x.bin, 'count', x.count))").alias(out_col_name)
        )
    )
    return out


def build_entropy_histograms(q):

    # Qname histogram (bits)
    qname_hist = build_histogram_from_binned(
        df_events=q,
        bin_col="qname_entropy_bin",
        out_col_name="qname_entropy_histogram"
    )

    # Subdomain histogram (bits) — exclude apex
    subdomain_hist = build_histogram_from_binned(
        df_events=q,
        bin_col="subdomain_entropy_bin",
        exclude_filter=~F.col("is_apex_v1"),
        out_col_name="subdomain_entropy_histogram"
    )
    return qname_hist, subdomain_hist

