import type { Data } from 'plotly.js'
import { baseLayout } from '../chartStyle'
import type { ChiSquareResult } from '../types'
import { Plot } from './Plot'

interface HeatmapChartProps {
  result: ChiSquareResult
}

// One hue, light to dark: darker cell = more rows in that combination.
const SEQUENTIAL_BLUES: [number, string][] = [
  [0, '#e6f0fc'],
  [0.5, '#5598e7'],
  [1, '#0d366b'],
]

export function HeatmapChart({ result }: HeatmapChartProps) {
  const table = result.contingency

  const trace = {
    type: 'heatmap',
    x: table.cols,
    y: table.rows,
    z: table.counts,
    // The expected counts ride along so the tooltip can show observed vs expected.
    customdata: result.expected,
    colorscale: SEQUENTIAL_BLUES,
    xgap: 2,
    ygap: 2,
    texttemplate: '%{z}', // print the count inside every cell
    hovertemplate:
      `${result.col_a}: %{y}<br>${result.col_b}: %{x}<br>` +
      'observed: %{z}<br>expected if independent: %{customdata}<extra></extra>',
    colorbar: { title: { text: 'rows' }, thickness: 12, outlinewidth: 0 },
  } as Data

  const layout = baseLayout()
  layout.margin = { t: 16, r: 16, b: 56, l: 96 }
  layout.xaxis = { ...layout.xaxis, title: { text: result.col_b }, showgrid: false, type: 'category' }
  // Reversed so the first category is at the top, like reading a table.
  layout.yaxis = { ...layout.yaxis, title: { text: result.col_a }, showgrid: false, type: 'category', autorange: 'reversed' }

  return (
    <figure className="chart">
      <Plot data={[trace]} layout={layout} />
      <figcaption>Each cell counts the rows with that combination of categories. Hover for expected counts.</figcaption>
    </figure>
  )
}
