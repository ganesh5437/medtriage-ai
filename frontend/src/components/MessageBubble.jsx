export default function MessageBubble({ role, content, disclaimer, time }) {
  const isPatient = role === 'patient'
  return (
    <div className={`max-w-[70%] animate-pop-in ${isPatient ? 'self-end' : 'self-start'}`}>
      {!isPatient && (
        <div className="text-[10px] text-textdim mb-1 uppercase tracking-wide">MedTriage AI</div>
      )}
      <div
        className={
          isPatient
            ? 'px-3.5 py-3 rounded-2xl rounded-br-sm text-sm leading-relaxed bg-teal text-white'
            : 'px-3.5 py-3 rounded-2xl rounded-bl-sm text-sm leading-relaxed bg-surface border border-border border-l-[3px] border-l-teal'
        }
      >
        {content}
      </div>
      <div className="text-[10px] text-textdim mt-1 opacity-70">{time}</div>
      {disclaimer && <div className="text-[10px] text-textdim mt-1 italic">{disclaimer}</div>}
    </div>
  )
}
