import { useEffect, useRef, useState } from 'react'

let plotlyPromise

function loadPlotly() {
  if (!plotlyPromise) {
    plotlyPromise = import('plotly.js-basic-dist-min').then((module) => module.default ?? module)
  }
  return plotlyPromise
}

export default function PlotChart({ data, layout, label, height = 320 }) {
  const element = useRef(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    let plotly
    let observer
    const target = element.current
    setError('')

    loadPlotly().then(async (library) => {
      if (!active) return
      plotly = library
      await plotly.react(target, data, {
        autosize: true,
        margin: { l: 105, r: 22, t: 12, b: 55 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        bargap: 0.19,
        font: { family: 'Inter, Segoe UI, sans-serif', size: 11, color: '#58737a' },
        ...layout,
      }, {
        responsive: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['sendChartToCloud', 'pan2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'select2d', 'lasso2d'],
      })
      if (!active) return
      observer = new ResizeObserver(() => {
        if (!active || !target.isConnected || !target.offsetWidth) return
        plotly.Plots.resize(target).catch(() => {
          if (active && target.isConnected) setError('The chart could not be resized. Try reloading this page.')
        })
      })
      observer.observe(target)
    }).catch(() => {
      if (active) setError('The chart could not be drawn. Try reloading this page.')
    })

    return () => {
      active = false
      observer?.disconnect()
      if (plotly) plotly.purge(target)
    }
  }, [data, layout])

  if (error) return <p className="chart-error" role="alert">{error}</p>
  return <div className="plot-chart" ref={element} role="img" aria-label={label} style={{ height }} />
}
