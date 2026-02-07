
import React from "react";

type Props = { title?: string; children: React.ReactNode; };

export function DashboardSection({ title, children }: Props) {
  return (
    <section className="dashboard-section">
      {title && <h2 className="dashboard-section-title">{title}</h2>}
      {children}
    </section>
  );
}
``
