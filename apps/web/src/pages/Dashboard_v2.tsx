import { useState, useEffect } from "react";
import axios from "axios";
import { DashboardHeader } from "../components/layout/DashboardHeader";
import { DashboardSection } from "../components/layout/v2/DashboardSection";
import { KPICard } from "../components/layout/v2/KPICard";
import { KPIGridSkeleton } from "../components/layout/KPIGridChart";
import { KPIGroup } from "../components/layout/v2/KPIGroup";
import { KPIGrid } from "../components/layout/v2/KPIGrid";
import type { DashboardView } from "../types";
import "../components/layout/v2/dashboard.css";
import { DashboardGrid } from "../components/layout/v2/DashboardGrid";
import { DashboardCard } from "../components/layout/v2/DashboardCard";
import { QnameEntropyHistogram } from "./QnameEntropyHistogram";
import { TopQnamesChart } from "../components/charts/TopQnamesChart";
import { HighEntropyQnamesChart } from "../components/charts/v2/HighEntropyQName";
import { RcodeBreakdownChart } from "../components/charts/RCodeChart";
import { QtypeBreakdownChart } from "../components/charts/QtypesChart";


const base_url = "http://localhost:8000/analytics";

export default function AnalyticsDashboard() {
  const [dashboard, setDashboard] = useState<DashboardView | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    axios
      .get<DashboardView>(base_url)
      .then((res) => setDashboard(res.data))
      .catch((err) => {
        console.error("API fetch error:", err);
        setError("Failed to load KPI data");
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading KPIs...</p>;
  if (error) return <p>{error}</p>;
  if (!dashboard) return <p>No KPI data available</p>;

  // Correct keys according to your API response (AnalyticsOutput)
  const base_kpi = dashboard.base_kpis;
  const risk_kpi = dashboard.risk_kpis;
  const qnameHistogram = dashboard.histograms.find(h => h.entropy_type === "qname")?.histogram ?? [];
  const subdomainHistogram = dashboard.histograms.find(h => h.entropy_type === "subdomain")?.histogram ?? [];
  const topQnames = dashboard.rankings.find(h => h.topN_type === "top_qnames")?.topN ?? [];
  const topRootDomains = dashboard.rankings.find(h => h.topN_type === "top_root_domains")?.topN ?? [];
  const highEntropyQnamesTopN = dashboard.rankings.find(h => h.topN_type === "high_entropy")?.topN ?? [];
  const rcodeBreakdown = dashboard.breakdowns.find(h => h.breakdown_type === "rcode_breakdown")?.breakdown ?? [];
  const qtypeBreakdown = dashboard.breakdowns.find(h => h.breakdown_type === "qtype_breakdown")?.breakdown ?? [];
  
  

  return (
    <div className="dashboard-page" style={{ padding: "1.5rem", maxWidth: "1800px", margin: "0 auto" }}>
      <DashboardHeader
        tenantId={base_kpi?.tenant ?? "tenantId"}
        eventDate={base_kpi?.event_date ?? "eventDate"}
        title="DNS Analytics Dashboard (V2)"
      />

      <DashboardSection title="Overview">
        {loading || !base_kpi || !risk_kpi ? (
          <KPIGridSkeleton />
        ) : (
          <>
            {/* Base KPI Group */}
            <KPIGroup title="Traffic Metadata">
              <KPIGrid ariaLabel="Base KPIs">
                <KPICard
                  label="Total queries"
                  value={base_kpi?.total_queries?.toLocaleString() ?? "–"}
                  caption="Requests observed in the selected window"
                />
                <KPICard
                  label="Unique QNAMEs"
                  value={base_kpi?.unique_queries?.toLocaleString() ?? "–"}
                  caption="Distinct queried names"
                />
                <KPICard
                  label="Unique Root Domains"
                  value={base_kpi?.unique_root_domains?.toLocaleString() ?? "–"}
                  caption="Distinct eTLD+1 roots"
                />
                <KPICard
                  label="Unique Source IPs"
                  value={base_kpi?.unique_src_ips?.toLocaleString() ?? "–"}
                  caption="Clients generating queries"
                />
              </KPIGrid>
            </KPIGroup>
            {/* Risk KPI Group */}
            <KPIGroup title="Risk Indicators">
            <KPIGrid ariaLabel="Risk KPIs">
              <KPICard
                label="High-entropy Queries"
                value={risk_kpi?.high_entropy_query_count?.toLocaleString() ?? "–"}
                caption={`Share: ${((risk_kpi?.high_entropy_query_ratio ?? 0) * 100).toFixed(1)}%`}
                intent={risk_kpi.high_entropy_query_ratio_intent}
              />
              <KPICard
                label="Max QNAME Entropy"
                value={base_kpi?.max_qname_entropy?.toFixed(2) ?? "–"}
                text={base_kpi?.max_entropy_qname ?? ""}
                intent={risk_kpi.max_qname_entropy_intent}
              />
              <KPICard
                label="NXDOMAIN Ratio"
                value={`${((risk_kpi?.nxdomain_ratio ?? 0) * 100).toFixed(1)}%`}
                caption="Failed resolutions"
                intent={risk_kpi.nxdomain_ratio_intent}
              />
              <KPICard
                label="Max Query Length"
                value={risk_kpi?.max_query_length?.toLocaleString() ?? "–"}
                caption="Longest observed query"
               
              />
              <KPICard
                label="Average Query Length"
                value={risk_kpi?.avg_query_length?.toFixed(2) ?? "–"}
                caption="Mean query length"
                intent={risk_kpi.avg_query_length_intent}
              />
            </KPIGrid>
          </KPIGroup>
          </>
        )}
      </DashboardSection>
      <DashboardSection title="Distributions">
        <DashboardGrid columns={3}>
          <DashboardCard title="QName Entropy" span={2}>
            {loading ? <div className="skeleton" /> : <QnameEntropyHistogram data={qnameHistogram} />}
          </DashboardCard>
          <DashboardCard title="Subdomain Entropy">
            {loading ? <div className="skeleton" /> : <QnameEntropyHistogram data={subdomainHistogram} />}
          </DashboardCard>
        </DashboardGrid>
      </DashboardSection>
      <DashboardSection title="Top‑N">
        <DashboardGrid columns={3}>
          <DashboardCard title="Top QNAMEs">{loading ? <div className="skeleton" /> : <TopQnamesChart data={topQnames} />}</DashboardCard>
          <DashboardCard title="Top Root Domains">{loading ? <div className="skeleton" /> : <TopQnamesChart data={topRootDomains} />}</DashboardCard>
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
