from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field


class TopQname(BaseModel):
    qname: Optional[str] = None
    query_count: Optional[int] = None


class RcodeCount(BaseModel):
    rcode: Optional[int] = None
    count: Optional[int] = None


class QtypeCount(BaseModel):
    qtype: Optional[int] = None
    count: Optional[int] = None


class HistogramBin(BaseModel):
    bin: Optional[str] = None
    count: Optional[int] = None


class TopDomain(BaseModel):
    root_domain: Optional[str] = None
    query_count: Optional[int] = None
    rank: Optional[int] = None


class HighEntropyQName(BaseModel):
    qname: Optional[str] = None
    entropy: Optional[float] = None
    query_count: Optional[int] = None


class AnalyticsGoldRecord(BaseModel):
    # identity
    tenant: Optional[str] = None
    event_date: Optional[date] = None

    # totals
    total_queries: Optional[int] = None
    unique_qnames: Optional[int] = None
    unique_root_domains: Optional[int] = None
    unique_subdomains: Optional[int] = None
    unique_src_ips: Optional[int] = None

    # entropy + structure stats
    avg_qname_entropy: Optional[float] = None
    max_qname_entropy: Optional[float] = None
    avg_subdomain_entropy: Optional[float] = None
    max_subdomain_entropy: Optional[float] = None
    avg_subdomain_count: Optional[float] = None
    max_subdomain_count: Optional[int] = None

    # Top-N and histograms
    top_qnames: List[TopQname] = Field(default_factory=list)
    rcode_breakdown: List[RcodeCount] = Field(default_factory=list)
    qtype_breakdown: List[QtypeCount] = Field(default_factory=list)
    qname_entropy_histogram: List[HistogramBin] = Field(default_factory=list)
    subdomain_entropy_histogram: List[HistogramBin] = Field(default_factory=list)
    top_root_domains: List[TopDomain] = Field(default_factory=list)

    # high entropy KPIs
    high_entropy_query_count: Optional[int] = None
    high_entropy_query_ratio: Optional[float] = None
    max_entropy_qname: Optional[str] = None
    high_entropy_qnames_topN: List[HighEntropyQName] = Field(default_factory=list)

    # NXDOMAIN
    nxdomain_count: Optional[int] = None
    nxdomain_ratio: Optional[float] = None

    # alert flags
    alert_high_entropy: Optional[bool] = None
    alert_nxdomain: Optional[bool] = None
