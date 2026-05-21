import { useState, useEffect } from 'react'

const PRIORITY_BG = {
  1: 'bg-red-950 border-red-700',
  2: 'bg-orange-950 border-orange-700',
  3: 'bg-blue-950 border-blue-700',
}
const PRIORITY_BAR = {
  1: 'bg-red-400',
  2: 'bg-orange-400',
  3: 'bg-blue-400',
}

const AUTO_DISMISS_MS = 14000

export default function AlertModal({ alert, onDismiss }) {
  const [progress, setProgress] = useState(100)

  useEffect(() => {
    const start = Date.now()
    const interval = setInterval(() => {
      const elapsed = Date.now() - start
      const remaining = Math.max(0, 100 - (elapsed / AUTO_DISMISS_MS) * 100)
      setProgress(remaining)
      if (remaining === 0) { clearInterval(interval); onDismiss() }
    }, 100)
    return () => clearInterval(interval)
  }, [])

  const bg  = PRIORITY_BG[alert.priority]  || PRIORITY_BG[3]
  const bar = PRIORITY_BAR[alert.priority] || PRIORITY_BAR[3]

  return (
    <div className={`mx-2 rounded-lg border ${bg} overflow-hidden shadow-xl`}>
      {/* Progress bar — thicker and colored */}
      <div className="h-1 bg-black/40">
        <div className={`h-1 ${bar} transition-all duration-100`} style={{ width: `${progress}%` }} />
      </div>

      <div className="px-3 py-2.5">
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-2">
            <span className="text-xl leading-none">{alert.icon}</span>
            <span className="text-sm font-bold text-white leading-tight">{alert.title}</span>
          </div>
          <button onClick={onDismiss}
            className="text-gray-400 hover:text-white text-base leading-none flex-shrink-0">✕</button>
        </div>

        {/* Position context */}
        {(alert.hero_pos || alert.villain_pos) && (
          <div className="flex items-center gap-1.5 mb-2 flex-wrap">
            {alert.hero_pos && (
              <span className="text-xs bg-green-900 text-green-300 px-1.5 py-0.5 rounded font-bold">
                Você: {alert.hero_pos}
              </span>
            )}
            {alert.villain_pos && alert.villain && (
              <span className="text-xs bg-black/40 text-gray-300 px-1.5 py-0.5 rounded">
                vs {alert.villain} ({alert.villain_pos})
              </span>
            )}
          </div>
        )}

        {/* Main action */}
        <p className="text-sm font-semibold text-white leading-snug mb-1.5">{alert.action}</p>

        {/* Detail */}
        {alert.detail && (
          <p className="text-xs text-gray-400 leading-relaxed">{alert.detail}</p>
        )}

        {/* Dismiss */}
        <button onClick={onDismiss}
          className="w-full mt-2.5 py-1 rounded bg-white/10 hover:bg-white/20 text-xs text-white font-medium transition-colors">
          Entendi
        </button>
      </div>
    </div>
  )
}
