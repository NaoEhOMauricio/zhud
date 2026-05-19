import { useState, useEffect } from 'react'

export default function UpdateBanner() {
  const [state, setState] = useState(null) // null | 'available' | 'downloaded'

  useEffect(() => {
    if (!window.zhud) return
    window.zhud.onUpdateAvailable  (() => setState('available'))
    window.zhud.onUpdateDownloaded (() => setState('downloaded'))
  }, [])

  if (!state) return null

  if (state === 'downloaded') return (
    <div className="flex-shrink-0 bg-green-900 border-b border-green-700 px-3 py-2 flex items-center justify-between gap-2">
      <div>
        <div className="text-xs font-bold text-green-300">Atualização pronta!</div>
        <div className="text-xs text-green-500">Reinicie para instalar a nova versão</div>
      </div>
      <button
        onClick={() => window.zhud?.restartToUpdate?.()}
        className="text-xs bg-green-700 hover:bg-green-600 text-white px-3 py-1 rounded transition-colors flex-shrink-0"
      >
        Reiniciar
      </button>
    </div>
  )

  return (
    <div className="flex-shrink-0 bg-blue-950 border-b border-blue-800 px-3 py-1.5 flex items-center gap-2">
      <span className="text-xs text-blue-400 pulse-live">⬇</span>
      <span className="text-xs text-blue-300">Baixando atualização...</span>
    </div>
  )
}
