export function formatNumber(value, maximumFractionDigits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—'
  return new Intl.NumberFormat(undefined, { maximumFractionDigits }).format(Number(value))
}

export function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? String(value)
    : new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(date)
}

export function titleCase(value) {
  if (!value) return '—'
  const labels = { iqr: 'IQR', z_score: 'Z-score', isolation_forest: 'Isolation Forest' }
  if (labels[String(value).toLowerCase()]) return labels[String(value).toLowerCase()]
  return String(value).replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export function displayValue(value) {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'number') return formatNumber(value, 4)
  return String(value)
}
