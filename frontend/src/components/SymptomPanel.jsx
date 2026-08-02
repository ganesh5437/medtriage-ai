export default function SymptomPanel({ symptoms, duration, severity, count }) {
  const sevColor = severity <= 3 ? '#16a34a' : severity <= 6 ? '#d97706' : '#dc2626'

  return (
    <div className="w-[280px] bg-surface border-r border-border p-4 overflow-y-auto flex-shrink-0">
      <div className="text-[11px] uppercase tracking-wide text-textdim mb-2.5 font-semibold">
        Symptoms detected
      </div>
      <div>
        {symptoms.map((s, i) => (
          <span
            key={i}
            className="inline-flex items-center gap-1.5 bg-teal/15 text-teal-light border border-teal/35 px-2.5 py-1 rounded-full text-xs mr-1.5 mb-1.5 animate-pop-in"
          >
            {s}
          </span>
        ))}
      </div>

      <div className="mt-4">
        <div className="text-[11px] uppercase tracking-wide text-textdim mb-1.5 font-semibold">
          Severity
        </div>
        <div className="h-2 bg-bg rounded-full overflow-hidden mt-1.5">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{ width: `${severity * 10}%`, backgroundColor: sevColor }}
          />
        </div>
      </div>

      {duration && (
        <div className="text-[11px] text-textdim mt-3.5 flex items-center gap-1.5">
          🕐 Duration: {duration}
        </div>
      )}

      <div className="text-[28px] font-bold mt-4">{count}</div>
      <div className="text-[11px] text-textdim">symptoms this session</div>
    </div>
  )
}
