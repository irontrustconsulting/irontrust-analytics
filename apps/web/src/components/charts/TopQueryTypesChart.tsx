// src/components/charts/TopQueryTypesChart.tsx
import Plot from "react-plotly.js";

export function TopQueryTypesChart({ data }) {
  const qtypes = data.map(row => row.qtype);
  const counts = data.map(row => row.query_count);

  return (
    <Plot
      data={[
        {
          x: qtypes,
          y: counts,
          type: "bar",
          marker: { color: "rgba(214, 39, 40, 0.7)" }
        }
      ]}
      layout={{
        title: "Top DNS Query Types",
        xaxis: { title: "Query Type" },
        yaxis: { title: "Count" }
      }}
      style={{ width: "100%", height: "600px" }}
    />
  );
}
