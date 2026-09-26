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

function Sidebar({ datasets, selectedId, onSelect, loading, error, reload, file, setFile, uploading, uploadError, onUpload, search, setSearch }) {
  const filtered = datasets.filter((dataset) =>
    dataset.file_name.toLowerCase().includes(search.toLowerCase()) || String(dataset.id).includes(search)
  )

  return (
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark">DQ</div><div><strong>Data Quality</strong><span>Studio</span></div></div>
      <div className="sidebar-section-label">WORKSPACE</div>
      <div className="workspace-name"><span className="workspace-dot" /> {DEMO_MODE ? 'Public sample' : 'Local analysis'} <span className="workspace-chevron">⌄</span></div>

      <div className="sidebar-heading"><span>Datasets</span><span className="count-pill">{datasets.length}</span></div>
      <label className="search-wrap">
        <span className="sr-only">Search datasets</span>
        <span aria-hidden="true">⌕</span>
        <input type="search" placeholder="Search datasets" value={search} onChange={(event) => setSearch(event.target.value)} />
      </label>

      <div className="dataset-list" aria-label="Datasets">
        {loading && <div className="sidebar-message">Loading datasets…</div>}
        {error && <div className="sidebar-message sidebar-error">{error}<button onClick={reload}>Retry</button></div>}
        {!loading && !error && filtered.length === 0 && <div className="sidebar-message">{datasets.length ? 'No matching datasets.' : 'No datasets yet. Upload one below.'}</div>}
        {filtered.map((dataset) => (
          <button
            key={dataset.id}
            className={`dataset-item ${selectedId === dataset.id ? 'selected' : ''}`}
            onClick={() => onSelect(dataset.id)}
            aria-current={selectedId === dataset.id ? 'true' : undefined}
          >
            <span className="dataset-icon">▦</span>
            <span className="dataset-text"><strong title={dataset.file_name}>{dataset.file_name}</strong><small>{formatNumber(dataset.rows_count, 0)} rows · #{dataset.id}</small></span>
          </button>
        ))}
      </div>

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

function Overview({ dataset, qualityState, onNavigate, onReport, reporting, reportError }) {
  const quality = qualityState.data
  const issues = quality?.issues ?? []
  return (
    <div className="section-stack">
      <section className="hero-panel">
        <div><span className="hero-kicker">DATASET WORKSPACE</span><h2>{dataset.file_name}</h2><p>Start with the shape of your data, then inspect the evidence behind quality scores and unusual records.</p></div>
        <div className="hero-actions"><div className="hero-id">DATASET <strong>#{dataset.id}</strong></div><button className="button report-button" onClick={onReport} disabled={reporting}>{reporting ? 'Preparing PDF…' : 'Download PDF report'}</button>{reportError && <p role="alert" className="report-error">{reportError}</p>}</div>
      </section>
      <div className="stats-grid">
        <StatCard label="ROWS" value={formatNumber(dataset.rows_count, 0)} detail="Stored records" />
        <StatCard label="COLUMNS" value={formatNumber(dataset.columns_count, 0)} detail="Detected fields" />
        <StatCard label="QUALITY SCORE" value={quality ? formatNumber(quality.overall_quality_score) : qualityState.loading ? '…' : '—'} detail={quality ? titleCase(quality.quality_grade) : 'From available checks'} tone="stat-emphasis" />
        <StatCard label={DEMO_MODE ? 'SAMPLE READY' : 'UPLOADED'} value={formatDate(dataset.uploaded_at)} detail={DEMO_MODE ? 'Public reference data' : 'Local storage'} />
      </div>
      {qualityState.error && <ErrorBlock message={qualityState.error} />}
      <div className="overview-grid">
        <section className="panel">
          <div className="panel-head"><div><span className="eyebrow">ASSESSMENT</span><h3>Quality at a glance</h3></div><button className="text-button" onClick={() => onNavigate('quality')}>View details →</button></div>
          {qualityState.loading ? <LoadingBlock label="Assessing quality…" /> : quality ? (
            <div className="dimension-list">
              {Object.entries(quality.dimensions).map(([name, dimension]) => (
                <div className="dimension-row" key={name}><span>{titleCase(name)}</span><div className="mini-track"><span style={{ width: `${dimension.score ?? 0}%` }} /></div><strong>{dimension.score === null ? 'Not evaluated' : `${formatNumber(dimension.score)} / 100`}</strong></div>
              ))}
            </div>
          ) : !qualityState.error ? <EmptyBlock title="No quality result">Select a dataset to begin.</EmptyBlock> : null}
        </section>
        <section className="panel">
          <div className="panel-head"><div><span className="eyebrow">WHAT TO REVIEW</span><h3>Leading findings</h3></div><span className="subtle-count">{issues.length} total</span></div>
          {qualityState.loading ? <LoadingBlock label="Finding issues…" /> : issues.length ? (
            <div className="finding-list">{issues.slice(0, 3).map((issue, index) => <div className="finding" key={`${issue.dimension}-${index}`}><span className={`severity-dot ${issue.severity}`} /><div><strong>{titleCase(issue.dimension)} · {titleCase(issue.severity)}</strong><p>{issue.message}</p></div></div>)}</div>
          ) : qualityState.error ? <p className="muted">Quality findings are unavailable for this dataset.</p> : <EmptyBlock title="No issues reported">Available quality checks did not report issues.</EmptyBlock>}
        </section>
      </div>
      <div className="action-grid">
        <button className="action-card" onClick={() => onNavigate('profile')}><span className="action-icon">▥</span><strong>Explore the profile</strong><span>Types, missing values, ranges, and examples</span><b>→</b></button>
        <button className="action-card" onClick={() => onNavigate('anomalies')}><span className="action-icon">◈</span><strong>Review anomalies</strong><span>Unusual values with evidence and context</span><b>→</b></button>
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
  return (
    <div className="section-stack">
      <div className="section-intro"><span className="eyebrow">EVIDENCE-BASED SCORE</span><h2>Data quality</h2><p>The score summarizes available checks. Each issue below shows what contributed to it.</p></div>
      <section className="score-banner"><div><span className="eyebrow">OVERALL QUALITY</span><div className="score-line"><strong>{quality.overall_quality_score === null ? '—' : formatNumber(quality.overall_quality_score)}</strong><span>/ 100</span></div><span className="grade-pill">{titleCase(quality.quality_grade)}</span></div><p>Unassessed retail dimensions are excluded from the weighted score rather than treated as perfect.</p></section>
      <div className="quality-grid">{Object.entries(quality.dimensions).map(([name, dimension]) => <div className="quality-card" key={name}><div className="quality-card-top"><span>{titleCase(name)}</span><small>Weight {formatNumber((quality.weights?.[name] ?? 0) * 100, 0)}%</small></div><strong>{dimension.score === null ? 'Not evaluated' : `${formatNumber(dimension.score)} / 100`}</strong><div className="quality-track"><span style={{ width: `${dimension.score ?? 0}%` }} /></div>{dimension.reason && <p>{dimension.reason}</p>}</div>)}</div>
      <section className="panel"><div className="panel-head"><div><span className="eyebrow">FINDINGS</span><h3>Issues and review items</h3></div><span className="subtle-count">{quality.issues.length} findings</span></div>{quality.issues.length ? <div className="issue-list">{quality.issues.map((issue, index) => <div className="issue-row" key={`${issue.dimension}-${index}`}><span className={`severity-label severity-${issue.severity}`}>{titleCase(issue.severity)}</span><div><strong>{titleCase(issue.dimension)}{issue.column ? ` · ${issue.column}` : ''}</strong><p>{issue.message}</p></div><span className="issue-count">{formatNumber(issue.affected_records, 0)} affected</span></div>)}</div> : <EmptyBlock title="No issues reported">The available rules did not find any issues in this dataset.</EmptyBlock>}</section>
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
  if (state.loading) return <LoadingBlock label="Detecting unusual records…" />
  if (state.error) return <ErrorBlock message={state.error} retry={retry} />
  if (!state.data) return null
  const result = state.data
  return <div className="section-stack"><div className="section-intro"><span className="eyebrow">UNUSUAL OBSERVATIONS</span><h2>Anomaly review</h2><p>An unusual record is a lead for investigation, not proof of a data-quality error.</p></div>
    <div className="stats-grid three"><StatCard label="FLAGGED ROWS" value={formatNumber(result.anomaly_rows_count, 0)} detail={`Of ${formatNumber(result.rows_count, 0)} data rows`} tone="stat-emphasis" /><StatCard label="POSSIBLE RETURNS" value={result.retail_context ? formatNumber(result.retail_context.flagged_negative_quantity_with_cancellation, 0) : '—'} detail="Negative quantity with cancellation marker" /><StatCard label="REVIEW NEGATIVE QTY" value={result.retail_context ? formatNumber(result.retail_context.flagged_negative_quantity_without_cancellation, 0) : '—'} detail="Without cancellation marker" /></div>
    {result.status === 'not_evaluated' && <EmptyBlock title="Anomaly checks were not evaluated">This dataset needs usable numeric fields. Check the method notes below.</EmptyBlock>}
    <section className="panel"><div className="panel-head"><div><span className="eyebrow">METHODS</span><h3>How rows were checked</h3></div></div><div className="method-summary">{Object.entries(result.methods).map(([name, method]) => <div key={name}><strong>{titleCase(name)}</strong><span>{method.status === 'evaluated' ? name === 'isolation_forest' ? `${formatNumber(method.flagged_rows, 0)} flags · ${method.fields.join(', ')}` : `${Object.values(method.fields).filter((field) => field.status === 'evaluated').length} fields assessed` : method.reason || 'Not evaluated'}</span></div>)}</div></section>
    <section className="panel table-panel"><div className="panel-head"><div><span className="eyebrow">FLAGGED RECORDS</span><h3>Review queue</h3></div><form className="row-lookup" onSubmit={onLookup}><label htmlFor="row-number">Go to row</label><input id="row-number" type="number" min="1" max={result.rows_count} value={rowInput} onChange={(event) => setRowInput(event.target.value)} placeholder="#" /><button className="button button-outline" type="submit">Explain</button></form></div>
      {result.examples.length ? <><div className="table-scroll"><table><thead><tr><th>Row</th><th>Numeric values</th><th>Signals</th><th>Interpretation</th><th></th></tr></thead><tbody>{result.examples.map((example) => <tr key={example.row_number}><td><strong>#{formatNumber(example.row_number, 0)}</strong></td><td><span className="value-preview">{Object.entries(example.values).map(([name, value]) => `${name}: ${displayValue(value)}`).join(' · ')}</span></td><td>{example.signals.length} checks</td><td>{titleCase(example.interpretation.category)}</td><td><button className="text-button" onClick={() => onExplain(example.row_number)}>Explain →</button></td></tr>)}</tbody></table></div><div className="pagination"><span>Rows {formatNumber(result.example_offset + 1, 0)}–{formatNumber(result.example_offset + result.examples.length, 0)} of {formatNumber(result.anomaly_rows_count, 0)} flagged</span><div><button className="button button-outline" disabled={result.example_offset === 0} onClick={() => onPage(Math.max(0, result.example_offset - result.example_limit))}>Previous</button><button className="button button-outline" disabled={result.next_offset === null} onClick={() => onPage(result.next_offset)}>Next</button></div></div></> : <EmptyBlock title="No rows on this page">Choose a previous page or inspect a specific row number.</EmptyBlock>}
    </section>
    {explanationLoading && <LoadingBlock label="Explaining row…" />}{explanationError && <ErrorBlock message={explanationError} />}{explanation && <Explanation explanation={explanation} onClose={onCloseExplanation} />}
  </div>
}

export default function App() {
  const [datasets, setDatasets] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [search, setSearch] = useState('')
  const [listLoading, setListLoading] = useState(true)
  const [listError, setListError] = useState('')
  const [listReload, setListReload] = useState(0)
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
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
      const sorted = [...items].sort((a, b) => b.id - a.id)
      setDatasets(sorted)
      setSelectedId((current) => sorted.some((item) => item.id === current) ? current : sorted[0]?.id ?? null)
    }).catch((error) => { if (active) setListError(error.message) }).finally(() => { if (active) setListLoading(false) })
    return () => { active = false }
  }, [listReload])

  useEffect(() => {
    if (selectedId === null) return
    const controller = new AbortController()
    setQualityState({ data: null, loading: true, error: '' })
    setProfileState({ data: null, loading: false, error: '' })
    setAnomalyState({ data: null, loading: false, error: '' })
    setExplanation(null)
    setExplanationLoading(false)
    setExplanationError('')
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

  async function handleReport() {
    if (!selectedId || reporting) return
    const reportId = selectedId
    setReporting(true)
    setReportError('')
    try {
      const blob = await api.report(reportId)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `dataset-${reportId}-quality-report.pdf`
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
      setDatasets((current) => [created, ...current.filter((item) => item.id !== created.id)])
      chooseDataset(created.id)
      setFile(null)
      formElement.reset()
      setNotice(`${created.file_name} uploaded and ready to inspect.`)
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
    <Sidebar datasets={datasets} selectedId={selectedId} onSelect={chooseDataset} loading={listLoading} error={listError} reload={() => setListReload((value) => value + 1)} file={file} setFile={setFile} uploading={uploading} uploadError={uploadError} onUpload={handleUpload} search={search} setSearch={setSearch} />
    <main className="main-content">
      <header className="topbar"><div><span className="eyebrow">INTELLIGENT DATA QUALITY FRAMEWORK</span><h1>Make sense of your data.</h1><p>Profile structure, measure quality, and investigate unusual records.</p></div><div className="topbar-status"><span className="status-dot" /> {DEMO_MODE ? 'Public sample demo' : 'Local workspace'}</div></header>
      {notice && <div className="success-notice" role="status">✓ {notice}<button onClick={() => setNotice('')} aria-label="Dismiss notification">×</button></div>}
      {!selectedDataset ? listLoading ? <LoadingBlock label="Opening workspace…" /> : listError ? <ErrorBlock message={listError} retry={() => setListReload((value) => value + 1)} /> : <EmptyBlock title="Your workspace is ready">Upload a CSV or Excel dataset to start exploring its quality.</EmptyBlock> : <>
        <nav className="tabs" aria-label="Dataset sections">{TABS.map((tab) => <button key={tab.id} className={activeTab === tab.id ? 'active' : ''} onClick={() => setActiveTab(tab.id)} aria-current={activeTab === tab.id ? 'page' : undefined}>{tab.label}</button>)}</nav>
        {activeTab === 'overview' && <Overview dataset={selectedDataset} qualityState={qualityState} onNavigate={setActiveTab} onReport={handleReport} reporting={reporting} reportError={reportError} />}
        {activeTab === 'profile' && <Profile state={profileState} retry={() => setProfileReload((value) => value + 1)} />}
        {activeTab === 'quality' && <Quality state={qualityState} retry={() => setQualityReload((value) => value + 1)} />}
        {activeTab === 'anomalies' && <Anomalies state={anomalyState} retry={() => setAnomalyReload((value) => value + 1)} onPage={(offset) => { setPageOffset(offset); setExplanation(null); setExplanationError('') }} explanation={explanation} explanationLoading={explanationLoading} explanationError={explanationError} onExplain={explainRow} onCloseExplanation={() => setExplanation(null)} rowInput={rowInput} setRowInput={setRowInput} onLookup={handleLookup} />}
        {activeTab === 'visualizations' && <Visualizations datasetId={selectedId} profileState={profileState} profileRetry={() => setProfileReload((value) => value + 1)} qualityState={qualityState} anomalyState={visualAnomalyState} anomalyRetry={() => setVisualAnomalyReload((value) => value + 1)} />}
      </>}
      <footer className="main-footer">Anomaly flags invite review. They are not automatic data-quality errors.</footer>
    </main>
  </div>
}
