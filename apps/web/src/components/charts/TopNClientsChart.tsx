// src/components/charts/TopNClientsChart.tsx
import Plot from "react-plotly.js";
import Plotly from "plotly.js-dist-min";


export function TopNClientsChart({ data }) {
  const clients = data.map(row => row.client_ip);
  const counts = data.map(row => row.query_count);

  return (
    <Plot
      data={[
        {
          x: clients,
          y: counts,
          type: "bar",
          marker: { color: "rgba(31, 119, 180, 0.7)" }
        }
      ]}
      layout={{
        title: "Top Querying Client IPs",
        xaxis: { title: "Client IP", tickangle: -45 },
        yaxis: { title: "Query Count" },
        margin: { b: 150 }
      }}
      style={{ width: "100%", height: "600px" }}
    />
  );
}
