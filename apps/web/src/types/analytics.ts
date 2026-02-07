// src/types/analytics.ts

export type HistogramBin = {
  bin?: string;
  count?: number;
};

export type TopQName = {
  qname?: string;
  query_count?: number;
};

export type RcodeCount = {
  rcode?: number;
  count?: number;
};

export type QtypeCount = {
  qtype?: number;
  count?: number;
};

export type TopRootDomain = {
  root_domain?: string;
  query_count?: number;
  rank?: number;
};

export type HighEntropyQName = {
  qname?: string;
  entropy?: number;
  query_count?: number;
};

export interface AnalyticsResponse {
  // identity
  tenant?: string;
  event_date?: string; // ISO date string from API (Spark date)

  // totals
  total_queries?: number;
  unique_qnames?: number;
  unique_root_domains?: number;
  unique_subdomains?: number;
  unique_src_ips?: number;

  // entropy + structure stats
  avg_qname_entropy?: number;
  max_qname_entropy?: number;
  avg_subdomain_entropy?: number;
  max_subdomain_entropy?: number;
  avg_subdomain_count?: number;
  max_subdomain_count?: number;

  // Top-N and breakdowns/histograms
  top_qnames?: TopQName[];
  rcode_breakdown?: RcodeCount[];
  qtype_breakdown?: QtypeCount[];
  top_root_domains?: TopRootDomain[];
  qname_entropy_histogram?: HistogramBin[];
  subdomain_entropy_histogram?: HistogramBin[];

  // high-entropy KPIs
  high_entropy_query_count?: number;
  high_entropy_query_ratio?: number;
  max_entropy_qname?: string;
  high_entropy_qnames_topN?: HighEntropyQName[];

  // NXDOMAIN
  nxdomain_count?: number;
  nxdomain_ratio?: number;

  // alert flags
  alert_high_entropy?: boolean;
  alert_nxdomain?: boolean;
}
