export function interpolateBlue(factor: number): string {
  // clamp
  const t = Math.max(0, Math.min(1, factor));

  // Light → dark variants of #1f77b4
  const light = [198, 219, 239]; // light blue
  const dark  = [31, 119, 180];  // #1f77b4

  const rgb = light.map((c, i) =>
    Math.round(c + t * (dark[i] - c))
  );

  return `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
}
