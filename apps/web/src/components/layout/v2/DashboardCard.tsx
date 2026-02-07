
import React from "react";

type Props = {
  title?: string;
  subtitle?: string;
  span?: number;
  actions?: React.ReactNode;
  children: React.ReactNode;
  ariaLabel?: string;
};

export function DashboardCard({
  title,
  subtitle,
  span = 1,
  actions,
  children,
  ariaLabel,
}: Props) {
  return (
    <section
      className="dashboard-card"
      style={{ gridColumn: `span ${span}` }}
      aria-label={ariaLabel ?? title}
    >
      {(title || subtitle || actions) && (
        <div className="dashboard-card-header">
          {title && <h3 className="dashboard-card-title">{title}</h3>}
          {subtitle && <div className="dashboard-card-subtitle">{subtitle}</div>}
          {actions}
        </div>
      )}
      <div className="dashboard-card-body">{children}</div>
    </section>
  );
}
``
