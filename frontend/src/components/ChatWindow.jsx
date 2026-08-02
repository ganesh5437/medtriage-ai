import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble'
import TypingIndicator from './TypingIndicator'
import VoiceInput from './VoiceInput'

export default function ChatWindow({ messages, typing, input, setInput, onSend }) {
  const logRef = useRef(null)

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [messages, typing])

  function handleKeyDown(e) {
    if (e.key === 'Enter') onSend(input)
  }

  return (
    <div className="flex-1 flex flex-col min-w-0">
      <div ref={logRef} className="flex-1 overflow-y-auto p-5 flex flex-col gap-3.5">
        {messages.map((m, i) => (
          <MessageBubble key={i} role={m.role} content={m.content} disclaimer={m.disclaimer} time={m.time} />
        ))}
        {typing && <TypingIndicator />}
      </div>

      <div className="flex items-center gap-2.5 px-5 py-3.5 border-t border-border bg-surface flex-shrink-0">
        <VoiceInput
          onTranscribed={(text) => onSend(text)}
          onError={(err) => onSend(null, err)}
        />
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe your symptoms..."
          className="flex-1 bg-bg border border-border text-white px-3.5 py-2.5 rounded-lg text-sm outline-none focus:border-teal"
        />
        <button
          onClick={() => onSend(input)}
          title="Send"
          className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 bg-teal text-white transition-transform active:scale-90"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M2 21l21-9L2 3v7l15 2-15 2v7z" />
          </svg>
        </button>
      </div>
    </div>
  )
}
