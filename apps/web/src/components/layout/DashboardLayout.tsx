type RowProps = {
  children: React.ReactNode;
  columns?: number;
};

export function DashboardRow({ children, columns = 2 }: RowProps) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
        gap: "1.25rem",          // horizontal + vertical gap within row
        marginBottom: "2.5rem",  // vertical gap BETWEEN rows
      }}
    >
      {children}
    </div>
  );
}

