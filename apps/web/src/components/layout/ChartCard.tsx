import React from "react";

type Props = {
  title: string;
  children: React.ReactNode;
};

export function ChartCard({ title, children }: Props) {
  return (
    <div style={cardStyle}>
      <div style={titleStyle}>{title}</div>
      <div style={contentStyle}>{children}</div>
    </div>
  );
}

/* ===== styles ===== */

const cardStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  background: "#fff",
  borderRadius: 8,
  boxShadow: "0 1px 4px rgba(0,0,0,0.1)",
  padding: "0.75rem",
  minWidth: 0,           // 🔑 critical for grid overflow
  height: "100%",
};

const titleStyle: React.CSSProperties = {
  fontSize: "0.95rem",
  fontWeight: 600,
  marginBottom: "0.5rem",
};

const contentStyle: React.CSSProperties = {
  flex: 1,
  minHeight: 0,          // 🔑 allows Plotly to resize
};
