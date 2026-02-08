import { useMemo } from "react";
import { useAnalytics } from "../hooks/useAnalytics";

import { QnameEntropyHistogram } from "./QnameEntropyHistogram";
import { TopQnamesChart } from "../components/charts/TopQnamesChart";
import { SubdomainEntropyHistogram } from "../components/charts/SubdomainEntropyHistogramChart";
import { DashboardHeader } from "../components/layout/DashboardHeader";
import { KPIGridSkeleton } from "../components/layout/KPIGridChart";
import { KPIGrid } from "../components/layout/v2/KPIGrid";
import { KPICard } from "../components/layout/v2/KPICard";
import { RcodeBreakdownChart } from "../components/charts/RCodeChart";
import { QtypeBreakdownChart } from "../components/charts/QtypesChart";
import { TopDomainsChart } from "../components/charts/v2/TopDomainsChart";
import { HighEntropyQnamesChart } from "../components/charts/v2/HighEntropyQName";

import { DashboardCard } from "../components/layout/v2/DashboardCard";
import { DashboardSection } from "../components/layout/v2/DashboardSection";
import { DashboardGrid } from "../components/layout/v2/DashboardGrid";
import { KPIGroup } from "../components/layout/v2/KPIGroup";


import "../components/layout/v2/dashboard.css";

type Props = {
  tenantId: string;
  eventDate: string;
};

export default function AnalyticsDashboard({ tenantId, eventDate }: Props) {
  const url = useMemo(
    () =>
      `${import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"}/v2/analytics?tenant_id=${encodeURIComponent(
        tenantId
      )}&event_date=${encodeURIComponent(eventDate)}`,
    [tenantId, eventDate]
  );

  const { data, error, loading } = useAnalytics(url);

  if (error) return <div>Error: {error}</div>;
  if (!data && !loading) return <div>No analytics available.</div>;

  // --- normalize optional numbers ---
  const totalQueries = data?.total_queries ?? 0;
  const uniqueQnames = data?.unique_qnames ?? 0;
  const uniqueRootDomains = data?.unique_root_domains ?? 0;
  const uniqueSrcIps = data?.unique_src_ips ?? 0;

  const highEntropyQueryCount = data?.high_entropy_query_count ?? 0;
  const highEntropyQueryRatio = data?.high_entropy_query_ratio ?? 0;
  const maxQNameEntropy = data?.max_qname_entropy ?? 0;
  const maxEntropyQName = data?.max_entropy_qname ?? "";
  const nxdomainRatio = data?.nxdomain_ratio ?? 0;

  const alertFlags = {
    high_entropy: data?.alert_high_entropy ?? false,
    nxdomain: data?.alert_nxdomain ?? false,
  };

  // --- normalize optional arrays ---
  const qnameEntropyHistogram = data?.qname_entropy_histogram ?? [];
  const subdomainEntropyHistogram = data?.subdomain_entropy_histogram ?? [];
  const topQnames = data?.top_qnames ?? [];
  const topRootDomains = data?.top_root_domains ?? [];
  const highEntropyQnamesTopN = data?.high_entropy_qnames_topN ?? [];
  const rcodeBreakdown = data?.rcode_breakdown ?? [];
  const qtypeBreakdown = data?.qtype_breakdown ?? [];

  return (
    <div className="dashboard-page" style={{ padding: "1.5rem", maxWidth: "1800px", margin: "0 auto" }}>
      <DashboardHeader tenantId={data?.tenant ?? tenantId} eventDate={data?.event_date ?? eventDate} title="DNS Analytics Dashboard (V1)" />

      <DashboardSection title="Overview">
      {loading ? (
        <KPIGridSkeleton />
      ) : (
        <>
          <KPIGroup title="Risk Indicators">
            <KPIGrid ariaLabel="Risk KPIs">
              <KPICard
                label="High-entropy Queries"
                value={highEntropyQueryCount.toLocaleString()}
                caption={`Share: ${(highEntropyQueryRatio * 100).toFixed(1)}%`}
                intent={alertFlags.high_entropy ? "alert" : "neutral"}
              />
              <KPICard
                label="Max QNAME Entropy"
                value={maxQNameEntropy.toFixed(2)}
                text={maxEntropyQName}
              />
              <KPICard
                label="NXDOMAIN Ratio"
                value={`${(nxdomainRatio * 100).toFixed(1)}%`}
                caption="Failed resolutions"
                intent={alertFlags.nxdomain ? "warn" : "neutral"}
              />
            </KPIGrid>
          </KPIGroup>

          <KPIGroup title="Traffic Metadata">
            <KPIGrid ariaLabel="Context KPIs">
              <KPICard
                label="Total queries"
                value={totalQueries.toLocaleString()}
                caption="Requests observed in the selected window"
              />
              <KPICard
                label="Unique QNAMEs"
                value={uniqueQnames.toLocaleString()}
                caption="Distinct queried names"
              />
              <KPICard
                label="Unique Root Domains"
                value={uniqueRootDomains.toLocaleString()}
                caption="Distinct eTLD+1 roots"
              />
              <KPICard
                label="Unique Source IPs"
                value={uniqueSrcIps.toLocaleString()}
                caption="Clients generating queries"
              />
            </KPIGrid>
          </KPIGroup>
        </>
      )}
    </DashboardSection>

    <DashboardSection title="Distributions">
      <DashboardGrid columns={3}>
        <DashboardCard title="QName Entropy" span={2}>
          {loading ? <div className="skeleton" /> : <QnameEntropyHistogram data={qnameEntropyHistogram} />}
        </DashboardCard>
        <DashboardCard title="Subdomain Entropy">
          {loading ? <div className="skeleton" /> : <SubdomainEntropyHistogram data={subdomainEntropyHistogram} />}
        </DashboardCard>
      </DashboardGrid>
    </DashboardSection>

    <DashboardSection title="Top‑N">
      <DashboardGrid columns={3}>
        <DashboardCard title="Top QNAMEs">{loading ? <div className="skeleton" /> : <TopQnamesChart data={topQnames} />}</DashboardCard>
        <DashboardCard title="Top Root Domains">{loading ? <div className="skeleton" /> : <TopDomainsChart data={topRootDomains} />}</DashboardCard>
        <DashboardCard title="High‑Entropy QNAMEs">{loading ? <div className="skeleton" /> : <HighEntropyQnamesChart data={highEntropyQnamesTopN} />}</DashboardCard>
      </DashboardGrid>
    </DashboardSection>

    <DashboardSection title="Breakdowns">
      <DashboardGrid columns={2}>
        <DashboardCard title="RCODE Breakdown">{loading ? <div className="skeleton" /> : <RcodeBreakdownChart data={rcodeBreakdown} />}</DashboardCard>
        <DashboardCard title="Query Type Breakdown">{loading ? <div className="skeleton" /> : <QtypeBreakdownChart data={qtypeBreakdown} />}</DashboardCard>
      </DashboardGrid>
    </DashboardSection>
  </div>
  );
}
