import { useState, useEffect, useRef } from 'react'
import { registerUser, loginUser } from '../api'

const TAGLINES = [
  'AI-powered triage. Built for real conversations.',
  'Symptoms in. Clarity out.',
  'Every case gets a second look — before the first visit.',
]

function BackgroundVitals() {
  const pathRef = useRef(null)
  const phaseRef = useRef(0)

  useEffect(() => {
    let frame
    function draw() {
      phaseRef.current += 0.12
      const phase = phaseRef.current
      let d = 'M0,60 '
      for (let x = 0; x <= 900; x += 6) {
        const t = (x / 900) * Math.PI * 14 + phase
        const spike = Math.floor(t / 3) % 5 === 0 ? Math.sin(t * 4) * 22 : Math.sin(t * 0.6) * 4
        d += `L${x},${60 - spike} `
      }
      if (pathRef.current) pathRef.current.setAttribute('d', d)
      frame = requestAnimationFrame(draw)
    }
    frame = requestAnimationFrame(draw)
    return () => cancelAnimationFrame(frame)
  }, [])

  return (
    <svg
      viewBox="0 0 900 120"
      preserveAspectRatio="none"
      className="absolute inset-x-0 top-1/2 -translate-y-1/2 w-full h-32 opacity-[0.08] pointer-events-none"
    >
      <path ref={pathRef} fill="none" stroke="#2dd4bf" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export default function AuthScreen({ onAuthed }) {
  const [mode, setMode] = useState('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('patient')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [taglineIdx, setTaglineIdx] = useState(0)
  const [taglineVisible, setTaglineVisible] = useState(true)

  useEffect(() => {
    const interval = setInterval(() => {
      setTaglineVisible(false)
      setTimeout(() => {
        setTaglineIdx((i) => (i + 1) % TAGLINES.length)
        setTaglineVisible(true)
      }, 400)
    }, 3800)
    return () => clearInterval(interval)
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      let data
      if (mode === 'register') {
        data = await registerUser(name, email, password, role)
      } else {
        data = await loginUser(email, password)
      }
      onAuthed({ token: data.access_token, role: data.role, email })
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-screen flex items-center justify-center bg-bg relative overflow-hidden">
      {/* subtle grid pattern */}
      <div
        className="absolute inset-0 opacity-[0.04] pointer-events-none"
        style={{
          backgroundImage:
            'linear-gradient(#2dd4bf 1px, transparent 1px), linear-gradient(90deg, #2dd4bf 1px, transparent 1px)',
          backgroundSize: '42px 42px',
        }}
      />
      <BackgroundVitals />

      <div className="w-full max-w-sm bg-surface/95 backdrop-blur border border-border rounded-2xl p-8 relative z-10 shadow-2xl">
        <div className="flex items-center gap-2.5 mb-2 justify-center">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" className="animate-[pulse-ring_2.4s_ease-in-out_infinite]">
            <path
              d="M12 21C12 21 4 15.5 4 9.5C4 6.5 6.5 4 9.5 4C11 4 12 5 12 5C12 5 13 4 14.5 4C17.5 4 20 6.5 20 9.5C20 15.5 12 21 12 21Z"
              stroke="#0d9488"
              strokeWidth="1.8"
            />
          </svg>
          <div>
            <div className="font-bold text-lg">MedTriage AI</div>
            <div className="text-[11px] text-textdim uppercase tracking-wide">Pre-consultation assistant</div>
          </div>
        </div>

        <div
          className={`text-center text-[11px] text-teal-light h-8 flex items-center justify-center transition-opacity duration-400 ${taglineVisible ? 'opacity-100' : 'opacity-0'}`}
        >
          {TAGLINES[taglineIdx]}
        </div>

        <div className="flex gap-1 bg-bg border border-border rounded-lg p-0.5 mb-6 mt-2">
          <button
            type="button"
            onClick={() => { setMode('login'); setError(null) }}
            className={`flex-1 py-2 rounded-md text-sm font-semibold transition-colors ${mode === 'login' ? 'bg-teal text-white' : 'text-textdim'}`}
          >
            Log In
          </button>
          <button
            type="button"
            onClick={() => { setMode('register'); setError(null) }}
            className={`flex-1 py-2 rounded-md text-sm font-semibold transition-colors ${mode === 'register' ? 'bg-teal text-white' : 'text-textdim'}`}
          >
            Sign Up
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
          {mode === 'register' && (
            <>
              <div>
                <label className="text-[11px] uppercase tracking-wide text-textdim block mb-1.5">Full name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-bg border border-border text-white px-3.5 py-2.5 rounded-lg text-sm outline-none focus:border-teal transition-colors"
                  placeholder="Jane Doe"
                />
              </div>
              <div>
                <label className="text-[11px] uppercase tracking-wide text-textdim block mb-1.5">I am a</label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setRole('patient')}
                    className={`flex-1 py-2 rounded-lg text-sm font-semibold border transition-colors ${role === 'patient' ? 'bg-teal/15 border-teal text-teal-light' : 'border-border text-textdim'}`}
                  >
                    Patient
                  </button>
                  <button
                    type="button"
                    onClick={() => setRole('clinician')}
                    className={`flex-1 py-2 rounded-lg text-sm font-semibold border transition-colors ${role === 'clinician' ? 'bg-teal/15 border-teal text-teal-light' : 'border-border text-textdim'}`}
                  >
                    Clinician
                  </button>
                </div>
              </div>
            </>
          )}

          <div>
            <label className="text-[11px] uppercase tracking-wide text-textdim block mb-1.5">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-bg border border-border text-white px-3.5 py-2.5 rounded-lg text-sm outline-none focus:border-teal transition-colors"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label className="text-[11px] uppercase tracking-wide text-textdim block mb-1.5">Password</label>
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-bg border border-border text-white px-3.5 py-2.5 rounded-lg text-sm outline-none focus:border-teal transition-colors"
              placeholder="At least 6 characters"
            />
          </div>

          {error && <div className="text-xs text-red-400 bg-emred/10 border border-emred/30 rounded-lg px-3 py-2">{error}</div>}

          <button
            type="submit"
            disabled={loading}
            className="bg-teal hover:bg-teal-light text-white font-semibold py-2.5 rounded-lg text-sm mt-1 disabled:opacity-60 transition-colors"
          >
            {loading ? 'Please wait...' : mode === 'login' ? 'Log In' : 'Create Account'}
          </button>
        </form>

        <div className="text-[10px] text-textdim text-center mt-5">
          ⚠ Demo only — do not enter real personal health information.
        </div>
      </div>
    </div>
  )
}