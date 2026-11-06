import { formatNumber, formatP } from '../format'
import type { ChiSquareResult } from '../types'
import { HeatmapChart } from './HeatmapChart'
import { Verdict } from './Verdict'

interface ChiSquareViewProps {
  result: ChiSquareResult
}

export function ChiSquareView({ result }: ChiSquareViewProps) {
  const headline = result.significant
    ? 'The two columns are associated'
    : 'No significant association between the columns'
  const detail = `Chi-square ${formatP(result.p_value)} · χ² = ${formatNumber(result.chi2)} (dof = ${result.dof}) · n = ${result.n}`

  return (
    <>
      <Verdict significant={result.significant} headline={headline} detail={detail} />

      <HeatmapChart result={result} />
    </>
  )
}
