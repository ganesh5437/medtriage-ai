import { useRef, useState } from 'react'
import { uploadVoice } from '../api'

export default function VoiceInput({ onTranscribed, onError }) {
  const [recording, setRecording] = useState(false)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  async function handleClick() {
    if (!recording) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        const recorder = new MediaRecorder(stream)
        chunksRef.current = []
        recorder.ondataavailable = (e) => chunksRef.current.push(e.data)
        recorder.onstop = async () => {
          const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
          try {
            const data = await uploadVoice(blob)
            if (data.success) {
              onTranscribed(data.text)
            } else {
              onError(data.error || 'Voice unavailable. Please type your message.')
            }
          } catch {
            onError('Voice unavailable. Please type your message.')
          }
        }
        recorder.start()
        mediaRecorderRef.current = recorder
        setRecording(true)
      } catch {
        onError('Microphone access denied or unavailable. Please type your message.')
      }
    } else {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current.stream.getTracks().forEach((t) => t.stop())
      setRecording(false)
    }
  }

  return (
    <button
      onClick={handleClick}
      title="Voice input"
      className={
        recording
          ? 'w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 transition-transform active:scale-90 bg-emred border-2 border-emred text-white animate-pulse-ring'
          : 'w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 transition-transform active:scale-90 bg-surface border-2 border-teal text-teal-light'
      }
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 14a3 3 0 003-3V6a3 3 0 10-6 0v5a3 3 0 003 3z" />
        <path d="M19 11a7 7 0 01-14 0H3a9 9 0 008 8.94V22h2v-2.06A9 9 0 0021 11h-2z" />
      </svg>
    </button>
  )
}
