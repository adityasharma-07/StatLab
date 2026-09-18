import { formatNumber, formatP } from '../format'
import type { CorrelationResult } from '../types'
import { ScatterChart } from './ScatterChart'
import { Verdict } from './Verdict'

interface CorrelationViewProps {
  result: CorrelationResult
}

export function CorrelationView({ result }: CorrelationViewProps) {
  const headline = result.significant
    ? `${capitalize(result.strength)} ${result.direction} correlation`
    : 'No significant correlation'
  const detail = `Pearson r = ${formatNumber(result.pearson_r)} (${formatP(result.pearson_p)}) · R² = ${formatNumber(result.r_squared)} · n = ${result.n}`

  return (
    <>
      <Verdict significant={result.significant} headline={headline} detail={detail} />

      <ScatterChart result={result} />

      <table className="data-table">
        <thead>
          <tr>
            <th>Measure</th>
            <th>Value</th>
            <th>What it tells you</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Pearson r</td>
            <td className="number">{formatNumber(result.pearson_r)} ({formatP(result.pearson_p)})</td>
            <td>Strength of the straight-line relationship (−1 to +1)</td>
          </tr>
          <tr>
            <td>Spearman ρ</td>
            <td className="number">{formatNumber(result.spearman_rho)} ({formatP(result.spearman_p)})</td>
            <td>Same idea on ranks: robust to outliers and curves</td>
          </tr>
          <tr>
            <td>Regression slope</td>
            <td className="number">{formatNumber(result.slope)}</td>
            <td>
              Each +1 in {result.col_a} goes with {formatNumber(result.slope)} in {result.col_b}
            </td>
          </tr>
          <tr>
            <td>R²</td>
            <td className="number">{formatNumber(result.r_squared)}</td>
            <td>
              Share of the variation in {result.col_b} explained by the line
            </td>
          </tr>
        </tbody>
      </table>
    </>
  )
}

function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1)
}
