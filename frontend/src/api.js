const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export async function sendChat(sessionId, message) {
  const resp = await fetch(`${API}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  })
  return resp.json()
}

export async function uploadLab(sessionId, file) {
  const formData = new FormData()
  formData.append('file', file)
  const resp = await fetch(`${API}/upload-lab?session_id=${sessionId}`, {
    method: 'POST',
    body: formData,
  })
  return resp.json()
}

export async function uploadVoice(blob) {
  const formData = new FormData()
  formData.append('file', blob, 'recording.webm')
  const resp = await fetch(`${API}/voice`, { method: 'POST', body: formData })
  return resp.json()
}

export async function fetchSessions() {
  const resp = await fetch(`${API}/sessions`)
  return resp.json()
}

export async function fetchSessionMessages(sessionId) {
  const resp = await fetch(`${API}/sessions/${sessionId}/messages`)
  return resp.json()
}

export async function fetchReport(sessionId) {
  const resp = await fetch(`${API}/report/${sessionId}`)
  return resp.json()
}

export function reportPdfUrl(sessionId) {
  return `${API}/report/${sessionId}/pdf`
}

export async function registerUser(name, email, password, role) {
  const resp = await fetch(`${API}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password, role }),
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    throw new Error(err.detail || 'Registration failed')
  }
  return resp.json()
}

export async function loginUser(email, password) {
  const resp = await fetch(`${API}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    throw new Error(err.detail || 'Login failed')
  }
  return resp.json()
}

export const API_BASE = API