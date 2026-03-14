/**
 * Analytics data models matching the Python Pydantic models.
 * These types define the structure of data from the analytics pipeline.
 */

/**
 * Base KPIs computed from DNS query analytics.
 */
export interface BaseKPIs {
  tenant: string;
  event_date: string;
  total_queries: number;
  unique_queries: number;
  unique_root_domains: number;
  unique_subdomains: number;
  unique_src_ips: number;
  avg_qname_entropy: number;
  max_qname_entropy: number;
  avg_subdomain_entropy: number;
  max_subdomain_entropy: number;
  avg_subdomain_count: number;
  max_subdomain_count: number;
  max_entropy_qname: string | null;
}

/**
 * Intent classification type for risk indicators.
 */
export type IntentLevel = "alert" | "warn" | "neutral";

/**
 * Risk-related KPIs computed from DNS query analytics.
 */
export interface RiskKPIs {
  tenant: string;
  event_date: string;
  high_entropy_query_count: number;
  high_entropy_query_ratio: number;
  apex_count: number;
  invalid_char_count: number;
  nxdomain_count: number;
  avg_query_length: number;
  max_query_length: number;
  long_query_count: number;
  max_qname_entropy: number;
  total_count: number;
  apex_ratio: number;
  invalid_char_ratio: number;
  nxdomain_ratio: number;
  unique_query_ratio: number;
  long_query_ratio: number;
  high_entropy_query_ratio_intent: IntentLevel;
  max_qname_entropy_intent: IntentLevel;
  nxdomain_ratio_intent: IntentLevel;
  unique_query_ratio_intent: IntentLevel;
  long_query_ratio_intent: IntentLevel;
  invalid_char_ratio_intent: IntentLevel;
  apex_ratio_intent: IntentLevel;
  avg_query_length_intent: IntentLevel;
}

/**
 * A single bin in a histogram.
 */
export interface HistogramBin {
  bin: string;
  count: number;
}

/**
 * Type of entropy measurement.
 */
export type EntropyType = "qname" | "subdomain";

/**
 * Histogram distribution of entropy values.
 */
export interface EntropyHistogram {
  tenant: string;
  event_date: string;
  histogram: HistogramBin[];
  entropy_type: EntropyType;
}

/**
 * A single entry in a top-N ranking.
 */
export interface TopNEntry {
  rank: number;
  name: string;
  query_count: number;
  entropy: number | null;
}

/**
 * Type of top-N ranking.
 */
export type TopNType = "top_qnames" | "top_root_domains" | "high_entropy";

/**
 * Top-N rankings of entities by frequency or entropy.
 */
export interface TopNRankings {
  tenant: string;
  event_date: string;
  topN: TopNEntry[];
  topN_type: TopNType;
}

/**
 * A single entry in a breakdown by code or type.
 */
export interface BreakdownEntry {
  code: number;
  count: number;
}

/**
 * Type of breakdown.
 */
export type BreakdownType = "rcode_breakdown" | "qtype_breakdown";

/**
 * Breakdown of queries by response code or query type.
 */
export interface Breakdown {
  tenant: string;
  event_date: string;
  breakdown: BreakdownEntry[];
  breakdown_type: BreakdownType;
}

/**
 * Complete analytics output containing all data types.
 */
export interface AnalyticsOutput {
  base_kpis: BaseKPIs;
  risk_kpis: RiskKPIs;
  histograms: EntropyHistogram[];
  rankings: TopNRankings[];
  breakdowns: Breakdown[];
}

/**
 * Dashboard view type - matches AnalyticsOutput structure
 * Provides a convenient interface for dashboard components
 */
export interface DashboardView extends AnalyticsOutput {
  // Aliases for convenience in dashboard components
  entropy_histograms?: EntropyHistogram[];
  topn_names?: TopNRankings[];
  code_breakdowns?: Breakdown[];
  base_kpi?: BaseKPIs;
  risk_kpi?: RiskKPIs;
}

// Re-export for backwards compatibility
export type HistogramData = EntropyHistogram;
export type TopNData = TopNRankings;
export type BreakdownData = Breakdown;