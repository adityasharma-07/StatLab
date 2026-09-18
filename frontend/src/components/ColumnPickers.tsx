import type { ColumnOption } from '../columns'

interface ColumnPickersProps {
  options: ColumnOption[]
  colA: string
  colB: string
  onChangeA: (column: string) => void
  onChangeB: (column: string) => void
}

export function ColumnPickers({ options, colA, colB, onChangeA, onChangeB }: ColumnPickersProps) {
  return (
    <>
      <ColumnSelect label="Column A" options={options} value={colA} onChange={onChangeA} />
      <ColumnSelect label="Column B" options={options} value={colB} onChange={onChangeB} />
    </>
  )
}

interface ColumnSelectProps {
  label: string
  options: ColumnOption[]
  value: string
  onChange: (column: string) => void
}

function ColumnSelect({ label, options, value, onChange }: ColumnSelectProps) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option.name} value={option.name}>
            {option.name} ({option.kind})
          </option>
        ))}
      </select>
    </label>
  )
}
