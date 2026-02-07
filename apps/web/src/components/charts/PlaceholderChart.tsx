
// src/components/charts/PlaceholderChart.tsx
import React from "react";

export function PlaceholderChart({ data }: { data: unknown[] }) {
  return (
    <pre style={{ whiteSpace: "pre-wrap" }}>
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}
