import { formatNumber, formatP } from '../format'
import type { GroupComparisonResult } from '../types'
import { BoxPlotChart } from './BoxPlotChart'
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

      <BoxPlotChart result={result} />

      <table className="data-table">
        <thead>
          <tr>
            <th>Group</th>
            <th>n</th>
            <th>Median</th>
            <th>Mean</th>
          </tr>
        </thead>
        <tbody>
          {result.groups.map((group) => (
            <tr key={group.name}>
              <td>{group.name}</td>
              <td className="number">{group.n}</td>
              <td className="number">{formatNumber(group.median)}</td>
              <td className="number">{formatNumber(group.mean)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  )
}
