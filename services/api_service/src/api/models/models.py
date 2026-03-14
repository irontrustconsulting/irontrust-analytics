"""
Data models for the Analytics pipeline output.
Uses Pydantic v2 for validation and serialization.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class HistogramBin(BaseModel):
    """A single bin in a histogram."""
    bin: str = Field(..., description="Bin label or range")
    count: int = Field(..., description="Count of items in this bin")


class EntropyHistogram(BaseModel):
    """Histogram distribution of entropy values."""
    tenant: str = Field(..., description="Tenant identifier")
    event_date: str = Field(..., description="Event date in YYYY-MM-DD format")
    histogram: list[HistogramBin] = Field(..., description="List of histogram bins")
    entropy_type: Literal["qname", "subdomain"] = Field(..., description="Type of entropy measured")


class BaseKPIs(BaseModel):
    """Base KPIs computed from DNS query analytics."""
    tenant: str = Field(..., description="Tenant identifier")
    event_date: str = Field(..., description="Event date in YYYY-MM-DD format")
    total_queries: int = Field(..., description="Total number of DNS queries")
    unique_queries: int = Field(..., description="Count of unique DNS queries")
    unique_root_domains: int = Field(..., description="Count of unique root domains")
    unique_subdomains: int = Field(..., description="Count of unique subdomains")
    unique_src_ips: int = Field(..., description="Count of unique source IPs")
    avg_qname_entropy: float = Field(..., description="Average entropy of query names")
    max_qname_entropy: float = Field(..., description="Maximum entropy of query names")
    avg_subdomain_entropy: float = Field(..., description="Average entropy of subdomains")
    max_subdomain_entropy: float = Field(..., description="Maximum entropy of subdomains")
    avg_subdomain_count: float = Field(..., description="Average number of subdomains per domain")
    max_subdomain_count: float = Field(..., description="Maximum number of subdomains per domain")
    max_entropy_qname: Optional[str] = Field(default=None, description="Query name with maximum entropy")


class RiskKPIs(BaseModel):
    """Risk-related KPIs computed from DNS query analytics."""
    tenant: str = Field(..., description="Tenant identifier")
    event_date: str = Field(..., description="Event date in YYYY-MM-DD format")
    high_entropy_query_count: int = Field(..., description="Count of high-entropy queries")
    high_entropy_query_ratio: float = Field(..., description="Ratio of high-entropy queries to total queries")
    apex_count: int = Field(..., description="Count of apex domain queries")
    invalid_char_count: int = Field(..., description="Count of queries with invalid characters")
    nxdomain_count: int = Field(..., description="Count of NXDOMAIN responses")
    avg_query_length: float = Field(..., description="Average length of query names")
    max_query_length: int = Field(..., description="Maximum length of query names")
    long_query_count: int = Field(..., description="Count of unusually long queries")
    max_qname_entropy: float = Field(..., description="Maximum entropy of query names")
    total_count: int = Field(..., description="Total count of queries analyzed")
    apex_ratio: float = Field(..., description="Ratio of apex queries to total queries")
    invalid_char_ratio: float = Field(..., description="Ratio of invalid character queries to total")
    nxdomain_ratio: float = Field(..., description="Ratio of NXDOMAIN responses to total")
    unique_query_ratio: float = Field(..., description="Ratio of unique queries to total queries")
    long_query_ratio: float = Field(..., description="Ratio of long queries to total queries")
    
    # Intent fields (8 fields with alert/warn/neutral values)
    high_entropy_query_ratio_intent: Literal["alert", "warn", "neutral"] = Field(..., description="Intent classification for high entropy query ratio")
    max_qname_entropy_intent: Literal["alert", "warn", "neutral"] = Field(..., description="Intent classification for max qname entropy")
    nxdomain_ratio_intent: Literal["alert", "warn", "neutral"] = Field(..., description="Intent classification for NXDOMAIN ratio")
    unique_query_ratio_intent: Literal["alert", "warn", "neutral"] = Field(..., description="Intent classification for unique query ratio")
    long_query_ratio_intent: Literal["alert", "warn", "neutral"] = Field(..., description="Intent classification for long query ratio")
    invalid_char_ratio_intent: Literal["alert", "warn", "neutral"] = Field(..., description="Intent classification for invalid character ratio")
    apex_ratio_intent: Literal["alert", "warn", "neutral"] = Field(..., description="Intent classification for apex ratio")
    avg_query_length_intent: Literal["alert", "warn", "neutral"] = Field(..., description="Intent classification for average query length")


class TopNEntry(BaseModel):
    """A single entry in a top-N ranking."""
    rank: int = Field(..., description="Rank position (1-based)")
    name: str = Field(..., description="Name of the entry (query, domain, etc.)")
    query_count: int = Field(..., description="Number of queries for this entry")
    entropy: Optional[float] = Field(default=None, description="Entropy value if applicable")


class TopNRankings(BaseModel):
    """Top-N rankings of entities by frequency or entropy."""
    tenant: str = Field(..., description="Tenant identifier")
    event_date: str = Field(..., description="Event date in YYYY-MM-DD format")
    topN: list[TopNEntry] = Field(..., description="List of top-N entries")
    topN_type: Literal["top_qnames", "top_root_domains", "high_entropy"] = Field(..., description="Type of top-N ranking")


class BreakdownEntry(BaseModel):
    """A single entry in a breakdown by code or type."""
    code: int = Field(..., description="Code value (e.g., response code, query type)")
    count: int = Field(..., description="Count of items with this code")


class Breakdown(BaseModel):
    """Breakdown of queries by response code or query type."""
    tenant: str = Field(..., description="Tenant identifier")
    event_date: str = Field(..., description="Event date in YYYY-MM-DD format")
    breakdown: list[BreakdownEntry] = Field(..., description="List of breakdown entries")
    breakdown_type: Literal["rcode_breakdown", "qtype_breakdown"] = Field(..., description="Type of breakdown")


class AnalyticsOutput(BaseModel):
    """Complete analytics output containing all data types."""
    base_kpis: BaseKPIs = Field(..., description="Base KPIs")
    risk_kpis: RiskKPIs = Field(..., description="Risk KPIs")
    histograms: list[EntropyHistogram] = Field(..., description="Entropy histograms")
    rankings: list[TopNRankings] = Field(..., description="Top-N rankings")
    breakdowns: list[Breakdown] = Field(..., description="Breakdowns by code/type")
