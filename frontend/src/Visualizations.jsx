import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from './api'
import { formatNumber, titleCase } from './format'
import PlotChart from './PlotChart'

const GREEN = '#51ad95'
const BLUE = '#527f98'
const BAR_LAYOUT = {
  xaxis: { title: { text: 'Rows' }, rangemode: 'tozero', gridcolor: '#edf2f0', zeroline: false },
  yaxis: { autorange: 'reversed', automargin: true, tickfont: { size: 10 } },
  margin: { l: 135, r: 22, t: 12, b: 52 },
  showlegend: false,
}

function horizontalBars(labels, counts, color = GREEN, unit = 'rows') {
  return [{ type: 'bar', orientation: 'h', x: counts, y: labels.map((label) => label.length > 27 ? `${label.slice(0, 24)}…` : label),
    customdata: labels, marker: { color, line: { color: '#ffffff', width: 1 } },
    hovertemplate: `%{customdata}<br>%{x:,} ${unit}<extra></extra>` }]
}

function ChartValues({ labels, counts, label = 'Rows', fractionDigits = 0 }) {
  return <details className="chart-values"><summary>View chart values as a table</summary>
    <div className="table-scroll"><table><thead><tr><th>Group</th><th>{label}</th></tr></thead><tbody>
      {labels.map((name, index) => <tr key={`${name}-${index}`}><td>{name}</td><td>{formatNumber(counts[index], fractionDigits)}</td></tr>)}
    </tbody></table></div>
  </details>
}

function MissingValuesTable({ columns, rowsCount }) {
  return <details className="chart-values"><summary>View missing fields as a table</summary>
    <div className="table-scroll"><table><thead><tr><th>Field</th><th>Missing rows</th><th>Share of rows</th></tr></thead><tbody>
      {columns.map((column) => <tr key={column.name}><td>{column.name}</td><td>{formatNumber(column.missing_count, 0)}</td><td>{formatNumber(100 * column.missing_count / rowsCount, 2)}%</td></tr>)}
    </tbody></table></div>
  </details>
}

function ChartPanel({ eyebrow, title, note, children }) {
  return <section className="panel chart-panel"><div className="panel-head"><div><span className="eyebrow">{eyebrow}</span><h3>{title}</h3></div></div>
    {note && <p className="chart-note">{note}</p>}{children}
  </section>
}

function Distribution({ datasetId, columns }) {
  const available = useMemo(() => columns.filter((column) => ['numeric', 'categorical', 'datetime'].includes(column.logical_type)), [columns])
  const [selectedColumn, setSelectedColumn] = useState('')
  const [range, setRange] = useState('central')
  const [state, setState] = useState({ data: null, loading: false, error: '' })
  const [reload, setReload] = useState(0)
  const cache = useRef(new Map())

  useEffect(() => {
    if (!available.some((column) => column.name === selectedColumn)) {
      setSelectedColumn(available.find((column) => column.logical_type === 'numeric')?.name ?? available[0]?.name ?? '')
    }
  }, [available, selectedColumn])

  useEffect(() => {
    if (!selectedColumn) return
    const cached = cache.current.get(selectedColumn)
    if (cached && reload === 0) {
      setState({ data: cached, loading: false, error: '' })
      return
    }
    const controller = new AbortController()
    setState({ data: null, loading: true, error: '' })
    api.visualization(datasetId, selectedColumn, controller.signal).then((data) => {
      cache.current.set(selectedColumn, data)
      setState({ data, loading: false, error: '' })
    }).catch((error) => {
      if (error.name !== 'AbortError') setState({ data: null, loading: false, error: error.message })
    })
    return () => controller.abort()
  }, [datasetId, selectedColumn, reload])

  const data = state.data
  const chart = useMemo(() => {
    if (!data || data.status !== 'evaluated') return null
    if (data.logical_type === 'numeric' && data.distribution_kind === 'discrete') {
      const labels = data.categories.map((item) => item.value)
      const counts = data.categories.map((item) => item.count)
      return { traces: [{ type: 'bar', x: labels, y: counts, marker: { color: GREEN },
        hovertemplate: '%{x}<br>%{y:,} rows<extra></extra>' }],
        layout: { xaxis: { title: { text: data.column }, type: 'category' }, yaxis: { title: { text: 'Rows' }, rangemode: 'tozero', gridcolor: '#edf2f0' }, margin: { l: 62, r: 22, t: 12, b: 58 } },
        labels, counts }
    }
    if (data.logical_type === 'numeric') {
      const bins = range === 'central' ? data.central_range : data.full_range
      const labels = bins.counts.map((_, index) => `${formatNumber(bins.edges[index], 2)} to ${formatNumber(bins.edges[index + 1], 2)}`)
      return {
        traces: [{ type: 'bar', x: bins.counts.map((_, index) => (bins.edges[index] + bins.edges[index + 1]) / 2),
          y: bins.counts, width: bins.counts.map((_, index) => bins.edges[index + 1] - bins.edges[index]),
          customdata: labels, marker: { color: GREEN }, hovertemplate: '%{customdata}<br>%{y:,} rows<extra></extra>' }],
        layout: { xaxis: { title: { text: data.column }, gridcolor: '#edf2f0' }, yaxis: { title: { text: 'Rows' }, rangemode: 'tozero', gridcolor: '#edf2f0' }, margin: { l: 62, r: 22, t: 12, b: 58 } },
        labels, counts: bins.counts,
      }
    }
    if (data.logical_type === 'datetime') {
      const labels = data.time_buckets.map((bucket) => bucket.period)
      const counts = data.time_buckets.map((bucket) => bucket.count)
      return { traces: [{ type: labels.length > 2 ? 'scatter' : 'bar', mode: labels.length > 2 ? 'lines+markers' : undefined,
        x: labels, y: counts, marker: { color: GREEN, size: 7 }, line: { color: GREEN, width: 2 }, hovertemplate: '%{x}<br>%{y:,} rows<extra></extra>' }],
        layout: { xaxis: { title: { text: `By ${data.time_unit}` }, type: 'category' }, yaxis: { title: { text: 'Rows' }, rangemode: 'tozero', gridcolor: '#edf2f0' }, margin: { l: 62, r: 22, t: 12, b: 58 } },
        labels, counts }
    }
    const labels = data.categories.map((item) => item.value)
    const counts = data.categories.map((item) => item.count)
    if (data.other_count) { labels.push('Other categories'); counts.push(data.other_count) }
    return { traces: horizontalBars(labels, counts), layout: BAR_LAYOUT, labels, counts }
  }, [data, range])

  return <ChartPanel eyebrow="FIELD EXPLORER" title="Explore a field" note="Compare the values within one field. Hover for exact counts; drag to zoom.">
    {available.length ? <>
      <div className="chart-controls"><label htmlFor="chart-column">Field</label><select id="chart-column" value={selectedColumn} onChange={(event) => { setSelectedColumn(event.target.value); setRange('central') }}>
        {available.map((column) => <option key={column.name} value={column.name}>{column.name} · {titleCase(column.logical_type)}</option>)}
      </select>
      {data?.logical_type === 'numeric' && data?.distribution_kind !== 'discrete' && <div className="chart-toggle" aria-label="Numeric range">
        <button className={range === 'central' ? 'active' : ''} onClick={() => setRange('central')}>Typical range</button>
        <button className={range === 'full' ? 'active' : ''} onClick={() => setRange('full')}>Full range</button>
      </div>}</div>
      {state.loading && <p className="chart-loading" role="status">Counting field values…</p>}
      {state.error && <div className="chart-error" role="alert">{state.error} <button className="text-button" onClick={() => setReload((value) => value + 1)}>Try again</button></div>}
      {data?.status === 'not_evaluated' && <p className="chart-empty">{data.reason}</p>}
      {chart && <>
        <PlotChart data={chart.traces} layout={chart.layout} label={`${data.column} distribution`} height={340} />
        <p className="chart-caption">{formatNumber(data.usable_count, 0)} usable rows · {formatNumber(data.missing_count, 0)} missing{data.excluded_nonfinite_count ? ` · ${formatNumber(data.excluded_nonfinite_count, 0)} infinite values excluded` : ''}.
          {data.logical_type === 'numeric' && data.distribution_kind !== 'discrete' && range === 'central' ? ` Typical range uses the 1st–99th percentiles; ${formatNumber(data.outside_central_count, 0)} finite rows outside it are excluded from this view.` : ''}
          {data.logical_type === 'numeric' && data.distribution_kind === 'discrete' ? ' Each bar is an actual value, not a histogram range.' : ''}
          {data.logical_type === 'datetime' ? ' Empty periods are included so gaps are visible.' : ''}
          {data.logical_type === 'categorical' && data.other_count ? ' Remaining categories are grouped as Other.' : ''}
        </p>
        <ChartValues labels={chart.labels} counts={chart.counts} />
      </>}
    </> : <p className="chart-empty">This dataset has no numeric, date, or categorical fields to chart.</p>}
  </ChartPanel>
}

export default function Visualizations({ datasetId, profileState, profileRetry, anomalyState, anomalyRetry }) {
  const profile = profileState.data?.dataset_id === datasetId ? profileState.data : null
  const anomalies = anomalyState.data?.dataset_id === datasetId ? anomalyState.data : null
  const missing = useMemo(() => profile?.columns.filter((column) => column.missing_count > 0)
    .sort((a, b) => b.missing_count - a.missing_count).slice(0, 12) ?? [], [profile])
  const signals = useMemo(() => {
    if (!anomalies) return []
    const result = []
    for (const [methodName, method] of Object.entries(anomalies.methods)) {
      if (method.status !== 'evaluated') continue
      if (methodName === 'isolation_forest') {
        if (method.flagged_rows > 0) result.push({ label: 'Isolation Forest', count: method.flagged_rows })
      } else {
        for (const [field, evidence] of Object.entries(method.fields)) {
          if (evidence.status === 'evaluated' && evidence.flagged_rows > 0) result.push({ label: `${titleCase(methodName)} · ${field}`, count: evidence.flagged_rows })
        }
      }
    }
    return result.sort((a, b) => b.count - a.count).slice(0, 12)
  }, [anomalies])

  const missingLabels = missing.map((column) => column.name)
  const missingCounts = missing.map((column) => column.missing_count)
  const missingPercentages = missing.map((column) => 100 * column.missing_count / profile.rows_count)
  const signalLabels = signals.map((item) => item.label)
  const signalCounts = signals.map((item) => item.count)

  return <div className="section-stack">
    <div className="section-intro"><span className="eyebrow">INTERACTIVE VISUALIZATIONS</span><h2>Explore the patterns</h2><p>See which fields need attention, how values are distributed, and which numeric checks flagged rows. Use Quality for the score and its evidence.</p></div>
      <ChartPanel eyebrow="COMPLETENESS" title="Where values are missing" note="Share of rows missing each field, ranked by impact. Up to 12 fields are shown; fields without missing values are omitted.">
        {profileState.loading || (!profile && !profileState.error) ? <p className="chart-loading">Loading column counts…</p> : profileState.error ? <div className="chart-error">{profileState.error} <button className="text-button" onClick={profileRetry}>Try again</button></div> : missing.length ? <>
          <p className="chart-insight"><strong>{missing[0].name}</strong> is missing in <strong>{formatNumber(missingPercentages[0], 1)}%</strong> of rows ({formatNumber(missingCounts[0], 0)} records).</p>
          <PlotChart data={[{ type: 'bar', orientation: 'h', x: missingPercentages, y: missingLabels.map((label) => label.length > 27 ? `${label.slice(0, 24)}…` : label), customdata: missingCounts,
            marker: { color: BLUE }, hovertemplate: '%{y}<br>%{x:.2f}% missing · %{customdata:,} rows<extra></extra>' }]}
            layout={{ ...BAR_LAYOUT, xaxis: { title: { text: 'Rows missing this field (%)' }, range: [0, Math.min(100, Math.max(...missingPercentages) + 12)], gridcolor: '#edf2f0', zeroline: false } }}
            label="Percentage of rows missing each field" height={Math.max(250, missing.length * 37 + 80)} />
          <MissingValuesTable columns={missing} rowsCount={profile.rows_count} />
        </> : <p className="chart-empty">No missing values were reported.</p>}
      </ChartPanel>
    {profile && <Distribution key={datasetId} datasetId={datasetId} columns={profile.columns} />}
    <ChartPanel eyebrow="ANOMALY SIGNALS" title="What flagged the rows" note="Shows up to 12 leading checks that actually flagged rows. Counts overlap; the distinct flagged-row total below counts each row once.">
      {anomalyState.loading || (!anomalies && !anomalyState.error) ? <p className="chart-loading">Counting anomaly signals…</p> : anomalyState.error ? <div className="chart-error">{anomalyState.error} <button className="text-button" onClick={anomalyRetry}>Try again</button></div> : signals.length ? <>
        <PlotChart data={horizontalBars(signalLabels, signalCounts, '#d39468')} layout={BAR_LAYOUT} label="Rows flagged by each anomaly signal" height={Math.max(280, signals.length * 33 + 70)} />
        <p className="chart-caption">{formatNumber(anomalies.anomaly_rows_count, 0)} distinct flagged rows of {formatNumber(anomalies.rows_count, 0)}. Flags invite review; they are not proof of data-quality errors.</p>
        <ChartValues labels={signalLabels} counts={signalCounts} />
      </> : <p className="chart-empty">No anomaly method flagged a row, or no method could be evaluated.</p>}
    </ChartPanel>
  </div>
}
