import { formatNumber, formatP } from '../format'
import type { GroupComparisonResult } from '../types'
import { AssumptionsPanel } from './AssumptionsPanel'
import { BoxPlotChart } from './BoxPlotChart'
import { PairwiseTable } from './PairwiseTable'
import { Verdict } from './Verdict'

interface GroupComparisonViewProps {
  result: GroupComparisonResult
}

export function GroupComparisonView({ result }: GroupComparisonViewProps) {
  const headline = result.significant ? 'Groups differ significantly' : 'No significant difference between groups'
  const detail = `${result.test} ${formatP(result.p_value)} · statistic = ${formatNumber(result.statistic)} · ${result.group_count} groups, n = ${result.n}`

  return (
    <>
      <Verdict significant={result.significant} headline={headline} detail={detail} />

      <AssumptionsPanel result={result} />

      <BoxPlotChart result={result} />

      {result.pairwise.length > 0 && (
        <section>
          <h3>Which groups differ? — {result.posthoc_test}</h3>
          <PairwiseTable pairs={result.pairwise} />
        </section>
      )}
    </>
  )
}
