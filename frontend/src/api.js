const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`${API_BASE}${path}`, options)
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new Error('Could not reach the API. Check that the backend is running.')
  }

  const text = await response.text()
  let payload
  try {
    payload = text ? JSON.parse(text) : null
  } catch {
    payload = null
  }

  if (!response.ok) {
    const detail = payload?.detail
    let message = `Request failed (${response.status}).`
    if ([502, 503, 504].includes(response.status)) {
      message = 'Could not reach the API. Check that the backend is running.'
    } else if (typeof detail === 'string') {
      message = detail
    } else if (Array.isArray(detail)) {
      message = detail.map((item) => item.msg).join('; ')
    }
    throw new Error(message)
  }
  return payload
}

export const api = {
  datasets: (signal) => request('/datasets', { signal }),
  profile: (id, signal) => request(`/datasets/${encodeURIComponent(id)}/profile`, { signal }),
  quality: (id, signal) => request(`/datasets/${encodeURIComponent(id)}/quality`, { signal }),
  visualization: (id, column, signal) =>
    request(`/datasets/${encodeURIComponent(id)}/visualizations?column=${encodeURIComponent(column)}`, { signal }),
  anomalies: (id, offset = 0, limit = 20, signal) =>
    request(`/datasets/${encodeURIComponent(id)}/anomalies?offset=${offset}&limit=${limit}`, { signal }),
  explanation: (id, rowNumber, signal) =>
    request(`/datasets/${encodeURIComponent(id)}/anomalies/${encodeURIComponent(rowNumber)}/explanation`, { signal }),
  upload: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request('/datasets/upload', { method: 'POST', body: form })
  },
}
