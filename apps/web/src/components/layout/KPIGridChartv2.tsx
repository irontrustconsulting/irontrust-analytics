type KPIPropsv2 = {
  high_entropy_query_count: number;
  high_entropy_query_ratio: number;
  max_qname_entropy: number;
  max_entropy_qname: string;
};

export function KPIGridv2(props: KPIPropsv2) {
  const items = [
    { label: "High entropy query count", value: props.high_entropy_query_count },
    { label: "High entropy query ratio", value: props.high_entropy_query_ratio },
    { label: "max_qname_entropy", value: props.max_qname_entropy },
    { label: "max_entropy_qname", value: props.max_entropy_qname },
  ];

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
        gap: "1rem",
        marginBottom: "2rem",
      }}
    >
      {items.map(i => (
        <div
          key={i.label}
          style={{
            padding: "1rem",
            border: "1px solid #e0e0e0",
            borderRadius: 6,
            background: "#fafafa",
          }}
        >
          <div style={{ fontSize: "0.85rem", color: "#666" }}>{i.label}</div>
          <div style={{ fontSize: "1.6rem", fontWeight: 600 }}>
            {i.value.toLocaleString()}
          </div>
        </div>
      ))}
    </div>
  );
}
