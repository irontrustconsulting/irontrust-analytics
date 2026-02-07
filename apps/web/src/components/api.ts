
// src/components/api.ts
import type { RawRow } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE;

/**
 * Fetch raw rows (strings/null) from your API.
 * Returns ONLY the results array; charts will not see envelope metadata.
 */
export default async function getResults(
  tenantId: string,
  queryTemplate: string,
  numRecords: number,
  signal?: AbortSignal
): Promise<RawRow[]> {
  const endpoint = `${API_BASE}/tenants/${encodeURIComponent(
    tenantId
  )}/analytics/dns/${encodeURIComponent(queryTemplate)}`;
  ///analytics/dns/${encodeURIComponent(queryTemplate)}?limit=${encodeURIComponent(numRecords)}

  const res = await fetch(endpoint, {
    method: "GET",
    headers: { Accept: "application/json" },
    signal,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status} ${res.statusText} — ${endpoint} ${text ? "- " + text : ""}`);
  }

  const json = await res.json().catch(() => ({ results: [] }));
  const results = Array.isArray(json?.results) ? json.results : [];
  return results as RawRow[];
}
 