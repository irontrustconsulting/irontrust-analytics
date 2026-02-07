import Plot from "react-plotly.js";
import { interpolateBlue } from "../../../utils/colorScale";
import type { TopRootDomain } from "../../../types";

export type TopDomainsProps = {
  data: TopRootDomain[];
};

export function TopDomainsChart({ data }: TopDomainsProps) {
  if (!data || data.length === 0) return <div>No top Domains to display</div>;

  // --- Normalize undefined values ---
  const normalized = data.map(d => ({
    root_domain: d.root_domain ?? "Unknown",
    query_count: d.query_count ?? 0,
  }));

  const counts = normalized.map(d => d.query_count);
  const maxCount = Math.max(...counts);
  const minCount = Math.min(...counts);

  const colors = counts.map(count => {
    const factor = (count - minCount) / (maxCount - minCount || 1); // avoid divide by zero
    return interpolateBlue(factor);
  });

  return (
    <Plot
      data={[
        {
          x: normalized.map(d => d.query_count),
          y: normalized.map(d => d.root_domain),
          type: "bar",
          orientation: "h",
          marker: { color: colors },
        },
      ]}
      layout={{
        autosize: true,
        margin: { t: 40, l: 200, r: 20, b: 60 }, // adjust left for long labels
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        title: { text: "" }, // leave titling to DashboardCard

        xaxis: {
          title: { text: "Query Count" },
          tickformat: ",",

          showgrid: false,

          zeroline: true,
          zerolinecolor: "rgba(255,255,255,0.12)",
          zerolinewidth: 1,

          showline: false,
          ticks: "",                       // no ticks

          tickfont: { color: "var(--text-secondary)" },
        },

       yaxis: {
          title: { text: "", standoff: 20 }, // leave y-axis title optional
          automargin: true,
          autorange: "reversed",              // highest on top
          showgrid: true,
          gridcolor: "rgba(255,255,255,0.07)", // subtle horizontal lines
          zeroline: false,
          showline: false,
          tickfont: { color: "var(--text-secondary)" },
        },

        legend: { orientation: "h", y: -0.25, x: 0, xanchor: "left", yanchor: "top" },
        hovermode: "y",                       // easier hover on horizontal bars
      }}

      useResizeHandler
      style={{ width: "100%", height: "100%" }}
      config={{ responsive: true }}
    />
  );
}
