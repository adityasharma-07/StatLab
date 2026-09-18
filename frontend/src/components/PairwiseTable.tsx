import { formatP } from '../format'
import type { PairwiseResult } from '../types'

interface PairwiseTableProps {
  pairs: PairwiseResult[]
}

// Which specific pairs of groups differ (the post-hoc test results).
export function PairwiseTable({ pairs }: PairwiseTableProps) {
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Group A</th>
          <th>Group B</th>
          <th>Adjusted p-value</th>
          <th>Different?</th>
        </tr>
      </thead>
      <tbody>
        {pairs.map((pair) => (
          <tr key={`${pair.group_a}|${pair.group_b}`}>
            <td>{pair.group_a}</td>
            <td>{pair.group_b}</td>
            <td className="number">{formatP(pair.p_value)}</td>
            <td>{pair.significant ? <span className="tag tag-significant">✓ Yes</span> : <span className="tag">No</span>}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
