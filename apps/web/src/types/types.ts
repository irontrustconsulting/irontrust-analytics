// types.ts
export interface AvgEntropyResult {
  qname: string;
  avg_entropy: number;
  query_count: number;
}

export interface AvgEntropyResponse {
  tenant: string;
  template: string;
  results: AvgEntropyResult[];
}

export interface QnameLengthResult {
  qname: string;
  qname_length: number;
}