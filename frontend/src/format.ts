// Small display helpers shared by the results components.

export function formatP(p: number): string {
  // Tiny p-values (like 5.6e-48) are unreadable and falsely precise, so
  // follow the usual reporting convention and cap them at "< 0.001".
  if (p < 0.001) return 'p < 0.001'
  return `p = ${p.toFixed(3)}`
}

export function formatNumber(value: number): string {
  // Up to 2 decimals, without trailing zeros: 3700 -> "3,700", 0.8712 -> "0.87".
  return value.toLocaleString('en-US', { maximumFractionDigits: 2 })
}
