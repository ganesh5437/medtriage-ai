export default function TypingIndicator() {
  return (
    <div className="flex gap-1 px-3.5 py-3 self-start">
      <span className="w-1.5 h-1.5 rounded-full bg-textdim animate-bounce-dot" />
      <span className="w-1.5 h-1.5 rounded-full bg-textdim animate-bounce-dot [animation-delay:.2s]" />
      <span className="w-1.5 h-1.5 rounded-full bg-textdim animate-bounce-dot [animation-delay:.4s]" />
    </div>
  )
}
