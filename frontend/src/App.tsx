import { useEffect, useState } from 'react'
import { analyze, fetchColumns, fetchDatasets } from './api'
import './App.css'
import { columnOptions } from './columns'
import { ColumnPickers } from './components/ColumnPickers'
import { DatasetPicker } from './components/DatasetPicker'
import { ResultsPanel } from './components/ResultsPanel'
import type { AnalyzeResponse, ColumnProfile, DataSource } from './types'

function App() {
  const [datasets, setDatasets] = useState<string[]>([])
  const [source, setSource] = useState<DataSource>({})
  const [profile, setProfile] = useState<ColumnProfile | null>(null)
  const [colA, setColA] = useState('')
  const [colB, setColB] = useState('')
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Switch to a data source: load its column profile and pick sensible
  // default columns (a numeric one and a categorical one, when available).
  async function openSource(newSource: DataSource) {
    setError('')
    setResult(null)
    try {
      const newProfile = await fetchColumns(newSource)
      const options = columnOptions(newProfile)
      const firstNumeric = options.find((option) => option.kind === 'numeric')
      const firstCategorical = options.find((option) => option.kind === 'categorical')
      setSource(newSource)
      setProfile(newProfile)
      setColA(firstNumeric?.name ?? options[0]?.name ?? '')
      setColB(firstCategorical?.name ?? options[1]?.name ?? '')
    } catch (caught) {
      setError(errorMessage(caught))
    }
  }

  // On first load: fetch the built-in dataset list and open the first one.
  useEffect(() => {
    async function start() {
      try {
        const response = await fetchDatasets()
        setDatasets(response.datasets)
        if (response.datasets.length > 0) await openSource({ dataset: response.datasets[0] })
      } catch (caught) {
        setError(errorMessage(caught))
      }
    }
    start()
  }, [])

  async function runAnalysis() {
    setError('')
    setLoading(true)
    try {
      setResult(await analyze({ ...source, col_a: colA, col_b: colB }))
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setLoading(false)
    }
  }

  const options = profile ? columnOptions(profile) : []

  return (
    <main className="page">
      <header className="page-header">
        <h1>StatScope</h1>
        <p>Pick a dataset and two columns. StatScope chooses the right statistical test, runs it, and shows the result.</p>
      </header>

      <section className="card">
        <div className="controls">
          <DatasetPicker datasets={datasets} selected={source.dataset ?? ''} onSelect={(dataset) => openSource({ dataset })} />
          <ColumnPickers
            options={options}
            colA={colA}
            colB={colB}
            onChangeA={(column) => { setColA(column); setResult(null) }}
            onChangeB={(column) => { setColB(column); setResult(null) }}
          />
          <button className="analyze-button" onClick={runAnalysis} disabled={!colA || !colB || loading}>
            {loading ? 'Analyzing…' : 'Analyze'}
          </button>
        </div>

        {profile && (
          <p className="hint">
            {profile.row_count} rows.
            {profile.excluded.length > 0 &&
              ` Not offered: ${profile.excluded.map((item) => `${item.column} (${item.reason})`).join(', ')}.`}
          </p>
        )}
      </section>

      {error && <div className="notice notice-error">{error}</div>}

      {result && (
        <section className="card">
          <ResultsPanel result={result} />
        </section>
      )}
    </main>
  )
}

function errorMessage(caught: unknown): string {
  return caught instanceof Error ? caught.message : 'Something went wrong.'
}

export default App
