import Plotly from 'plotly.js-cartesian-dist-min'
import type { Data, Layout } from 'plotly.js'
import { useEffect, useRef } from 'react'

interface PlotProps {
  data: Data[]
  layout: Partial<Layout>
}

// A thin React wrapper around Plotly: draw into a div, redraw when props change.
export function Plot({ data, layout }: PlotProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return
    // Plotly.react updates an existing chart in place (or creates it the first time).
    Plotly.react(container, data, layout, { displayModeBar: false, responsive: true })
  }, [data, layout])

  useEffect(() => {
    const container = containerRef.current
    // Free Plotly's resources when the component is removed from the page.
    return () => {
      if (container) Plotly.purge(container)
    }
  }, [])

  return <div ref={containerRef} className="plot" />
}
