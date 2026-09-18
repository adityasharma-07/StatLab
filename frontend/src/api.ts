// All calls to the backend live here, so components never build URLs themselves.

import type { AnalyzeRequest, AnalyzeResponse, ColumnProfile, DataSource, DatasetsResponse, UploadResponse } from './types'

// Empty in development (Vite proxies /api) and when FastAPI serves the built
// frontend. Set VITE_API_BASE only if the API is deployed on a different host.
const API_BASE: string = import.meta.env.VITE_API_BASE ?? ''

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    // FastAPI puts a readable error message in the "detail" field.
    const body = await response.json().catch(() => null)
    const detail = typeof body?.detail === 'string' ? body.detail : `Request failed (${response.status})`
    throw new Error(detail)
  }
  return response.json()
}

export async function fetchDatasets(): Promise<DatasetsResponse> {
  const response = await fetch(`${API_BASE}/api/datasets`)
  return readJson<DatasetsResponse>(response)
}

export async function fetchColumns(source: DataSource): Promise<ColumnProfile> {
  const params = new URLSearchParams()
  if (source.dataset) params.set('dataset', source.dataset)
  if (source.session) params.set('session', source.session)
  const response = await fetch(`${API_BASE}/api/columns?${params}`)
  return readJson<ColumnProfile>(response)
}

export async function analyze(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  const response = await fetch(`${API_BASE}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  return readJson<AnalyzeResponse>(response)
}

export async function uploadCsv(file: File): Promise<UploadResponse> {
  // Files are sent as multipart form data; the browser sets the Content-Type.
  const form = new FormData()
  form.append('file', file)
  const response = await fetch(`${API_BASE}/api/upload`, { method: 'POST', body: form })
  return readJson<UploadResponse>(response)
}
