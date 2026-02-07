// src/components/charts/HighEntropyQnamesChart.tsx
import Plot from "react-plotly.js";
//import { interpolateRed } from "../../../styles/colorScale";
import type { HighEntropyQName } from "../../../types";

type Props = {
  data: HighEntropyQName[];
};

export function HighEntropyQnamesChart({ data }: Props) {
  if (!data || data.length === 0) {
    return <div>No high-entropy QNAMEs detected</div>;
  }

  // --- Normalize undefined values ---
  const normalized = data.map(d => ({
    qname: d.qname ?? "Unknown",
    query_count: d.query_count ?? 0,
    entropy: d.entropy ?? 0,
  }));

  // Sort descending by query_count
  const sorted = [...normalized].sort((a, b) => b.query_count - a.query_count);

  const qnames = sorted.map(d => d.qname);
  const counts = sorted.map(d => d.query_count);
  const entropies = sorted.map(d => d.entropy);

  return (
    <Plot
      data={[
        {
          x: counts,
          y: qnames,
          type: "bar",
          orientation: "h",
          marker: {
            color: entropies,
            colorscale: "Reds",
            colorbar: { title: { text: "Entropy" } },
          },
          hovertemplate:
            "<b>%{y}</b><br>" +
            "Queries: %{x:,}<br>" +
            "Entropy: %{marker.color:.2f}<extra></extra>",
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
