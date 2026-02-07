import Plot from "react-plotly.js";
import type { TopRootDomain } from "../../types";

type Props = {
  data: TopRootDomain[];
};

export function TopDomainsChart({ data }: Props) {
  const normalized = data.map(row => ({
    root_domain: row.root_domain ?? "Unknown",
    query_count: row.query_count ?? 0,
  }));

  const labels: string[] = normalized.map(row => row.root_domain);
  const counts: number[] = normalized.map(row => row.query_count);

  return (
    <Plot
      data={[
        {
          x: labels,
          y: counts,
          type: "bar",
          marker: { color: "rgba(255, 127, 14, 0.7)" },
        },
      ]}
      layout={{
        autosize: true,
        margin: { t: 60, l: 200, r: 20, b: 60 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        title: { text: "Top Queried Domains" }, // <-- fixed
        xaxis: { title: { text: "Domain" }, tickangle: -45 },
        yaxis: { title: { text: "Query Count" } },
   
      }}
      style={{ width: "100%", height: "600px" }}
    />
  );
}
