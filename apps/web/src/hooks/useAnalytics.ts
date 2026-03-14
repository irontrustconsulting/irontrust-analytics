// src/hooks/useAnalytics.ts
import { useEffect, useState } from "react";
import type { AnalyticsOutput } from "../types/analytics";

async function fetchAnalytics(url: string, signal?: AbortSignal): Promise<AnalyticsOutput> {
  const res = await fetch(url, { signal });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const json = await res.json();

  // Validate required fields
  if (!json?.base_kpis || !json?.risk_kpis) {
    throw new Error("Invalid analytics payload (missing base_kpis or risk_kpis)");
  }

  return json as AnalyticsOutput;
}

export function useAnalytics(url: string) {
  const [data, setData] = useState<AnalyticsOutput | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();

    setLoading(true);
    setError(null);

    fetchAnalytics(url, controller.signal)
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e) => {
        if (!cancelled) {
          if (e.name === "AbortError") return;
          setError(e.message ?? String(e));
          setData(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [url]);

  return { data, error, loading };
}
