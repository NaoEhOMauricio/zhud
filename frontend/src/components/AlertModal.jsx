import { useState, useEffect } from 'react'

const PRIORITY_BG = {
  1: 'bg-red-950 border-red-700',
  2: 'bg-orange-950 border-orange-700',
  3: 'bg-blue-950 border-blue-700',
}

const AUTO_DISMISS_MS = 12000  // 12 seconds

export default function AlertModal({ alert, onDismiss }) {
  const [progress, setProgress] = useState(100)

  useEffect(() => {
    const start = Date.now()
    const interval = setInterval(() => {
      const elapsed = Date.now() - start
      const remaining = Math.max(0, 100 - (elapsed / AUTO_DISMISS_MS) * 100)
      setProgress(remaining)
      if (remaining === 0) {
        clearInterval(interval)
        onDismiss()
      }
    }, 100)
    return () => clearInterval(interval)
  }, [])

  const bg = PRIORITY_BG[alert.priority] || PRIORITY_BG[3]

  return (
    <div className={`mx-2 rounded-lg border ${bg} overflow-hidden shadow-xl`}>
      {/* Progress bar */}
      <div className="h-0.5 bg-black/20">
        <div
          className="h-0.5 bg-white/30 transition-all duration-100"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="px-3 py-2.5">
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-2">
            <span className="text-xl leading-none">{alert.icon}</span>
            <span className="text-xs font-bold text-white leading-tight">{alert.title}</span>
          </div>
          <button
            onClick={onDismiss}
            className="text-gray-500 hover:text-white text-sm leading-none flex-shrink-0 mt-0.5"
          >✕</button>
        </div>

        {/* Position context */}
        {(alert.hero_pos || alert.villain_pos) && (
          <div className="flex items-center gap-1.5 mb-2 flex-wrap">
            {alert.hero_pos && (
              <span className="text-xs bg-green-900 text-green-300 px-1.5 py-0.5 rounded font-semibold">
                Você: {alert.hero_pos}
              </span>
            )}
            {alert.villain_pos && alert.villain && (
              <span className="text-xs bg-black/30 text-gray-300 px-1.5 py-0.5 rounded">
                vs {alert.villain} ({alert.villain_pos})
              </span>
            )}
          </div>
        )}

        {/* Action — the main message */}
        <p className="text-sm font-semibold text-white leading-snug mb-1.5">
          {alert.action}
        </p>

        {/* Detail */}
        {alert.detail && (
          <p className="text-xs text-gray-400 leading-relaxed">{alert.detail}</p>
        )}

        {/* Dismiss button */}
        <button
          onClick={onDismiss}
          className="w-full mt-2 text-xs text-gray-600 hover:text-gray-400 text-center"
        >
          Entendi
        </button>
      </div>
    </div>
  )
}
