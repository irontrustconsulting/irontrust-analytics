// transform.ts
import type { AvgEntropyResult } from '../types/types';

export function buildEntropyChartData(results: AvgEntropyResult[]) {
  return {
    categories: results.map(r => r.qname),
    entropyValues: results.map(r => r.avg_entropy),
    queryCounts: results.map(r => r.query_count),
  };
}
