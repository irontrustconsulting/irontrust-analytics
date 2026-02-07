import { useEffect, useRef } from "react";

type Props = {
  children: React.ReactNode;
};

export function PlotCard({ children }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Force a resize after layout settles
    const timer = setTimeout(() => {
      window.dispatchEvent(new Event("resize"));
    }, 50);

    return () => clearTimeout(timer);
  }, []);

  return (
    <div
      ref={ref}
      style={{
        width: "100%",
        minHeight: 420,      // 🔑 STABLE HEIGHT
        background: "#fff",
        borderRadius: 8,
        padding: "0.5rem",
        boxSizing: "border-box",
      }}
    >
      {children}
    </div>
  );
}
