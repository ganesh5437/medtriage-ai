export default function DifferentialPanel({ differential }) {
  return (
    <div className="mt-5">
      <div className="text-[11px] uppercase tracking-wide text-textdim mb-2.5 font-semibold">
        Differential (AI-suggested)
      </div>
      {(!differential || differential.length === 0) && (
        <div className="text-xs text-textdim">Nothing yet — describe your symptoms to begin.</div>
      )}
      {differential &&
        differential.map((d, i) => (
          <div key={i} className="bg-bg border border-border rounded-lg p-2.5 mb-2">
            <div className="font-semibold text-sm text-teal-light">{d.condition}</div>
            <div className="text-[11px] text-textdim mt-0.5">{d.confidence}</div>
          </div>
        ))}
    </div>
  )
}
