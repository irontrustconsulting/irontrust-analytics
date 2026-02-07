
import React from "react";

type Props = {
  columns?: 1 | 2 | 3;
  children: React.ReactNode;
  className?: string;
};

export function DashboardGrid({ columns = 3, children, className }: Props) {
  const colsClass = `cols-${columns}`;
  return <div className={`dashboard-grid ${colsClass} ${className ?? ""}`.trim()}>{children}</div>;
}
