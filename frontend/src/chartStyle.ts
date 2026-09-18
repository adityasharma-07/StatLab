import type { Layout } from 'plotly.js'

// Chart colors, shared by every chart so they read as one system.
export const CHART_COLORS = {
  primary: '#2a78d6', // main data marks
  secondary: '#eb6834', // a second series (the regression line)
  text: '#52514e',
  grid: '#e1e0d9',
  axis: '#c3c2b7',
}

const FONT_FAMILY = 'system-ui, -apple-system, "Segoe UI", sans-serif'

// Layout settings every chart starts from: quiet grid and axes so the data
// marks are the loudest thing on the chart.
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
