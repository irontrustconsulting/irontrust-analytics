// src/hooks/useAnalytics.ts
import { useEffect, useState } from "react";
import type { AnalyticsResponse } from "../types";

async function fetchAnalytics(url: string, signal?: AbortSignal): Promise<AnalyticsResponse> {
  const res = await fetch(url, { signal });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const json = await res.json();

  // Use the correct field names
  if (!json?.tenant || !json?.event_date) {
    throw new Error("Invalid analytics payload (missing tenant or event_date)");
  }

  return json as AnalyticsResponse;
}

export function useAnalytics(url: string) {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
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
