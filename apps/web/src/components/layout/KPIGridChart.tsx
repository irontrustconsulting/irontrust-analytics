
//import React from "react";

type Props = {
  total_queries: number;
  unique_qnames: number;
  unique_root_domains: number;
  unique_src_ips: number;

  // High-entropy KPIs (optional)
  high_entropy_query_count?: number;
  high_entropy_query_ratio?: number;
  max_qname_entropy?: number;
  max_entropy_qname?: string;

  // NXDOMAIN KPIs (optional)
  nxdomain_ratio?: number;

  // Alerts (optional)
  alert_flags?: {
    high_entropy?: boolean;
    nxdomain?: boolean;
  };
};

const formatPct = (x?: number) =>
  typeof x === "number" ? `${(x * 100).toFixed(1)}%` : "–";

export function KPIGrid({
  total_queries,
  unique_qnames,
  unique_root_domains,
  unique_src_ips,
  high_entropy_query_count,
  high_entropy_query_ratio,
  max_qname_entropy,
  max_entropy_qname,
  nxdomain_ratio,
  alert_flags,
}: Props) {
  const highEntropyBadge = alert_flags?.high_entropy ? (
    <span className="kpi-badge kpi-badge-alert">High entropy</span>
  ) : null;

  const nxdomainBadge = alert_flags?.nxdomain ? (
    <span className="kpi-badge kpi-badge-warn">NXDOMAIN</span>
  ) : null;

  return (
    <div className="kpi-grid" aria-label="Key Performance Indicators">
      {/* Total Queries */}
      <div className="kpi-card" role="group" aria-label="Total queries">
        <div className="kpi-label">Total queries</div>
        <div className="kpi-value">{total_queries.toLocaleString()}</div>
        <div className="kpi-caption">Requests observed in the selected window</div>
      </div>

      {/* Unique QNAMEs */}
      <div className="kpi-card" role="group" aria-label="Unique QNAMEs">
        <div className="kpi-label">Unique QNAMEs</div>
        <div className="kpi-value">{unique_qnames.toLocaleString()}</div>
        <div className="kpi-caption">Distinct queried names</div>
      </div>

      {/* Unique Root Domains */}
      <div className="kpi-card" role="group" aria-label="Unique root domains">
        <div className="kpi-label">Unique Root Domains</div>
        <div className="kpi-value">{unique_root_domains.toLocaleString()}</div>
        <div className="kpi-caption">Distinct eTLD+1 roots</div>
      </div>

      {/* Unique Source IPs */}
      <div className="kpi-card" role="group" aria-label="Unique source IPs">
        <div className="kpi-label">Unique Source IPs</div>
        <div className="kpi-value">{unique_src_ips.toLocaleString()}</div>
        <div className="kpi-caption">Clients generating queries</div>
      </div>

      {/* High-entropy section */}
      <div
        className="kpi-card"
        role="group"
        aria-label="High-entropy metrics"
        title={
          high_entropy_query_ratio !== undefined
            ? `High-entropy share: ${formatPct(high_entropy_query_ratio)}`
            : undefined
        }
      >
        <div className="kpi-label">
          High-entropy Queries
          {highEntropyBadge}
        </div>
        <div className="kpi-value">
          {(high_entropy_query_count ?? 0).toLocaleString()}
        </div>
        <div className="kpi-caption">
          Share: {formatPct(high_entropy_query_ratio)}
        </div>
      </div>

      {/* Max entropy value + name (long text safe) */}
      <div
        className="kpi-card"
        role="group"
        aria-label="Max QNAME entropy"
        title={max_entropy_qname || undefined} // tooltip on hover for long names
      >
        <div className="kpi-label">Max QNAME Entropy</div>
        <div className="kpi-value">
          {typeof max_qname_entropy === "number"
            ? max_qname_entropy.toFixed(2)
            : "–"}
        </div>
        {max_entropy_qname ? (
          <div className="kpi-text">{max_entropy_qname}</div>
        ) : (
          <div className="kpi-caption">Highest entropy QNAME</div>
        )}
      </div>

      {/* NXDOMAIN ratio */}
      <div
        className="kpi-card"
        role="group"
        aria-label="NXDOMAIN ratio"
        title={
          nxdomain_ratio !== undefined
            ? `NXDOMAIN share: ${formatPct(nxdomain_ratio)}`
            : undefined
        }
      >
        <div className="kpi-label">
          NXDOMAIN Ratio
          {nxdomainBadge}
        </div>
        <div className="kpi-value">{formatPct(nxdomain_ratio)}</div>
        <div className="kpi-caption">Failed resolutions</div>
      </div>
    </div>
  );
}

/* Optional: card-level skeleton for loading states */
export function KPIGridSkeleton() {
  return (
    <div className="kpi-grid" aria-label="KPI skeleton">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="kpi-card">
          <div className="kpi-label">Loading…</div>
          <div className="skeleton" style={{ height: 28 }} />
        </div>
      ))}
    </div>
  );
}
