import { useEffect, useRef } from 'react'

export default function VitalsLine({ mode }) {
  const pathRef = useRef(null)
  const phaseRef = useRef(0)
  const frameRef = useRef(null)

  useEffect(() => {
    function draw() {
      phaseRef.current += mode === 'emergency' ? 0.55 : mode === 'active' ? 0.35 : 0.15
      const phase = phaseRef.current
      let d = 'M0,18 '
      for (let x = 0; x <= 280; x += 4) {
        const t = (x / 280) * Math.PI * 8 + phase
        let y = 18
        if (mode === 'emergency') {
          const spike = Math.floor(t) % 4 === 0 ? Math.sin(t * 6) * 16 : Math.sin(t * 0.5) * 2
          y = 18 - spike
        } else if (mode === 'active') {
          const spike = Math.floor(t / 2) % 3 === 0 ? Math.sin(t * 3) * 10 : Math.sin(t) * 3
          y = 18 - spike
        } else {
          y = 18 - Math.sin(t * 0.5) * 2.5
        }
        d += `L${x},${y} `
      }
      if (pathRef.current) pathRef.current.setAttribute('d', d)
      frameRef.current = requestAnimationFrame(draw)
    }
    frameRef.current = requestAnimationFrame(draw)
    return () => cancelAnimationFrame(frameRef.current)
  }, [mode])

  return (
    <div className="flex-1 max-w-[280px] h-9 mx-6 relative overflow-hidden">
      <svg viewBox="0 0 280 36" preserveAspectRatio="none" className="w-full h-full block">
        <path
          ref={pathRef}
          fill="none"
          stroke={mode === 'emergency' ? '#dc2626' : '#2dd4bf'}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <div className="absolute -bottom-0.5 right-0 text-[9px] text-textdim tracking-wide">
        {mode === 'emergency' ? 'alert' : mode === 'active' ? 'processing' : 'idle'}
      </div>
    </div>
  )
}
