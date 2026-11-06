import type { Data } from 'plotly.js'
import { baseLayout, CHART_COLORS } from '../chartStyle'
import type { RegressionResult } from '../types'
import { Plot } from './Plot'

interface ScatterChartProps {
  result: RegressionResult
}

export function ScatterChart({ result }: ScatterChartProps) {
  const xs = result.points.map((point) => point.x)
  const ys = result.points.map((point) => point.y)

  const pointsTrace: Data = {
    type: 'scatter',
    mode: 'markers',
    name: 'Rows',
    x: xs,
    y: ys,
    // Semi-transparent markers so overlapping points show up as darker areas.
    marker: { color: CHART_COLORS.primary, size: 8, opacity: 0.55 },
    hovertemplate: `${result.col_a}: %{x}<br>${result.col_b}: %{y}<extra></extra>`,
  }

  // A straight line only needs two points: the fitted y at the smallest and
  // largest x, computed from the engine's slope and intercept.
  const xMin = Math.min(...xs)
  const xMax = Math.max(...xs)
  const lineTrace: Data = {
    type: 'scatter',
    mode: 'lines',
    name: 'Fitted line',
    x: [xMin, xMax],
    y: [result.slope * xMin + result.intercept, result.slope * xMax + result.intercept],
    line: { color: CHART_COLORS.secondary, width: 2 },
    hoverinfo: 'skip',
  }

  const layout = baseLayout()
  layout.margin = { t: 40, r: 16, b: 56, l: 64 }
  layout.xaxis = { ...layout.xaxis, title: { text: result.col_a } }
  layout.yaxis = { ...layout.yaxis, title: { text: result.col_b } }
  layout.legend = { orientation: 'h', x: 0, y: 1.12 }

  return (
    <figure className="chart">
      <Plot data={[pointsTrace, lineTrace]} layout={layout} />
    </figure>
  )
}
