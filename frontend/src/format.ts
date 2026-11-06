// Display helpers shared by the results components.

export function formatP(p: number): string {
  // Reporting convention: anything smaller is shown as "< 0.001".
  if (p < 0.001) return 'p < 0.001'
  return `p = ${p.toFixed(3)}`
}

export function formatNumber(value: number): string {
  // Up to 2 decimals, no trailing zeros.
  return value.toLocaleString('en-US', { maximumFractionDigits: 2 })
}
