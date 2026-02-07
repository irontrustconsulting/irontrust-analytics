type KPIGridProps = {
  children: React.ReactNode;
  ariaLabel?: string;
};

export function KPIGrid({ children, ariaLabel }: KPIGridProps) {
  return (
    <div className="kpi-grid" aria-label={ariaLabel}>
      {children}
    </div>
  );
}
