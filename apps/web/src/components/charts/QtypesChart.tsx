import Plot from "react-plotly.js";
import { COLORS } from "../../utils/dashboardColors";
import type { QtypeCount } from "../../types";


type Props = {
  data: QtypeCount[];
};

export function QtypeBreakdownChart({ data }: Props) {
  const normalized = data.map(d => ({
    count: d.count ?? 0,       // default 0
    qtype: d.qtype ?? -1,      // default -1 (or any placeholder)
  }));

  const sorted = [...normalized].sort((a, b) => b.count - a.count);

  return (
    <Plot
      data={[
        {
          x: sorted.map(d => d.count), // now always number
          y: sorted.map(d => `QTYPE ${d.qtype}`), // now always string
          type: "bar",
          orientation: "h",
          marker: { color: COLORS.volumeBlue },
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

      config={{ responsive: true }}
      style={{ width: "100%", height: "100%" }}
    />
  );
}

