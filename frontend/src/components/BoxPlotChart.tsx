import type { Data } from 'plotly.js'
import type { GroupComparisonResult } from '../types'
import { baseLayout, CHART_COLORS } from '../chartStyle'
import { Plot } from './Plot'

interface BoxPlotChartProps {
  result: GroupComparisonResult
}

export function BoxPlotChart({ result }: BoxPlotChartProps) {
  const groups = result.groups

  // The engine already computed each group's summary, so we hand Plotly the
  // box stats directly instead of shipping every raw row to the browser.
  // All boxes share one color: the x-axis label already says which group is which.
  const trace = {
    type: 'box',
    x: groups.map((group) => group.name),
    q1: groups.map((group) => group.q1),
    median: groups.map((group) => group.median),
    q3: groups.map((group) => group.q3),
    lowerfence: groups.map((group) => group.min),
    upperfence: groups.map((group) => group.max),
    mean: groups.map((group) => group.mean),
    marker: { color: CHART_COLORS.primary },
    line: { width: 2 },
    fillcolor: 'rgba(42, 120, 214, 0.18)',
    showlegend: false,
  } as Data

  const layout = baseLayout()
  layout.xaxis = { ...layout.xaxis, title: { text: result.group_col }, showgrid: false }
  layout.yaxis = { ...layout.yaxis, title: { text: result.value_col } }

  return (
    <figure className="chart">
      <Plot data={[trace]} layout={layout} />
      <figcaption>
        Box = middle 50% of values (Q1 to Q3), line = median, dashed line = mean, whiskers = min to max.
      </figcaption>
    </figure>
  )
}
