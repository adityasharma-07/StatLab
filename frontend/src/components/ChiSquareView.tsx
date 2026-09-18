import { formatNumber, formatP } from '../format'
import type { ChiSquareResult } from '../types'
import { HeatmapChart } from './HeatmapChart'
import { Verdict } from './Verdict'

interface ChiSquareViewProps {
  result: ChiSquareResult
}

export function ChiSquareView({ result }: ChiSquareViewProps) {
  const headline = result.significant
    ? `Variables are associated (${result.strength} association)`
    : 'No significant association between the variables'
  const detail = `Chi-square ${formatP(result.p_value)} · χ² = ${formatNumber(result.chi2)} (dof = ${result.dof}) · Cramér's V = ${formatNumber(result.cramers_v)} · n = ${result.n}`

  return (
    <>
      <Verdict significant={result.significant} headline={headline} detail={detail} />

      {result.low_expected_warning && (
        <div className="notice">
          <strong>Interpret with care.</strong> More than 20% of cells have an expected count below 5, where the chi-square
          approximation becomes unreliable.
        </div>
      )}

      <HeatmapChart result={result} />
    </>
  )
}
