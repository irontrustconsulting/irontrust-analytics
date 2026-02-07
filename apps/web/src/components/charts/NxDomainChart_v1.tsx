
// src/components/charts/NxDomainChart.tsx
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from "recharts";
// import type { NxDomainItem } from "../../types";
import type { NxDomainRow } from "../../types";

const label = (s: string | null) => s ?? "(null)";
const truncate = (s: string, max = 40) => (s.length <= max ? s : s.slice(0, max - 1) + "…");

export function NxDomainChart({ data }: { data: NxDomainRow[] }) {
  const chartData = data.map(d => ({ label: label(d.qname), nxdomain_count: d.nxdomain_count }));
    <ResponsiveContainer width="100%" height={380}>
      <BarChart data={chartData} layout="vertical" margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" />
        <YAxis type="category" dataKey="label" width={220} tickFormatter={truncate} />
        <Tooltip formatter={(value, name) => (name === "nxdomain_count" ? Number(value) : value)} />
        <Legend />
        <Bar dataKey="nxdomain_count" name="NXDOMAIN Count" fill="#5b84b3" radius={[0, 6, 6, 0]} />
    </ResponsiveContainer>
  );
}
