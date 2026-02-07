import Plot from "react-plotly.js";
import { useMemo } from "react";
import { COLORS } from "../utils/dashboardColors";
import type { HistogramBin } from "../types";

type Props = {
  data: HistogramBin[];
  thresholdBits?: number;
  titleThresholdLabel?: string;
};

function parseBinLower(label: string): number {
  const EN_DASH = "–";

  if (label.endsWith("+")) {
    const n = parseFloat(label.replace("+", ""));
    return Number.isFinite(n) ? n : Number.NEGATIVE_INFINITY;
  }

  const parts = label.includes(EN_DASH)
    ? label.split(EN_DASH)
    : label.split("-");

  const lower = parseFloat(parts[0]);
  return Number.isFinite(lower) ? lower : Number.NEGATIVE_INFINITY;
}

export function QnameEntropyHistogram({
  data,
  thresholdBits = 3.0,
  titleThresholdLabel,
}: Props) {

  // ✅ normalize once — after this, NO undefined anywhere
  const ordered = useMemo(
    () =>
      (data ?? []).map(d => ({
        bin: d.bin ?? "Unknown",
        count: d.count ?? 0,
      })),
    [data]
  );

  const totalCount = useMemo(
    () => ordered.reduce((acc, d) => acc + d.count, 0),
    [ordered]
  );

  if (!ordered.length || totalCount === 0) {
    return <div><em>No queries available for this range.</em></div>;
  }

  const highIdx = useMemo(() => {
    for (let i = 0; i < ordered.length; i++) {
      if (parseBinLower(ordered[i].bin) >= thresholdBits) {
        return i;
      }
    }
    return Number.POSITIVE_INFINITY;
  }, [ordered, thresholdBits]);

  const x = ordered.map(d => d.bin);
  const counts = ordered.map(d => d.count);
  const percents = ordered.map(d => (d.count / totalCount) * 100);

  const barColors = ordered.map((_, i) =>
    i >= highIdx ? COLORS.riskRed : COLORS.volumeBlue
  );

  const yMax = Math.max(...counts);
  const yLineTop = yMax * 1.02;
  const yLabel = yMax * 1.03;
  const yTop = Math.max(yMax * 1.08, yLabel * 1.02);

  const thresholdCategory =
    Number.isFinite(highIdx) && highIdx < x.length
      ? x[highIdx]
      : null;

  const labelText =
    titleThresholdLabel ?? `Threshold (≥ ${thresholdBits.toFixed(1)})`;

  return (
    <Plot
      data={[
        {
          x,
          y: counts,
          type: "bar",
          showlegend: false,
          marker: { color: barColors },
          customdata: percents.map(p => [p]),
          hovertemplate:
            "<b>%{x}</b><br>" +
            "Queries: %{y:,}<br>" +
            "Share: %{customdata[0]:.1f}%<extra></extra>",
          name: "Query count",
        },
        {
          x: [null],
          y: [null],
          type: "bar",
          name: `Regular entropy (< ${thresholdBits.toFixed(1)})`,
          marker: { color: COLORS.volumeBlue },
          showlegend: true,
          hoverinfo: "skip",
        },
        {
          x: [null],
          y: [null],
          type: "bar",
          name: `High entropy (≥ ${thresholdBits.toFixed(1)})`,
          marker: { color: COLORS.riskRed },
          showlegend: true,
          hoverinfo: "skip",
        },
      ]}
      layout={{
        bargap: 0.2,
        margin: { t: 10, l: 60, r: 20, b: 115 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",

        xaxis: {
          title: { text: "Entropy Bin (bits/char)", standoff: 22 },
          categoryorder: "array",
          categoryarray: x,
          tickangle: -20,
          automargin: true,
          showgrid: false,                         // remove vertical gridlines
          zeroline: false,
          tickfont: { color: "var(--text-secondary)" },
        },
        yaxis: {
          title: { text: "Query Count" },
          tickformat: ",",
          rangemode: "tozero",
          range: [0, yTop],
          automargin: true,
          showgrid: true,                          // subtle horizontal lines
          gridcolor: "rgba(255,255,255,0.07)",     // match horizontal bar chart
          zeroline: true,
          zerolinecolor: "rgba(255,255,255,0.12)",
          zerolinewidth: 1,
          tickfont: { color: "var(--text-secondary)" },
        },

        legend: {
          orientation: "h",
          x: 0,
          y: -0.55,
          yanchor: "top",
          xanchor: "left",
        },

        shapes: thresholdCategory
          ? [
              {
                type: "line",
                xref: "x",
                yref: "y",
                x0: thresholdCategory,
                x1: thresholdCategory,
                y0: 0,
                y1: yLineTop,
                line: { color: "#111827", width: 2, dash: "dot" },
                layer: "above",
              },
            ]
          : [],
        annotations: thresholdCategory
          ? [
              {
                x: thresholdCategory,
                xref: "x",
                y: yLabel,
                yref: "y",
                yanchor: "bottom",
                text: labelText,
                showarrow: false,
                font: { size: 12, color: "#111827" },
                bgcolor: "rgba(255,255,255,0.85)",
                bordercolor: "rgba(17,24,39,0.2)",
                borderwidth: 1,
                borderpad: 2,
                xanchor: "center",
              },
            ]
          : [],
      }}

      useResizeHandler
      config={{ responsive: true }}
      style={{ width: "100%", height: "100%" }}
    />
  );
}
