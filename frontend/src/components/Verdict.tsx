interface VerdictProps {
  significant: boolean
  headline: string
  detail: string
}

// The verdict states its result in words, so it never depends on colour alone.
export function Verdict({ significant, headline, detail }: VerdictProps) {
  return (
    <div className={significant ? 'verdict verdict-significant' : 'verdict'}>
      <p className="verdict-label">{significant ? 'Significant' : 'Not significant'}</p>
      <p className="verdict-headline">{headline}</p>
      <p className="verdict-detail">{detail}</p>
    </div>
  )
}
