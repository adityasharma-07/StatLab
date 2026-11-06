import { useEffect, useState } from 'react'
import { analyze, fetchColumns, fetchDatasets, uploadCsv } from './api'
import './App.css'
import { columnOptions, describePair } from './columns'
import { ColumnPickers } from './components/ColumnPickers'
import { DatasetPicker } from './components/DatasetPicker'
import { ResultsPanel } from './components/ResultsPanel'
import type { AnalyzeResponse, ColumnProfile, DataSource } from './types'

interface Upload {
  session: string
  filename: string
}

function App() {
  const [datasets, setDatasets] = useState<string[]>([])
  const [upload, setUpload] = useState<Upload | null>(null)
  const [source, setSource] = useState<DataSource>({})
  const [profile, setProfile] = useState<ColumnProfile | null>(null)
  const [colA, setColA] = useState('')
  const [colB, setColB] = useState('')
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Load a source's columns and default to a numeric + categorical pair.
  function showProfile(newSource: DataSource, newProfile: ColumnProfile) {
    const options = columnOptions(newProfile)
    const firstNumeric = options.find((option) => option.kind === 'numeric')
    const firstCategorical = options.find((option) => option.kind === 'categorical')
    setSource(newSource)
    setProfile(newProfile)
    setColA(firstNumeric?.name ?? options[0]?.name ?? '')
    setColB(firstCategorical?.name ?? options[1]?.name ?? '')
    setResult(null)
  }

  // Switch between a built-in dataset and an uploaded CSV.
  async function openSource(newSource: DataSource) {
    setError('')
    try {
      showProfile(newSource, await fetchColumns(newSource))
    } catch (caught) {
      setError(errorMessage(caught))
    }
  }

  async function handleUpload(file: File) {
    setError('')
    try {
      // The upload response already includes the column profile.
      const response = await uploadCsv(file)
      setUpload({ session: response.session_id, filename: response.filename })
      showProfile({ session: response.session_id }, response)
    } catch (caught) {
      setError(errorMessage(caught))
    }
  }

  // On first load, fetch the dataset list and open the first one.
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
  const optionA = options.find((option) => option.name === colA)
  const optionB = options.find((option) => option.name === colB)
  const sameColumn = colA === colB

  return (
    <main className="page">
      <header className="page-header">
        <h1>StatLab</h1>
        <p>Pick a dataset and two columns. StatLab picks the analysis that fits them, runs it, and plots the result.</p>
      </header>

      <section className="controls-panel">
        <div className="controls">
          <DatasetPicker
            datasets={datasets}
            selectedDataset={source.dataset ?? ''}
            uploadedName={upload?.filename ?? ''}
            onSelectDataset={(dataset) => openSource({ dataset })}
            onSelectUpload={() => upload && openSource({ session: upload.session })}
            onUpload={handleUpload}
          />
          <ColumnPickers
            options={options}
            colA={colA}
            colB={colB}
            onChangeA={(column) => { setColA(column); setResult(null) }}
            onChangeB={(column) => { setColB(column); setResult(null) }}
          />
          <button className="analyze-button" onClick={runAnalysis} disabled={!colA || !colB || sameColumn || loading}>
            {loading ? 'Analyzing…' : 'Analyze'}
          </button>
        </div>

        {profile && (
          <div className="panel-footnotes">
            <p className="pair-preview">{describePair(optionA, optionB)}</p>
            <p className="hint">
              {profile.row_count} rows.
              {profile.excluded.length > 0 &&
                ` Not offered: ${profile.excluded.map((item) => `${item.column} (${item.reason})`).join(', ')}.`}
            </p>
          </div>
        )}
      </section>

      {error && <div className="notice notice-error">{error}</div>}

      {result && (
        <section className="results">
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
