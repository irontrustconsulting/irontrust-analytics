// src/components/charts/NxDomainChart.tsx
import Plot from "react-plotly.js";

export function NxDomainChart({ data }) {
  const labels = data.map(row => row.qname);
  const counts = data.map(row => row.nxdomain_count);

  return (
    <Plot
      data={[
        {
          x: labels,
          y: counts,
          type: "bar",
          marker: { color: "rgba(219, 64, 82, 0.7)" }
        }
      ]}
      layout={{
        title: "NXDOMAIN Counts per Domain",
        xaxis: { title: "Domain", tickangle: -45 },
        yaxis: { title: "NXDOMAIN Count" },
        margin: { b: 150 }
      }}
      style={{ width: "100%", height: "600px" }}
    />
  );
}
