import { useState, useEffect } from 'react'

export default function TiltAlert({ alerts, onDismiss }) {
  if (!alerts || alerts.length === 0) return null
  const a = alerts[0]

  const color = a.tilt_score >= 80 ? 'border-red-600 bg-red-950'
              : a.tilt_score >= 60 ? 'border-orange-600 bg-orange-950'
              : 'border-yellow-600 bg-yellow-950'
  const textColor = a.tilt_score >= 80 ? 'text-red-300'
                  : a.tilt_score >= 60 ? 'text-orange-300'
                  : 'text-yellow-300'

  return (
    <div className={`mx-2 mt-1 mb-0 rounded border ${color} px-3 py-2 flex items-start justify-between gap-2`}>
      <div className="flex-1 min-w-0">
        <div className={`text-xs font-bold ${textColor} flex items-center gap-1`}>
          <span className="pulse-live inline-block w-2 h-2 rounded-full bg-current" />
          TILT DETECTADO — {a.nickname}
        </div>
        <div className="text-xs text-gray-300 mt-0.5">
          {a.tilt_label} · VPIP recente {a.recent_vpip}% (+{a.delta}% vs histórico)
        </div>
      </div>
      <button
        onClick={() => onDismiss(a.nickname)}
        className="text-gray-500 hover:text-gray-300 text-xs flex-shrink-0 mt-0.5"
      >✕</button>
    </div>
  )
}
