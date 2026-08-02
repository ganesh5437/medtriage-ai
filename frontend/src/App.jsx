import { useState } from 'react'
import VitalsLine from './components/VitalsLine'
import SymptomPanel from './components/SymptomPanel'
import ChatWindow from './components/ChatWindow'
import LabUpload from './components/LabUpload'
import DifferentialPanel from './components/DifferentialPanel'
import EmergencyOverlay from './components/EmergencyOverlay'
import ClinicianDashboard from './components/ClinicianDashboard'
import AuthScreen from './components/AuthScreen'
import { sendChat, reportPdfUrl } from './api'

function formatTime() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function App() {
  const [auth, setAuth] = useState(() => {
    const saved = localStorage.getItem('medtriage_auth')
    return saved ? JSON.parse(saved) : null
  })
  const [view, setView] = useState('patient') // 'patient' | 'clinician'
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [typing, setTyping] = useState(false)
  const [vitalsMode, setVitalsMode] = useState('idle')
  const [symptoms, setSymptoms] = useState([])
  const [duration, setDuration] = useState(null)
  const [severity, setSeverity] = useState(0)
  const [symptomCount, setSymptomCount] = useState(0)
  const [differential, setDifferential] = useState([])
  const [showEmergency, setShowEmergency] = useState(false)
  const [showDownload, setShowDownload] = useState(false)

  async function handleSend(text, directError) {
    if (directError) {
      setMessages((prev) => [...prev, { role: 'ai', content: directError, time: formatTime() }])
      return
    }
    if (!text || !text.trim()) return

    setMessages((prev) => [...prev, { role: 'patient', content: text, time: formatTime() }])
    setInput('')
    setVitalsMode('active')
    setTyping(true)

    try {
      const data = await sendChat(sessionId, text)
      setTyping(false)
      setSessionId(data.session_id)

      if (data.is_emergency) {
        setVitalsMode('emergency')
        setShowEmergency(true)
        setMessages((prev) => [...prev, { role: 'ai', content: data.reply, disclaimer: data.disclaimer, time: formatTime() }])
        return
      }

      setVitalsMode('idle')
      setMessages((prev) => [...prev, { role: 'ai', content: data.reply, disclaimer: data.disclaimer, time: formatTime() }])

      const extracted = data.extracted || {}
      setSymptoms(extracted.symptoms || [])
      setSymptomCount((prev) => prev + (extracted.symptoms || []).length)
      setDuration(extracted.duration || null)
      setSeverity(extracted.severity || 0)
      setDifferential(data.differential || [])
      setShowDownload(true)
    } catch {
      setTyping(false)
      setVitalsMode('idle')
      setMessages((prev) => [
        ...prev,
        { role: 'ai', content: 'Connection issue — please check the backend server is running.', time: formatTime() },
      ])
    }
  }

  function handleReset() {
    setShowEmergency(false)
    setVitalsMode('idle')
    setSessionId(null)
    setMessages([])
    setSymptoms([])
    setSymptomCount(0)
    setDuration(null)
    setSeverity(0)
    setDifferential([])
    setShowDownload(false)
  }

  function handleAuthed(authData) {
    localStorage.setItem('medtriage_auth', JSON.stringify(authData))
    setAuth(authData)
    setView(authData.role === 'clinician' ? 'clinician' : 'patient')
  }

  function handleLogout() {
    localStorage.removeItem('medtriage_auth')
    setAuth(null)
    handleReset()
  }

  if (!auth) {
    return <AuthScreen onAuthed={handleAuthed} />
  }

  return (
    <div className="h-screen flex flex-col">
      <div className="bg-surface text-textdim text-[11px] text-center py-1.5 border-b border-border flex-shrink-0">
        ☁ Demo only — do not enter real personal health information.
      </div>

      <header className="flex items-center justify-between px-5 py-3 border-b border-border bg-surface flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <path
              d="M12 21C12 21 4 15.5 4 9.5C4 6.5 6.5 4 9.5 4C11 4 12 5 12 5C12 5 13 4 14.5 4C17.5 4 20 6.5 20 9.5C20 15.5 12 21 12 21Z"
              stroke="#0d9488"
              strokeWidth="1.8"
            />
          </svg>
          <div>
            <div className="font-bold text-base">MedTriage AI</div>
            <div className="text-[11px] text-textdim uppercase tracking-wide">Pre-consultation assistant</div>
          </div>
        </div>

        <VitalsLine mode={vitalsMode} />

        <div className="flex items-center gap-3">
          <div className="flex gap-1 bg-bg border border-border rounded-lg p-0.5">
            <button
              onClick={() => setView('patient')}
              className={`px-3.5 py-1.5 rounded-md text-xs font-semibold ${view === 'patient' ? 'bg-teal text-white' : 'text-textdim'}`}
            >
              Patient
            </button>
            <button
              onClick={() => setView('clinician')}
              className={`px-3.5 py-1.5 rounded-md text-xs font-semibold ${view === 'clinician' ? 'bg-teal text-white' : 'text-textdim'}`}
            >
              Clinician Dashboard
            </button>
          </div>
          <div className="text-right">
            <div className="text-xs font-medium">{auth.email}</div>
            <div className="text-[10px] text-textdim uppercase">{auth.role}</div>
          </div>
          <button
            onClick={handleLogout}
            title="Log out"
            className="text-textdim hover:text-white text-xs border border-border rounded-lg px-3 py-1.5"
          >
            Log out
          </button>
        </div>
      </header>

      {view === 'patient' && (
        <main className="flex flex-1 overflow-hidden">
          <SymptomPanel symptoms={symptoms} duration={duration} severity={severity} count={symptomCount} />
          <ChatWindow messages={messages} typing={typing} input={input} setInput={setInput} onSend={handleSend} />
          <div className="w-[280px] bg-surface border-l border-border p-4 overflow-y-auto flex-shrink-0">
            <LabUpload sessionId={sessionId} onNeedsSession={() => handleSend(null, 'Please describe your symptoms first to start a session before uploading labs.')} />
            <DifferentialPanel differential={differential} />
            {showDownload && (
              <button
                onClick={() => window.open(reportPdfUrl(sessionId), '_blank')}
                className="bg-teal text-white border-none px-4.5 py-2.5 rounded-lg font-semibold text-sm cursor-pointer mt-5"
              >
                ⬇ Download Report PDF
              </button>
            )}
          </div>
        </main>
      )}

      {view === 'clinician' && <ClinicianDashboard />}

      <EmergencyOverlay show={showEmergency} onReset={handleReset} />
    </div>
  )
}