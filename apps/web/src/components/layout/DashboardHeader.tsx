type Props = {
  tenantId: string;
  eventDate: string;
  title: string
};

export function DashboardHeader({ tenantId, eventDate, title }: Props) {
  return (
    <div style={{ marginBottom: "1.5rem" }}>
      <h1 style={{ marginBottom: "0.25rem" }}>{title}</h1>
      <div style={{ color: "#666" }}>
        Tenant: <strong>{tenantId}</strong> | Date: <strong>{eventDate}</strong>
      </div>
    </div>
  );
}
