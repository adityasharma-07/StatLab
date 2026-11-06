import type { Layout } from 'plotly.js'

// Shared by every chart.
export const CHART_COLORS = {
  primary: '#2f5d52', // main data marks
  secondary: '#9a3f16', // a second series (the regression line)
  primaryFill: 'rgba(47, 93, 82, 0.16)',
  text: '#56523f',
  grid: '#ddd9cb',
  axis: '#b9b4a2',
}

const FONT_FAMILY = "'IBM Plex Sans', sans-serif"

// Base layout every chart starts from.
export function baseLayout(): Partial<Layout> {
  return {
    height: 380,
    margin: { t: 16, r: 16, b: 56, l: 64 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { family: FONT_FAMILY, size: 13, color: CHART_COLORS.text },
    xaxis: { gridcolor: CHART_COLORS.grid, linecolor: CHART_COLORS.axis, zeroline: false },
    yaxis: { gridcolor: CHART_COLORS.grid, linecolor: CHART_COLORS.axis, zeroline: false },
    hoverlabel: { font: { family: FONT_FAMILY, size: 13 } },
  }
}
