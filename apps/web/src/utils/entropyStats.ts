
// utils/entropyStats.ts
export type HistogramBin = { bin: string; count: number; };

export const BIN_ORDER = [
  "0.0–0.5","0.5–1.0","1.0–1.5","1.5–2.0",
  "2.0–2.5","2.5–3.0","3.0–4.0","4.0+",
];
export const HIGH_ENTROPY_START_BIN = "3.0–4.0";

export function computeHighEntropyPercent(data: HistogramBin[]): number {
  const byBin = new Map(data.map(d => [d.bin, d.count]));
  const ordered = BIN_ORDER.map(bin => byBin.get(bin) ?? 0);
  const total = ordered.reduce((a, b) => a + b, 0);
  if (total === 0) return 0;

  const startIdx = BIN_ORDER.indexOf(HIGH_ENTROPY_START_BIN);
  const high = ordered.slice(startIdx).reduce((a, b) => a + b, 0);
  return (high / total) * 100;
}
