interface DatasetPickerProps {
  datasets: string[]
  selected: string
  onSelect: (dataset: string) => void
}

export function DatasetPicker({ datasets, selected, onSelect }: DatasetPickerProps) {
  return (
    <label className="field">
      <span className="field-label">Dataset</span>
      <select value={selected} onChange={(event) => onSelect(event.target.value)}>
        {datasets.map((dataset) => (
          <option key={dataset} value={dataset}>
            {dataset}
          </option>
        ))}
      </select>
    </label>
  )
}
