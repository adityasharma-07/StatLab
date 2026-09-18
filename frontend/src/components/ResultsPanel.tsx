import type { AnalyzeResponse } from '../types'
import { ChiSquareView } from './ChiSquareView'
import { GroupComparisonView } from './GroupComparisonView'

interface ResultsPanelProps {
  result: AnalyzeResponse
}

// Picks the right view for whatever analysis the engine ran.
export function ResultsPanel({ result }: ResultsPanelProps) {
  // The engine couldn't analyze this pair: show its explanation, not a crash.
  if (result.status !== 'ok') {
    return (
      <div className="notice">
        <strong>Can't analyze these columns.</strong> {result.message}
      </div>
    )
  }

  if (result.analysis === 'chi_square') return <ChiSquareView result={result} />
  return <GroupComparisonView result={result} />
}
