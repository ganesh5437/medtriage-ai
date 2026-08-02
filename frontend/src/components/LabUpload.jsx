import { useRef, useState } from 'react'
import { uploadLab } from '../api'

export default function LabUpload({ sessionId, onNeedsSession }) {
  const [dragOver, setDragOver] = useState(false)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  async function handleFile(file) {
    if (!sessionId) {
      onNeedsSession()
      return
    }
    setLoading(true)
    setError(null)
    setResults(null)
    try {
      const data = await uploadLab(sessionId, file)
      setLoading(false)
      if (data.parsed && Object.keys(data.values).length) {
        setResults(data.values)
      } else {
        setError(data.error || 'No values extracted.')
      }
    } catch {
      setLoading(false)
      setError('Upload failed. Please try again.')
    }
  }

  return (
    <div>
      <div className="text-[11px] uppercase tracking-wide text-textdim mb-2.5 font-semibold">
        Lab report
      </div>
      <div
        onClick={() => fileInputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragOver(false)
          if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0])
        }}
        className={`border-2 border-dashed border-teal rounded-lg p-5 text-center text-xs text-textdim cursor-pointer transition-colors ${dragOver ? 'bg-teal/10' : ''}`}
      >
        📄 Drop PDF/JPG/PNG here
        <br />
        or click to upload
      </div>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.jpg,.jpeg,.png"
        className="hidden"
        onChange={(e) => e.target.files.length && handleFile(e.target.files[0])}
      />

      {loading && (
        <div className="w-4 h-4 border-2 border-border border-t-teal rounded-full animate-spin-slow mx-auto mt-2" />
      )}
      {error && (
        <div className="bg-bg border border-border rounded-lg px-2.5 py-2 mt-2 text-xs">{error}</div>
      )}
      {results &&
        Object.entries(results).map(([test, v]) => (
          <div key={test} className="bg-bg border border-border rounded-lg px-2.5 py-2 mt-2 text-xs flex justify-between">
            <span>{test}</span>
            <span className="text-teal-light font-semibold">
              {v.value} {v.unit || ''}
            </span>
          </div>
        ))}
    </div>
  )
}
