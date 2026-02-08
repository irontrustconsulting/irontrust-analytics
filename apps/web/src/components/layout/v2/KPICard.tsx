type KPIIntent = "neutral" | "warn" | "alert";

type KPICardProps = {
  label: string;
  value: React.ReactNode;
  caption?: string;
  text?: string;
  badge?: React.ReactNode;
  title?: string;
  intent?: KPIIntent;
};

export function KPICard({
  label,
  value,
  caption,
  text,
  badge,
  title,
  intent = "neutral",
}: KPICardProps) {
  return (
    <div
      className={`kpi-card kpi-${intent}`}
      role="group"
      title={title}
    >
      <div className="kpi-label">
        {label}
        {badge}
      </div>
      <div className="kpi-value">{value}</div>
      {text && <div className="kpi-text">{text}</div>}
      {caption && <div className="kpi-caption">{caption}</div>}
    </div>
  );
}
