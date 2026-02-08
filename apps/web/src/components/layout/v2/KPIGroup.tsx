// src/components/layout/v2/KPIGroup.tsx

type Props = {
  title: string;
  children: React.ReactNode;
};

export function KPIGroup({ title, children }: Props) {
  return (
    <div className="kpi-group" role="group" aria-label={title}>
      <div className="kpi-group-title">{title}</div>
      {children}
    </div>
  );
}
