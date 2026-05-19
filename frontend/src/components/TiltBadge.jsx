export default function TiltBadge({ tilt }) {
  if (!tilt || tilt.label === 'Sem dados' || tilt.label === 'Normal') return null
  if (tilt.label === 'Sem dados (HU/3-max)') return null  // HU filtered — no false positives

  const styles = {
    Leve:     { dot: 'bg-yellow-400',  text: 'text-yellow-400',  bg: 'bg-yellow-950' },
    Moderado: { dot: 'bg-orange-400',  text: 'text-orange-400',  bg: 'bg-orange-950' },
    Severo:   { dot: 'bg-red-400',     text: 'text-red-400',     bg: 'bg-red-950' },
  }
  const s = styles[tilt.label] || styles.Leve

  return (
    <div className={`mx-3 mb-2 ${s.bg} rounded px-2 py-1.5 border border-opacity-30`}
         style={{ borderColor: 'currentColor' }}>
      <div className="flex items-center gap-1.5">
        <span className={`w-2 h-2 rounded-full flex-shrink-0 pulse-live ${s.dot}`} />
        <span className={`text-xs font-bold ${s.text}`}>TILT {tilt.label.toUpperCase()}</span>
        <span className="text-xs text-gray-400 ml-auto">
          +{tilt.delta > 0 ? tilt.delta : 0}% VPIP recente
        </span>
      </div>
      <div className="text-xs text-gray-400 mt-0.5">
        Rec. {tilt.recent_vpip}% vs base {Math.round(tilt.recent_vpip - tilt.delta)}%
        <span className="text-gray-600"> — últimas 15 mãos</span>
      </div>
    </div>
  )
}
