import { formatNumber, formatP } from '../format'
import type { RegressionResult } from '../types'
import { ScatterChart } from './ScatterChart'
import { Verdict } from './Verdict'

interface RegressionViewProps {
  result: RegressionResult
}

export function RegressionView({ result }: RegressionViewProps) {
  const headline = result.significant
    ? `${result.col_b} rises with ${result.col_a}`
    : 'No significant relationship'
  const negative = result.significant && result.direction === 'negative'
  const detail = `Linear regression ${formatP(result.p_value)} · R² = ${formatNumber(result.r_squared)} · n = ${result.n}`

  return (
    <>
      <Verdict
        significant={result.significant}
        headline={negative ? `${result.col_b} falls as ${result.col_a} rises` : headline}
        detail={detail}
      />

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
            <td>Slope</td>
            <td className="number">{formatNumber(result.slope)}</td>
            <td>
              Each +1 in {result.col_a} goes with {formatNumber(result.slope)} in {result.col_b}
            </td>
          </tr>
          <tr>
            <td>R²</td>
            <td className="number">{formatNumber(result.r_squared)}</td>
            <td>Share of the variation in {result.col_b} explained by the line</td>
          </tr>
        </tbody>
      </table>
    </>
  )
}
