# udfs.py (MVP v1 entropy upgrades - cleaned for Python 3.12 + Spark 3.5.x)

from pyspark.sql.functions import udf
from pyspark.sql.types import (
    FloatType, DoubleType, StringType, IntegerType, BooleanType,
    StructType, StructField
)
import math
# import tldextract
# ---------------------------------------------------------------------
# tldextract setup (no network; uses built-in snapshot of suffix list)
# ---------------------------------------------------------------------
try:
    import tldextract
    _extractor = tldextract.TLDExtract(
        cache_dir=False,
        fallback_to_snapshot=True,
        suffix_list_urls=None)
    
except Exception:
    _extractor = None  # UDFs will return NULL where extractor is unavailable

# ===============================================================
# Legacy baseline functions
# ===============================================================

def shannon_entropy(s):
    if not s or not isinstance(s, str):
        return 0.0
    prob = [float(s.count(c)) / len(s) for c in set(s)]
    entropy = -sum(p * math.log2(p) for p in prob)
    return 0.0 if entropy == 0.0 else entropy

shannon_entropy_udf = udf(shannon_entropy, FloatType())

def extract_domain_parts(qname):
    if not qname or not isinstance(qname, str):
        return (None, None, None, None, 0)

    extracted = _extractor(qname)
    subdomain = extracted.subdomain if extracted.subdomain else None
    domain = extracted.domain if extracted.domain else None
    suffix = extracted.suffix if extracted.suffix else None
    root_domain = f"{domain}.{suffix}" if domain and suffix else None
    subdomain_count = len(subdomain.split(".")) if subdomain else 0

    return (subdomain, domain, suffix, root_domain, subdomain_count)

domain_parts_udf = udf(
    extract_domain_parts,
    StructType([
        StructField("subdomain", StringType(), True),
        StructField("domain", StringType(), True),
        StructField("suffix", StringType(), True),
        StructField("root_domain", StringType(), True),
        StructField("subdomain_count", IntegerType(), True),
    ])
)

# ===============================================================
# v1: Clean entropy analytics (no type hints for UDF calls)
# ===============================================================

# RFC 1035-compliant alphabet for DNS labels
_ALPHABET = set("abcdefghijklmnopqrstuvwxyz0123456789-")
_HMAX = math.log2(len(_ALPHABET))  # ≈ 5.21 bits/character


def _clean_hostname_component(s):
    """
    Lowercase, remove dots, filter to [a-z0-9-].
    Return None if empty or invalid.
    """
    if s is None or not isinstance(s, str):
        return None

    s = s.lower().replace(".", "")
    s = "".join(ch for ch in s if ch in _ALPHABET)
    return s if s else None


def _has_invalid_chars_raw(s):
    """
    True if s contains characters outside [a-z0-9-.]
    """
    if s is None or not isinstance(s, str):
        return False

    s = s.lower()
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-.")
    return any(ch not in allowed for ch in s)


def shannon_entropy_bits_v1(s):
    """
    Shannon entropy in bits/character on cleaned strings.
    Returns None for invalid or empty inputs.
    """
    s = _clean_hostname_component(s)
    if s is None:
        return None

    counts = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1

    n = len(s)
    H = 0.0
    for c in counts.values():
        p = c / n
        H -= p * math.log2(p)

    return H


def shannon_entropy_norm_v1(s):
    """
    Normalized Shannon entropy (0–1).
    """
    H = shannon_entropy_bits_v1(s)
    return None if H is None else (H / _HMAX)


# --- Registered UDFs (v1) ---

shannon_entropy_bits_udf_v1 = udf(shannon_entropy_bits_v1, DoubleType())
shannon_entropy_norm_udf_v1 = udf(shannon_entropy_norm_v1, DoubleType())
has_invalid_chars_udf_v1 = udf(_has_invalid_chars_raw, BooleanType())


def is_idn_v1(s):
    """
    True if qname contains an 'xn--' punycode label.
    """
    if s is None or not isinstance(s, str):
        return False

    return "xn--" in s.lower()


is_idn_udf_v1 = udf(is_idn_v1, BooleanType())