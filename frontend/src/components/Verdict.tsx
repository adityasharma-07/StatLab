interface VerdictProps {
  significant: boolean
  headline: string
  detail: string
}

// The big color-coded headline at the top of every result. The icon and the
// wording carry the meaning too, so it never depends on color alone.
export function Verdict({ significant, headline, detail }: VerdictProps) {
  return (
    <div className={significant ? 'verdict verdict-significant' : 'verdict'}>
      <span className="verdict-icon" aria-hidden="true">
        {significant ? '✓' : '–'}
      </span>
      <div>
        <p className="verdict-headline">{headline}</p>
        <p className="verdict-detail">{detail}</p>
      </div>
    </div>
  )
}
