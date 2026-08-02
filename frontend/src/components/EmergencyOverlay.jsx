export default function EmergencyOverlay({ show, onReset }) {
  if (!show) return null
  return (
    <div className="fixed inset-0 bg-emred/95 z-[999] flex flex-col items-center justify-center text-center p-5 animate-flash-bg">
      <h1 className="text-3xl mb-4">🚨 EMERGENCY DETECTED</h1>
      <div className="text-2xl font-mono my-4 tracking-wide">
        India: 108 &nbsp;|&nbsp; US: 911 &nbsp;|&nbsp; EU: 112
      </div>
      <p className="max-w-md mb-6 opacity-90">
        This is not a diagnosis. Please contact emergency services immediately or go to the nearest emergency room.
      </p>
      <button
        onClick={onReset}
        className="bg-white text-emred border-none px-7 py-3 rounded-lg font-bold cursor-pointer text-sm"
      >
        Start New Session
      </button>
    </div>
  )
}
