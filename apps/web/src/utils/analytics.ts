// src/api/analytics.ts
import type { AnalyticsResponse } from "../types";

const API_BASE = "http://127.0.0.1:8000/v1/tenants";
const TENANT = "tenant-demo-1";

// Fetch the list of available queries
export async function fetchQueryList() {
  const res = await fetch(`${API_BASE}/${TENANT}/analytics/templates`);
  if (!res.ok) throw new Error('Failed to fetch query list');
  return res.json(); // Expected to return an array of query IDs
}

// Run the selected query and fetch its results
export async function runQuery(queryId: string) {
  const res = await fetch(`${API_BASE}/${TENANT}/analytics/run/${queryId}?limit=8000`);
  if (!res.ok) throw new Error(`Failed to run query: ${queryId}`);
  
  const data = await res.json();

  // Extract only the "results" field
  return data.results || []; // Return the results array (empty array if no results)
}


export async function fetchAnalytics(url: string): Promise<AnalyticsResponse> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const json = await res.json();
  // Optional: shallow runtime checks for critical fields
  if (!json?.tenant_id || !json?.event_date) {
    throw new Error("Invalid analytics payload: missing identity fields");
  }
  return json as AnalyticsResponse;
}
