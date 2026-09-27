import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from './api'
import { displayValue, formatDate, formatNumber, titleCase } from './format'
import Visualizations from './Visualizations'

const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'profile', label: 'Profile' },
  { id: 'quality', label: 'Quality' },
  { id: 'anomalies', label: 'Anomalies' },
  { id: 'visualizations', label: 'Visualizations' },
]
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true'
const DATASET_ORDER_KEY = 'data-quality-dataset-order-v1'
const SEVERITY_ORDER = { high: 0, medium: 1, low: 2, info: 3 }
const METHOD_DESCRIPTIONS = {
  iqr: 'Compares each numeric value with the usual middle range.',
  z_score: 'Checks how far a numeric value is from the average.',
  isolation_forest: 'Fits this dataset’s numeric rows and flags unusual combinations.',
}

function dimensionLabel(name) {
  return name === 'validity' || name === 'consistency' ? `Retail ${name}` : titleCase(name)
}

function priorityIssues(issues) {
  return [...issues].sort((a, b) =>
    (SEVERITY_ORDER[a.severity] ?? 4) - (SEVERITY_ORDER[b.severity] ?? 4)
      || (b.affected_records ?? 0) - (a.affected_records ?? 0))
}

function savedDatasetOrder() {
  try {
    const ids = JSON.parse(localStorage.getItem(DATASET_ORDER_KEY) || '[]')
    return Array.isArray(ids) ? ids.filter(Number.isInteger) : []
  } catch {
    return []
  }
}

function orderDatasets(items) {
  const positions = new Map(savedDatasetOrder().map((id, index) => [id, index]))
  return [...items].sort((a, b) =>
    (positions.get(a.id) ?? Infinity) - (positions.get(b.id) ?? Infinity) || b.id - a.id
  )
}

function reportFileName(fileName) {
  const sourceName = fileName.split(/[\\/]/).pop() || ''
  const stem = sourceName.replace(/\.(csv|xlsx)$/i, '').replace(/[<>:"/\\|?*\x00-\x1f]/g, '_').replace(/^[ .]+|[ .]+$/g, '').slice(0, 100)
  return `Data Quality Report - ${stem || 'Dataset'}.pdf`
}

function LoadingBlock({ label = 'Loading data…' }) {
  return <div className="loading-block" role="status"><span className="spinner" />{label}</div>
}

function ErrorBlock({ message, retry }) {
  return (
    <div className="error-block" role="alert">
      <div><strong>Could not load this section.</strong><p>{message}</p></div>
      {retry && <button className="button button-outline" onClick={retry}>Try again</button>}
    </div>
  )
}

function EmptyBlock({ title, children }) {
  return <div className="empty-block"><span className="empty-icon">◌</span><h3>{title}</h3><p>{children}</p></div>
}

function StatCard({ label, value, detail, tone = '' }) {
  return (
    <div className={`stat-card ${tone}`}>
      <span className="eyebrow">{label}</span>
      <strong>{value}</strong>
      {detail && <span className="stat-detail">{detail}</span>}
    </div>
  )
}

function Sidebar({ datasets, selectedId, onSelect, onReorder, loading, error, reload, file, setFile, uploading, uploadError, onUpload, search, setSearch, confirmClear, setConfirmClear, clearing, clearError, onClear, removeId, setRemoveId, removingId, removeError, onRemove }) {
  const [draggingId, setDraggingId] = useState(null)
  const [overId, setOverId] = useState(null)
  const pointerDrag = useRef(null)
  const filtered = datasets.filter((dataset) =>
    dataset.file_name.toLowerCase().includes(search.toLowerCase())
  )

  function dragTarget(event) {
    const entry = document.elementFromPoint(event.clientX, event.clientY)?.closest('[data-dataset-id]')
    return entry ? Number(entry.dataset.datasetId) : null
  }

  function finishPointerDrag(event) {
    const drag = pointerDrag.current
    if (!drag) return
    const targetId = dragTarget(event)
    if (drag.started && targetId !== null) onReorder(drag.id, targetId)
    pointerDrag.current = null
    setDraggingId(null)
    setOverId(null)
  }

  return (
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark">DQ</div><div><strong>Data Quality</strong><span>Studio</span></div></div>
      <div className="sidebar-heading"><span>Datasets</span><span className="count-pill">{datasets.length}</span></div>
      {(datasets.length > 1 || search) && <label className="search-wrap">
        <span className="sr-only">Search datasets</span>
        <svg aria-hidden="true" viewBox="0 0 24 24" fill="none"><circle cx="10.75" cy="10.75" r="6.25" stroke="currentColor" strokeWidth="1.8" /><path d="m15.5 15.5 4.25 4.25" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" /></svg>
        <input type="search" placeholder="Search datasets" value={search} onChange={(event) => setSearch(event.target.value)} />
      </label>}

      {datasets.length > 1 && <p className="sort-hint">{search ? 'Clear search to rearrange datasets.' : 'Drag the handle to rearrange. Arrow keys work too.'}</p>}
      <div className="dataset-list" aria-label="Datasets">
        {loading && <div className="sidebar-message">Loading datasets…</div>}
        {error && <div className="sidebar-message sidebar-error">{error}<button onClick={reload}>Retry</button></div>}
        {!loading && !error && filtered.length === 0 && <div className="sidebar-message">{datasets.length ? 'No matching datasets.' : 'No datasets yet. Upload one below.'}</div>}
        {filtered.map((dataset) => (
          <div className={`dataset-entry ${selectedId === dataset.id ? 'selected' : ''} ${overId === dataset.id && draggingId !== dataset.id ? 'drop-target' : ''}`} key={dataset.id} data-dataset-id={dataset.id}>
            <div className="dataset-row">
              {datasets.length > 1 && !search && <button className="dataset-drag" type="button"
                aria-label={`Rearrange ${dataset.file_name}; drag or use arrow keys`}
                title="Drag to rearrange, or use arrow keys"
                onPointerDown={(event) => {
                  if (event.button !== 0) return
                  pointerDrag.current = { id: dataset.id, x: event.clientX, y: event.clientY, started: false }
                  event.currentTarget.setPointerCapture(event.pointerId)
                }}
                onPointerMove={(event) => {
                  const drag = pointerDrag.current
                  if (!drag || drag.id !== dataset.id) return
                  if (!drag.started && Math.hypot(event.clientX - drag.x, event.clientY - drag.y) < 5) return
                  drag.started = true
                  setDraggingId(dataset.id)
                  setOverId(dragTarget(event))
                }}
                onPointerUp={finishPointerDrag}
                onPointerCancel={() => { pointerDrag.current = null; setDraggingId(null); setOverId(null) }}
                onKeyDown={(event) => {
                  if (event.key !== 'ArrowUp' && event.key !== 'ArrowDown') return
                  event.preventDefault()
                  const index = datasets.findIndex((item) => item.id === dataset.id)
                  const neighbor = datasets[index + (event.key === 'ArrowUp' ? -1 : 1)]
                  if (neighbor) onReorder(dataset.id, neighbor.id)
                }}>⠿</button>}
              <button className={`dataset-item ${selectedId === dataset.id ? 'selected' : ''}`} onClick={() => onSelect(dataset.id)} aria-current={selectedId === dataset.id ? 'true' : undefined}>
                <span className="dataset-icon">▦</span>
                <span className="dataset-text"><strong title={dataset.file_name}>{dataset.file_name}</strong><small>{formatNumber(dataset.rows_count, 0)} rows</small></span>
              </button>
              {!DEMO_MODE && <button className="dataset-remove" aria-label={`Remove ${dataset.file_name}`} title={`Remove ${dataset.file_name}`} onClick={() => setRemoveId(dataset.id)} disabled={removingId !== null}>×</button>}
            </div>
            {removeId === dataset.id && <div className="dataset-remove-confirm">
              <p>Remove {dataset.file_name} and identical saved copies?</p>
              <div><button onClick={() => setRemoveId(null)} disabled={removingId !== null}>Cancel</button><button className="history-delete" onClick={() => onRemove(dataset.id)} disabled={removingId !== null}>{removingId === dataset.id ? 'Removing…' : 'Remove'}</button></div>
              {removeError && <p className="history-error" role="alert">{removeError}</p>}
            </div>}
          </div>
        ))}
      </div>

      {!DEMO_MODE && <div className="history-actions">
        {!confirmClear ? <button className="history-link" onClick={() => setConfirmClear(true)} disabled={clearing}>Clear history</button> : <div className="history-confirm">
          <strong>Clear all saved datasets?</strong>
          <p>This deletes local uploads and saved records, including older entries hidden from this list.</p>
          <div><button onClick={() => setConfirmClear(false)} disabled={clearing}>Cancel</button><button className="history-delete" onClick={onClear} disabled={clearing}>{clearing ? 'Clearing…' : 'Delete all'}</button></div>
        </div>}
        {clearError && <p className="history-error" role="alert">{clearError}</p>}
      </div>}

      {DEMO_MODE ? <div className="sidebar-message demo-note">Public sample demo. Uploads are available when you run the project locally.</div> : <form className="upload-card" onSubmit={onUpload}>
        <span className="upload-symbol" aria-hidden="true">↥</span>
        <strong>Add a dataset</strong>
        <p>CSV or Excel (.xlsx). Your file stays on the local backend.</p>
        <label className="file-picker">
          <span>{file ? file.name : 'Choose a file'}</span>
          <input type="file" accept=".csv,.xlsx" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
        </label>
        <button className="button button-primary upload-button" type="submit" disabled={!file || uploading}>{uploading ? 'Uploading…' : 'Upload dataset'}</button>
        {uploadError && <p className="upload-error" role="alert">{uploadError}</p>}
      </form>}
      <div className="sidebar-footer">Structured data, clearer decisions.</div>
    </aside>
  )
}

function Overview({ dataset, qualityState, onNavigate, onRetryQuality, onReport, reporting, reportError }) {
  const quality = qualityState.data
  const issues = priorityIssues(quality?.issues ?? [])
  const highIssues = issues.filter((issue) => issue.severity === 'high')
  const evaluatedChecks = quality ? Object.values(quality.dimensions).filter((dimension) => dimension.score !== null).length : 0
  return (
    <div className="section-stack">
      <section className="hero-panel">
        <div><span className="hero-kicker">CURRENT DATASET</span><h2>{dataset.file_name}</h2><p>General profiling and anomaly checks work across datasets. Retail rules run when their required columns are present.</p></div>
        <div className="hero-actions"><button className="button report-button" onClick={onReport} disabled={reporting}>{reporting ? 'Preparing PDF…' : 'Download PDF report'}</button>{reportError && <p role="alert" className="report-error">{reportError}</p>}</div>
      </section>
      <div className="stats-grid">
        <StatCard label="ROWS" value={formatNumber(dataset.rows_count, 0)} detail="Stored records" />
        <StatCard label="COLUMNS" value={formatNumber(dataset.columns_count, 0)} detail="Detected fields" />
        <StatCard label="RULE SCORE" value={quality ? formatNumber(quality.overall_quality_score) : qualityState.loading ? '…' : '—'} detail={quality?.quality_grade ? `${titleCase(quality.quality_grade)} · ${evaluatedChecks} of ${Object.keys(quality.dimensions).length} checks` : 'From available checks'} tone="stat-emphasis" />
        <StatCard label={DEMO_MODE ? 'SAMPLE READY' : 'UPLOADED'} value={formatDate(dataset.uploaded_at)} detail={DEMO_MODE ? 'Public reference data' : 'Local storage'} />
      </div>
      {highIssues.length > 0 && <div className="score-caution" role="note"><strong>{highIssues.length} high-severity finding{highIssues.length === 1 ? '' : 's'} need review despite the score.</strong> The rule score does not know which fields your task requires. <button className="text-button" onClick={() => onNavigate('quality')}>See findings →</button></div>}
      {qualityState.error && <ErrorBlock message={qualityState.error} retry={onRetryQuality} />}
      <div className="overview-grid">
        <section className="panel">
          <div className="panel-head"><div><span className="eyebrow">ASSESSMENT</span><h3>Quality at a glance</h3></div><button className="text-button" onClick={() => onNavigate('quality')}>View details →</button></div>
          {qualityState.loading ? <LoadingBlock label="Assessing quality…" /> : quality ? (
            <div className="dimension-list">
              {Object.entries(quality.dimensions).map(([name, dimension]) => (
                <div className="dimension-row" key={name}><span>{dimensionLabel(name)}</span>{dimension.score === null ? <span className="dimension-unevaluated">Excluded</span> : <div className="mini-track"><span style={{ width: `${dimension.score}%` }} /></div>}<strong title={dimension.reason}>{dimension.score === null ? 'Not evaluated' : `${formatNumber(dimension.score)} / 100`}</strong></div>
              ))}
            </div>
          ) : !qualityState.error ? <EmptyBlock title="No quality result">Select a dataset to begin.</EmptyBlock> : null}
        </section>
        <section className="panel">
          <div className="panel-head"><div><span className="eyebrow">WHAT TO REVIEW</span><h3>Leading findings</h3></div><span className="subtle-count">{issues.length} total</span></div>
          {qualityState.loading ? <LoadingBlock label="Finding issues…" /> : issues.length ? (
            <div className="finding-list">{issues.slice(0, 3).map((issue, index) => <div className={`finding finding-${issue.severity}`} key={`${issue.dimension}-${index}`}><span className={`severity-dot ${issue.severity}`} aria-hidden="true" /><div><strong>{dimensionLabel(issue.dimension)} · {titleCase(issue.severity)}</strong><p>{issue.message}</p></div></div>)}</div>
          ) : qualityState.error ? <p className="muted">Quality findings are unavailable for this dataset.</p> : <EmptyBlock title="No issues reported">Available quality checks did not report issues.</EmptyBlock>}
        </section>
      </div>
    </div>
  )
}

function Profile({ state, retry }) {
  if (state.loading) return <LoadingBlock label="Profiling the dataset…" />
  if (state.error) return <ErrorBlock message={state.error} retry={retry} />
  if (!state.data) return null
  const profile = state.data
  return (
    <div className="section-stack">
      <div className="section-intro"><span className="eyebrow">STRUCTURE</span><h2>Dataset profile</h2><p>See how each column is shaped before drawing conclusions from it.</p></div>
      <div className="stats-grid three"><StatCard label="DATA ROWS" value={formatNumber(profile.rows_count, 0)} /><StatCard label="MISSING CELLS" value={formatNumber(profile.total_missing_values, 0)} detail={`${profile.columns_with_missing_values} columns affected`} /><StatCard label="DUPLICATE ROWS" value={formatNumber(profile.duplicate_rows_count, 0)} /></div>
      <section className="panel table-panel"><div className="panel-head"><div><span className="eyebrow">COLUMN INVENTORY</span><h3>{profile.columns_count} fields</h3></div></div>
        <div className="table-scroll"><table><thead><tr><th>Column</th><th>Logical type</th><th>Missing</th><th>Unique</th><th>Details</th></tr></thead><tbody>{profile.columns.map((column) => (
          <tr key={column.name}><td><strong>{column.name}</strong><small className="cell-note">{column.data_type}</small></td><td><span className="type-pill">{column.logical_type}</span></td><td>{formatNumber(column.missing_count, 0)} <small>({formatNumber(column.missing_percentage)}%)</small></td><td>{formatNumber(column.unique_count, 0)}</td><td><details><summary>Inspect</summary><div className="column-detail">
            <p><strong>Samples:</strong> {column.sample_values?.length ? column.sample_values.map(displayValue).join(', ') : 'No nonmissing samples'}</p>
            {column.statistics && <p><strong>Numeric range:</strong> {displayValue(column.statistics.min)} to {displayValue(column.statistics.max)} · Mean {displayValue(column.statistics.mean)}</p>}
            {column.date_range && <p><strong>Date range:</strong> {displayValue(column.date_range.minimum)} to {displayValue(column.date_range.maximum)}</p>}
            {column.top_values && <p><strong>Common values:</strong> {column.top_values.map((item) => `${displayValue(item.value)} (${formatNumber(item.count, 0)})`).join(', ')}</p>}
          </div></details></td></tr>
        ))}</tbody></table></div>
      </section>
    </div>
  )
}

function Quality({ state, retry }) {
  if (state.loading) return <LoadingBlock label="Assessing data quality…" />
  if (state.error) return <ErrorBlock message={state.error} retry={retry} />
  if (!state.data) return null
  const quality = state.data
  const issues = priorityIssues(quality.issues)
  const highIssues = issues.filter((issue) => issue.severity === 'high')
  const evaluatedChecks = Object.values(quality.dimensions).filter((dimension) => dimension.score !== null).length
  return (
    <div className="section-stack">
      <div className="section-intro"><span className="eyebrow">EVIDENCE-BASED SCORE</span><h2>Data quality</h2><p>The score summarizes available checks. Each issue below shows what contributed to it.</p></div>
      <section className="score-banner"><div><span className="eyebrow">AVAILABLE RULE SCORE</span><div className="score-line"><strong>{quality.overall_quality_score === null ? '—' : formatNumber(quality.overall_quality_score)}</strong><span>/ 100</span></div><span className="grade-pill">{quality.quality_grade ? `${titleCase(quality.quality_grade)} by configured checks` : 'Not graded'}</span></div><p><strong>{evaluatedChecks} of {Object.keys(quality.dimensions).length} checks evaluated.</strong> {quality.score_breakdown ? `Half weighted average (${formatNumber(quality.score_breakdown.weighted_mean)}) plus half the lowest evaluated check (${dimensionLabel(quality.score_breakdown.limiting_dimension)}: ${formatNumber(quality.score_breakdown.limiting_dimension_score)}).` : 'No quality check could be evaluated.'} Retail checks are excluded when their fields are absent.</p></section>
      {highIssues.length > 0 && <div className="score-caution" role="note"><strong>{highIssues.length} high-severity finding{highIssues.length === 1 ? '' : 's'} need review regardless of the score.</strong> {highIssues[0].message}</div>}
      <div className="quality-grid">{Object.entries(quality.dimensions).map(([name, dimension]) => <div className="quality-card" key={name}><div className="quality-card-top"><span>{dimensionLabel(name)}</span><small>{dimension.score === null ? 'Excluded from score' : `Base weight ${formatNumber((quality.weights?.[name] ?? 0) * 100, 0)}%`}</small></div><strong>{dimension.score === null ? 'Not evaluated' : `${formatNumber(dimension.score)} / 100`}</strong>{dimension.score !== null && <div className="quality-track"><span style={{ width: `${dimension.score}%` }} /></div>}{name === 'completeness' && dimension.worst_column ? <p>Filled-cell score {formatNumber(dimension.cell_coverage_score)} · {dimension.worst_column} is {formatNumber(dimension.worst_column_missing_percentage)}% blank · extra deduction {formatNumber(dimension.concentration_penalty)} points (max 15).</p> : dimension.reason && <p>{dimension.reason}</p>}</div>)}</div>
      <section className="panel"><div className="panel-head"><div><span className="eyebrow">FINDINGS</span><h3>Issues and review items</h3></div><span className="subtle-count">{issues.length} findings</span></div>{issues.length ? <div className="issue-list">{issues.map((issue, index) => <div className="issue-row" key={`${issue.dimension}-${index}`}><span className={`severity-label severity-${issue.severity}`}>{titleCase(issue.severity)}</span><div><strong>{dimensionLabel(issue.dimension)}{issue.column ? ` · ${issue.column}` : ''}</strong><p>{issue.message}</p></div><span className="issue-count">{formatNumber(issue.affected_records, 0)} affected</span></div>)}</div> : <EmptyBlock title="No issues reported">The available rules did not find any issues in this dataset.</EmptyBlock>}</section>
    </div>
  )
}

function Explanation({ explanation, onClose }) {
  return <section className="explanation-panel" aria-label={`Explanation for row ${explanation.row_number}`}><div className="panel-head"><div><span className="eyebrow">ROW EXPLANATION</span><h3>Row {formatNumber(explanation.row_number, 0)}</h3></div><button className="icon-button" onClick={onClose} aria-label="Close explanation">×</button></div>
    <div className="explanation-status"><span className={`status-pill status-${explanation.status}`}>{titleCase(explanation.status)}</span><span className="category-label">{titleCase(explanation.interpretation.category)}</span></div>
    <p className="interpretation">{explanation.interpretation.message}</p><p className="next-step"><strong>Next check:</strong> {explanation.interpretation.next_step}</p>
    <div className="value-grid">{Object.entries(explanation.values).map(([name, value]) => <div key={name}><span>{name}</span><strong>{displayValue(value)}</strong></div>)}{explanation.invoice_number && <div><span>Invoice</span><strong>{displayValue(explanation.invoice_number)}</strong></div>}</div>
    <h4>Method evidence</h4>{explanation.method_evidence.length ? <div className="evidence-list">{explanation.method_evidence.map((evidence, index) => <div className="evidence-item" key={`${evidence.method}-${index}`}><span className="method-pill">{titleCase(evidence.method)}</span><p>{evidence.message}</p>{evidence.field ? <small>Observed {displayValue(evidence.observed_value)} · {evidence.direction} boundary {displayValue(evidence.boundary)} · distance {displayValue(evidence.distance_from_boundary)}</small> : <small>Model score {displayValue(evidence.score)} · flagged below {displayValue(evidence.flagged_when_below)}</small>}</div>)}</div> : <p className="muted">{explanation.status === 'not_evaluated' ? 'No anomaly method could evaluate this dataset.' : 'No anomaly method flagged this row. This does not certify the record as correct.'}</p>}
  </section>
}

function Anomalies({ state, retry, onPage, explanation, explanationLoading, explanationError, onExplain, onCloseExplanation, rowInput, setRowInput, onLookup }) {
  const explanationRef = useRef(null)
  useEffect(() => {
    if (explanationLoading || explanationError || explanation) {
      explanationRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [explanationLoading, explanationError, explanation])
  if (state.loading) return <LoadingBlock label="Detecting unusual records…" />
  if (state.error) return <ErrorBlock message={state.error} retry={retry} />
  if (!state.data) return null
  const result = state.data
  return <div className="section-stack"><div className="section-intro"><span className="eyebrow">UNUSUAL OBSERVATIONS</span><h2>Anomaly review</h2><p>An unusual record is a lead for investigation, not proof of a data-quality error.</p></div>
    <div className="stats-grid three"><StatCard label="FLAGGED ROWS" value={formatNumber(result.anomaly_rows_count, 0)} detail={`Of ${formatNumber(result.rows_count, 0)} data rows`} tone="stat-emphasis" /><StatCard label="POSSIBLE RETURNS" value={result.retail_context ? formatNumber(result.retail_context.flagged_negative_quantity_with_cancellation, 0) : '—'} detail="Negative quantity with cancellation marker" /><StatCard label="REVIEW NEGATIVE QTY" value={result.retail_context ? formatNumber(result.retail_context.flagged_negative_quantity_without_cancellation, 0) : '—'} detail="Without cancellation marker" /></div>
    {result.status === 'not_evaluated' && <EmptyBlock title="Anomaly checks were not evaluated">This dataset needs usable numeric fields. Check the method notes below.</EmptyBlock>}
    <section className="panel"><div className="panel-head"><div><span className="eyebrow">METHODS</span><h3>How rows were checked</h3></div></div><p className="method-note">IQR and Z-score are statistical checks. Isolation Forest is fitted to this dataset when enough numeric rows exist. The next-step suggestions come from explicit rules, not a language model.</p><div className="method-summary">{Object.entries(result.methods).map(([name, method]) => <div key={name}><strong>{titleCase(name)}</strong><span>{method.status === 'evaluated' ? name === 'isolation_forest' ? `${formatNumber(method.flagged_rows, 0)} flags · ${method.fields.join(', ')}` : `${Object.values(method.fields).filter((field) => field.status === 'evaluated').length} fields assessed` : method.reason || 'Not evaluated'}</span><p>{METHOD_DESCRIPTIONS[name]}</p></div>)}</div></section>
    <section className="panel table-panel"><div className="panel-head"><div><span className="eyebrow">FLAGGED RECORDS</span><h3>Review queue</h3></div><form className="row-lookup" onSubmit={onLookup}><label htmlFor="row-number">Source row</label><input id="row-number" type="number" min="1" max={result.rows_count} value={rowInput} onChange={(event) => setRowInput(event.target.value)} placeholder="#" /><button className="button button-outline" type="submit">Explain</button></form></div>
      <p className="queue-note">Priority order: more anomaly signals first, then the model score. Row # is the position in the uploaded data, excluding the header. Explanations cover numeric anomaly signals; missing fields appear in Profile and Quality.</p>
      <div className="explanation-response" ref={explanationRef} aria-live="polite">
        {explanationLoading && <LoadingBlock label="Explaining row…" />}{explanationError && <ErrorBlock message={explanationError} />}{explanation && <Explanation explanation={explanation} onClose={onCloseExplanation} />}
      </div>
      {result.examples.length ? <><div className="table-scroll"><table><thead><tr><th>Row #</th><th>Numeric values</th><th>Signals</th><th>Interpretation</th><th></th></tr></thead><tbody>{result.examples.map((example) => <tr key={example.row_number}><td><strong>#{formatNumber(example.row_number, 0)}</strong></td><td><span className="value-preview">{Object.entries(example.values).map(([name, value]) => `${name}: ${displayValue(value)}`).join(' · ')}</span></td><td>{example.signals.length} checks</td><td>{titleCase(example.interpretation.category)}</td><td><button className="text-button" onClick={() => onExplain(example.row_number)}>Explain →</button></td></tr>)}</tbody></table></div><div className="pagination"><span>Queue items {formatNumber(result.example_offset + 1, 0)}–{formatNumber(result.example_offset + result.examples.length, 0)} of {formatNumber(result.anomaly_rows_count, 0)} flagged</span><div><button className="button button-outline" disabled={result.example_offset === 0} onClick={() => onPage(Math.max(0, result.example_offset - result.example_limit))}>Previous</button><button className="button button-outline" disabled={result.next_offset === null} onClick={() => onPage(result.next_offset)}>Next</button></div></div></> : <EmptyBlock title="No rows on this page">Choose a previous page or inspect a specific row number.</EmptyBlock>}
    </section>
  </div>
}

export default function App() {
  const [datasets, setDatasets] = useState([])
  const [orderReady, setOrderReady] = useState(false)
  const [selectedId, setSelectedId] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [search, setSearch] = useState('')
  const [listLoading, setListLoading] = useState(true)
  const [listError, setListError] = useState('')
  const [listReload, setListReload] = useState(0)
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [confirmClear, setConfirmClear] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [clearError, setClearError] = useState('')
  const [removeId, setRemoveId] = useState(null)
  const [removingId, setRemovingId] = useState(null)
  const [removeError, setRemoveError] = useState('')
  const [notice, setNotice] = useState('')
  const [reporting, setReporting] = useState(false)
  const [reportError, setReportError] = useState('')
  const [qualityState, setQualityState] = useState({ data: null, loading: false, error: '' })
  const [qualityReload, setQualityReload] = useState(0)
  const [profileState, setProfileState] = useState({ data: null, loading: false, error: '' })
  const [anomalyState, setAnomalyState] = useState({ data: null, loading: false, error: '' })
  const [visualAnomalyState, setVisualAnomalyState] = useState({ data: null, loading: false, error: '' })
  const [pageOffset, setPageOffset] = useState(0)
  const [rowInput, setRowInput] = useState('')
  const [explanation, setExplanation] = useState(null)
  const [explanationLoading, setExplanationLoading] = useState(false)
  const [explanationError, setExplanationError] = useState('')
  const [profileReload, setProfileReload] = useState(0)
  const [anomalyReload, setAnomalyReload] = useState(0)
  const [visualAnomalyReload, setVisualAnomalyReload] = useState(0)
  const profileCache = useRef(new Map())
  const anomalyCache = useRef(new Map())
  const visualAnomalyCache = useRef(new Map())
  const explanationController = useRef(null)

  useEffect(() => {
    let active = true
    setListLoading(true)
    setListError('')
    api.datasets().then((items) => {
      if (!active) return
      const sorted = orderDatasets(items)
      setDatasets(sorted)
      setSelectedId((current) => sorted.some((item) => item.id === current) ? current : sorted[0]?.id ?? null)
      setOrderReady(true)
    }).catch((error) => { if (active) setListError(error.message) }).finally(() => { if (active) setListLoading(false) })
    return () => { active = false }
  }, [listReload])

  useEffect(() => {
    if (!orderReady) return
    try {
      localStorage.setItem(DATASET_ORDER_KEY, JSON.stringify(datasets.map((item) => item.id)))
    } catch {
      // The list still works when browser storage is unavailable.
    }
  }, [datasets, orderReady])

  useEffect(() => {
    if (selectedId === null) return
    setProfileState({ data: null, loading: false, error: '' })
    setAnomalyState({ data: null, loading: false, error: '' })
    setVisualAnomalyState({ data: null, loading: false, error: '' })
    setExplanation(null)
    setExplanationLoading(false)
    setExplanationError('')
  }, [selectedId])

  useEffect(() => {
    if (selectedId === null) return
    const controller = new AbortController()
    setQualityState({ data: null, loading: true, error: '' })
    api.quality(selectedId, controller.signal).then((data) => setQualityState({ data, loading: false, error: '' })).catch((error) => {
      if (error.name !== 'AbortError') setQualityState({ data: null, loading: false, error: error.message })
    })
    return () => { controller.abort(); explanationController.current?.abort() }
  }, [selectedId, qualityReload])

  useEffect(() => {
    if (selectedId === null || !['profile', 'visualizations'].includes(activeTab)) return
    const key = `${selectedId}:${profileReload}`
    const cached = profileCache.current.get(key)
    if (cached) { setProfileState({ data: cached, loading: false, error: '' }); return }
    const controller = new AbortController()
    setProfileState({ data: null, loading: true, error: '' })
    api.profile(selectedId, controller.signal).then((data) => {
      profileCache.current.set(key, data)
      setProfileState({ data, loading: false, error: '' })
    }).catch((error) => { if (error.name !== 'AbortError') setProfileState({ data: null, loading: false, error: error.message }) })
    return () => controller.abort()
  }, [selectedId, activeTab, profileReload])

  useEffect(() => {
    if (selectedId === null || activeTab !== 'anomalies') return
    const key = `${selectedId}:${pageOffset}:${anomalyReload}`
    const cached = anomalyCache.current.get(key)
    if (cached) { setAnomalyState({ data: cached, loading: false, error: '' }); return }
    const controller = new AbortController()
    setAnomalyState({ data: null, loading: true, error: '' })
    api.anomalies(selectedId, pageOffset, 20, controller.signal).then((data) => {
      anomalyCache.current.set(key, data)
      setAnomalyState({ data, loading: false, error: '' })
    }).catch((error) => { if (error.name !== 'AbortError') setAnomalyState({ data: null, loading: false, error: error.message }) })
    return () => controller.abort()
  }, [selectedId, activeTab, pageOffset, anomalyReload])

  useEffect(() => {
    if (selectedId === null || activeTab !== 'visualizations') return
    const key = `${selectedId}:${visualAnomalyReload}`
    const cached = visualAnomalyCache.current.get(key)
    if (cached) { setVisualAnomalyState({ data: cached, loading: false, error: '' }); return }
    const controller = new AbortController()
    setVisualAnomalyState({ data: null, loading: true, error: '' })
    api.anomalies(selectedId, 0, 1, controller.signal).then((data) => {
      visualAnomalyCache.current.set(key, data)
      setVisualAnomalyState({ data, loading: false, error: '' })
    }).catch((error) => {
      if (error.name !== 'AbortError') setVisualAnomalyState({ data: null, loading: false, error: error.message })
    })
    return () => controller.abort()
  }, [selectedId, activeTab, visualAnomalyReload])

  const selectedDataset = useMemo(() => datasets.find((item) => item.id === selectedId), [datasets, selectedId])

  function chooseDataset(id) {
    setSelectedId(id)
    setActiveTab('overview')
    setPageOffset(0)
    setRowInput('')
    setNotice('')
    setReportError('')
  }

  function reorderDataset(sourceId, targetId) {
    if (sourceId === targetId) return
    setDatasets((current) => {
      const sourceIndex = current.findIndex((item) => item.id === sourceId)
      const targetIndex = current.findIndex((item) => item.id === targetId)
      if (sourceIndex < 0 || targetIndex < 0) return current
      const reordered = [...current]
      const [moved] = reordered.splice(sourceIndex, 1)
      reordered.splice(targetIndex, 0, moved)
      return reordered
    })
  }

  async function handleClearHistory() {
    setClearing(true)
    setClearError('')
    try {
      const result = await api.clearHistory()
      setDatasets([])
      setSelectedId(null)
      setSearch('')
      setFile(null)
      setConfirmClear(false)
      profileCache.current.clear()
      anomalyCache.current.clear()
      visualAnomalyCache.current.clear()
      setNotice(`${result.deleted_records} saved dataset records removed.${result.file_errors ? ` ${result.file_errors} upload files could not be removed.` : ''}`)
    } catch (error) {
      setClearError(error.message)
    } finally {
      setClearing(false)
    }
  }

  async function handleRemoveDataset(id) {
    setRemovingId(id)
    setRemoveError('')
    try {
      const result = await api.removeDataset(id)
      const remaining = datasets.filter((dataset) => dataset.id !== id)
      setDatasets(remaining)
      if (selectedId === id) {
        setSelectedId(remaining[0]?.id ?? null)
        setActiveTab('overview')
      }
      setRemoveId(null)
      setNotice(`${result.deleted_records} saved record${result.deleted_records === 1 ? '' : 's'} removed.${result.file_errors ? ` ${result.file_errors} upload files could not be removed.` : ''}`)
      setListReload((value) => value + 1)
    } catch (error) {
      setRemoveError(error.message)
    } finally {
      setRemovingId(null)
    }
  }

  async function handleReport() {
    if (!selectedId || reporting) return
    const reportId = selectedId
    const reportName = reportFileName(selectedDataset.file_name)
    setReporting(true)
    setReportError('')
    try {
      const blob = await api.report(reportId)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = reportName
      document.body.appendChild(link)
      link.click()
      link.remove()
      setTimeout(() => URL.revokeObjectURL(url), 60_000)
    } catch (error) {
      setReportError(error.message)
    } finally {
      setReporting(false)
    }
  }

  async function handleUpload(event) {
    event.preventDefault()
    if (!file) return
    const formElement = event.currentTarget
    setUploading(true)
    setUploadError('')
    setNotice('')
    try {
      const created = await api.upload(file)
      const alreadySaved = datasets.some((dataset) => dataset.id === created.id)
      setDatasets((current) => current.some((item) => item.id === created.id) ? current : [...current, created])
      chooseDataset(created.id)
      setFile(null)
      formElement.reset()
      setNotice(alreadySaved ? `${created.file_name} is already saved. Showing its existing analysis.` : `${created.file_name} uploaded and ready to inspect.`)
    } catch (error) {
      setUploadError(error.message)
    } finally {
      setUploading(false)
    }
  }

  async function explainRow(rowNumber) {
    if (!selectedId) return
    explanationController.current?.abort()
    const controller = new AbortController()
    explanationController.current = controller
    setExplanation(null)
    setExplanationError('')
    setExplanationLoading(true)
    try {
      const result = await api.explanation(selectedId, rowNumber, controller.signal)
      if (!controller.signal.aborted) setExplanation(result)
    } catch (error) {
      if (error.name !== 'AbortError') setExplanationError(error.message)
    } finally {
      if (!controller.signal.aborted) setExplanationLoading(false)
    }
  }

  function handleLookup(event) {
    event.preventDefault()
    const value = Number(rowInput)
    if (!Number.isInteger(value) || value < 1 || value > (anomalyState.data?.rows_count ?? 0)) {
      setExplanationError('Enter a valid data-row number for this dataset.')
      return
    }
    explainRow(value)
  }

  return <div className="app-shell">
    <Sidebar datasets={datasets} selectedId={selectedId} onSelect={chooseDataset} onReorder={reorderDataset} loading={listLoading} error={listError} reload={() => setListReload((value) => value + 1)} file={file} setFile={setFile} uploading={uploading} uploadError={uploadError} onUpload={handleUpload} search={search} setSearch={setSearch} confirmClear={confirmClear} setConfirmClear={setConfirmClear} clearing={clearing} clearError={clearError} onClear={handleClearHistory} removeId={removeId} setRemoveId={(id) => { setRemoveId(id); setRemoveError('') }} removingId={removingId} removeError={removeError} onRemove={handleRemoveDataset} />
    <main className="main-content">
      <header className="topbar"><div><span className="eyebrow">INTELLIGENT DATA QUALITY FRAMEWORK</span><h1>Dataset review</h1></div></header>
      {notice && <div className="success-notice" role="status">✓ {notice}<button onClick={() => setNotice('')} aria-label="Dismiss notification">×</button></div>}
      {!selectedDataset ? listLoading ? <LoadingBlock label="Opening workspace…" /> : listError ? <ErrorBlock message={listError} retry={() => setListReload((value) => value + 1)} /> : <EmptyBlock title={DEMO_MODE ? 'Sample unavailable' : 'Your workspace is ready'}>{DEMO_MODE ? 'Try again shortly. The free demo API may be waking up.' : 'Upload a CSV or Excel dataset to start exploring its quality.'}</EmptyBlock> : <>
        <nav className="tabs" aria-label="Dataset sections">{TABS.map((tab) => <button key={tab.id} className={activeTab === tab.id ? 'active' : ''} onClick={() => setActiveTab(tab.id)} aria-current={activeTab === tab.id ? 'page' : undefined}>{tab.label}</button>)}</nav>
        {activeTab === 'overview' && <Overview dataset={selectedDataset} qualityState={qualityState} onNavigate={setActiveTab} onRetryQuality={() => setQualityReload((value) => value + 1)} onReport={handleReport} reporting={reporting} reportError={reportError} />}
        {activeTab === 'profile' && <Profile state={profileState} retry={() => setProfileReload((value) => value + 1)} />}
        {activeTab === 'quality' && <Quality state={qualityState} retry={() => setQualityReload((value) => value + 1)} />}
        {activeTab === 'anomalies' && <Anomalies state={anomalyState} retry={() => setAnomalyReload((value) => value + 1)} onPage={(offset) => { setPageOffset(offset); setExplanation(null); setExplanationError('') }} explanation={explanation} explanationLoading={explanationLoading} explanationError={explanationError} onExplain={explainRow} onCloseExplanation={() => setExplanation(null)} rowInput={rowInput} setRowInput={setRowInput} onLookup={handleLookup} />}
        {activeTab === 'visualizations' && <Visualizations datasetId={selectedId} profileState={profileState} profileRetry={() => setProfileReload((value) => value + 1)} anomalyState={visualAnomalyState} anomalyRetry={() => setVisualAnomalyReload((value) => value + 1)} />}
      </>}
      <footer className="main-footer">Anomaly flags invite review. They are not automatic data-quality errors.</footer>
    </main>
  </div>
}
