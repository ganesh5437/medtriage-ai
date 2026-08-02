import { useEffect, useState } from 'react'
import { fetchSessions, fetchSessionMessages, fetchReport, reportPdfUrl } from '../api'

const badgeClass = {
  pending: 'bg-amber/20 text-amber',
  active: 'bg-teal/20 text-teal-light',
  emergency: 'bg-emred/20 text-red-400',
}

export default function ClinicianDashboard() {
  const [sessions, setSessions] = useState([])
  const [loadingList, setLoadingList] = useState(true)
  const [selectedId, setSelectedId] = useState(null)
  const [detail, setDetail] = useState(null)
  const [loadingDetail, setLoadingDetail] = useState(false)

  useEffect(() => {
    fetchSessions()
      .then((data) => setSessions(data.sessions || []))
      .catch(() => setSessions([]))
      .finally(() => setLoadingList(false))
  }, [])

  async function selectSession(sid) {
    setSelectedId(sid)
    setLoadingDetail(true)
    try {
      const [msgs, report] = await Promise.all([fetchSessionMessages(sid), fetchReport(sid)])
      setDetail({ msgs, report })
    } catch {
      setDetail(null)
    } finally {
      setLoadingDetail(false)
    }
  }

  return (
    <div className="flex flex-1 overflow-hidden">
      <div className="w-[300px] bg-surface border-r border-border overflow-y-auto flex-shrink-0">
        {loadingList && <div className="p-4 text-textdim text-sm">Loading...</div>}
        {!loadingList && sessions.length === 0 && (
          <div className="p-4 text-textdim text-sm">No sessions yet.</div>
        )}
        {sessions.map((s) => (
          <div
            key={s.session_id}
            onClick={() => selectSession(s.session_id)}
            className={`p-3.5 border-b border-border cursor-pointer transition-colors hover:bg-bg ${
              selectedId === s.session_id ? 'bg-teal/10 border-l-[3px] border-l-teal' : ''
            }`}
          >
            <div className="text-[11px] text-textdim font-mono">{s.session_id.slice(0, 8)}...</div>
            <div className="text-sm mt-1">{s.started_at ? new Date(s.started_at).toLocaleString() : ''}</div>
            <div className="text-xs text-textdim mt-1">
              {(s.symptoms_summary || []).join(', ') || 'No symptoms recorded'}
            </div>
            <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold uppercase mt-1.5 ${badgeClass[s.status] || badgeClass.active}`}>
              {s.status}
            </span>
          </div>
        ))}
      </div>

      <div className="flex-1 p-6 overflow-y-auto">
        {!selectedId && (
          <div className="text-textdim text-center mt-20 text-sm">
            Select a session to view chat history and report.
          </div>
        )}
        {selectedId && loadingDetail && (
          <div className="text-textdim text-center mt-20 text-sm">Loading session...</div>
        )}
        {selectedId && !loadingDetail && detail && (
          <div>
            <h2 className="mb-4 text-lg font-semibold">Session {selectedId.slice(0, 8)}...</h2>

            <div className="text-[11px] uppercase tracking-wide text-textdim mb-2.5 font-semibold">
              Chat History
            </div>
            <div className="bg-surface border border-border rounded-lg p-3.5 mb-5 max-h-[300px] overflow-y-auto">
              {detail.msgs.messages.map((m, i) => (
                <div key={i} className="mb-2.5">
                  <b className={`text-xs ${m.role === 'ai' ? 'text-teal-light' : 'text-white'}`}>
                    {m.role.toUpperCase()}
                  </b>
                  <div className="text-sm mt-0.5">{m.content}</div>
                </div>
              ))}
            </div>

            <div className="text-[11px] uppercase tracking-wide text-textdim mb-2.5 font-semibold">
              Report Summary
            </div>
            <div className="bg-surface border border-border rounded-lg p-3.5">
              <p className="text-sm mb-2">
                <b>Chief complaint:</b> {detail.report.chief_complaint || 'N/A'}
              </p>
              <p className="text-sm mb-2">
                <b>Symptoms:</b> {(detail.report.symptoms || []).join(', ') || 'None recorded'}
              </p>
              <p className="text-[11px] text-textdim mt-2.5">{detail.report.disclaimer}</p>
            </div>
            <button
              onClick={() => window.open(reportPdfUrl(selectedId), '_blank')}
              className="bg-teal text-white border-none px-4.5 py-2.5 rounded-lg font-semibold text-sm cursor-pointer mt-4"
            >
              ⬇ Download PDF Report
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
