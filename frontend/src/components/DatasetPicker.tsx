import type { ChangeEvent } from 'react'

// The <select> value that stands for "the CSV the user uploaded".
const UPLOADED = '__uploaded__'

interface DatasetPickerProps {
  datasets: string[]
  selectedDataset: string // '' when an uploaded file is active
  uploadedName: string // '' when nothing has been uploaded
  onSelectDataset: (dataset: string) => void
  onSelectUpload: () => void
  onUpload: (file: File) => void
}

export function DatasetPicker({ datasets, selectedDataset, uploadedName, onSelectDataset, onSelectUpload, onUpload }: DatasetPickerProps) {
  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (file) onUpload(file)
    // Clear the input so choosing the same file again still fires onChange.
    event.target.value = ''
  }

  return (
    <div className="field">
      <div className="field-label-row">
        <label className="field-label" htmlFor="dataset-select">
          Dataset
        </label>
        <label className="upload-link">
          upload a CSV
          <input type="file" accept=".csv,text/csv" onChange={handleFileChange} hidden />
        </label>
      </div>

      <select
        id="dataset-select"
        value={selectedDataset || UPLOADED}
        onChange={(event) => {
          if (event.target.value === UPLOADED) onSelectUpload()
          else onSelectDataset(event.target.value)
        }}
      >
        {datasets.map((dataset) => (
          <option key={dataset} value={dataset}>
            {dataset}
          </option>
        ))}
        {uploadedName && <option value={UPLOADED}>{uploadedName} (uploaded)</option>}
      </select>
    </div>
  )
}
