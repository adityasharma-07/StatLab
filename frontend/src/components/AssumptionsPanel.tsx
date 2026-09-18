import { formatP } from '../format'
import type { GroupComparisonResult } from '../types'

interface AssumptionsPanelProps {
  result: GroupComparisonResult
}

// Why this test was chosen: the conceptual highlight of the app.
// The reason sentence comes from the engine; the table shows the evidence.
export function AssumptionsPanel({ result }: AssumptionsPanelProps) {
  const assumptions = result.assumptions

  return (
    <section className="assumptions">
      <p className="assumptions-title">Why {result.test}?</p>
      <p>{result.test_reason}</p>

      <table className="data-table">
        <thead>
          <tr>
            <th>Assumption check</th>
            <th>Result</th>
            <th>Holds?</th>
          </tr>
        </thead>
        <tbody>
          {assumptions.normality.map((check) => (
            <tr key={check.group}>
              <td>Normality of {check.group} (Shapiro-Wilk)</td>
              <td className="number">{formatP(check.shapiro_p)}</td>
              <td>{check.normal ? '✓ Yes' : '✗ No'}</td>
            </tr>
          ))}
          <tr>
            <td>Equal variances across groups (Levene)</td>
            <td className="number">{formatP(assumptions.levene_p)}</td>
            <td>{assumptions.equal_variance ? '✓ Yes' : '✗ No'}</td>
          </tr>
        </tbody>
      </table>
    </section>
  )
}
