import { useState, useEffect } from 'react'

const API = 'http://127.0.0.1:8765'

function fmt(min) {
  if (!min) return '—'
  if (min < 60) return `${Math.round(min)}min`
  return `${Math.floor(min / 60)}h ${Math.round(min % 60)}min`
}

export default function SessionPanel() {
  const [current, setCurrent] = useState(null)
  const [history, setHistory] = useState([])

  useEffect(() => {
    const load = () => {
      fetch(`${API}/session/current`).then(r => r.json()).then(setCurrent).catch(() => {})
      fetch(`${API}/sessions`).then(r => r.json()).then(setHistory).catch(() => {})
    }
    load()
    const t = setInterval(load, 15000)
    return () => clearInterval(t)
  }, [])

  return (
    <div className="flex-1 overflow-y-auto px-3 py-2 space-y-3">

      {/* Current session */}
      <div>
        <div className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wider">Sessão Atual</div>
        {current?.active ? (
          <div className="bg-gray-900 rounded-lg border border-green-800 p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-green-500 font-semibold flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-green-500 pulse-live inline-block" />
                Ativa
              </span>
              <span className="text-xs text-gray-400">{fmt(current.duration_min)}</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-center">
              <div className="bg-gray-800 rounded p-2">
                <div className="text-lg font-bold text-white">{current.hands}</div>
                <div className="text-xs text-gray-500">mãos</div>
              </div>
              <div className="bg-gray-800 rounded p-2">
                <div className="text-sm font-bold text-gray-300 capitalize">{current.game_type === 'tournament' ? 'Torneio' : 'Cash'}</div>
                <div className="text-xs text-gray-500">formato</div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center text-gray-700 text-xs py-4 bg-gray-900 rounded-lg">Nenhuma sessão ativa</div>
        )}
      </div>

      {/* History */}
      <div>
        <div className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wider">Sessões Anteriores</div>
        {history.length === 0 ? (
          <div className="text-center text-gray-700 text-xs py-4">Nenhuma sessão registrada</div>
        ) : (
          <div className="space-y-1">
            {history.map(s => (
              <div key={s.id} className="bg-gray-900 rounded px-3 py-2 flex items-center justify-between">
                <div>
                  <div className="text-xs text-gray-300">
                    {new Date(s.start).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}
                    {' '}
                    {new Date(s.start).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                  </div>
                  <div className="text-xs text-gray-600">{fmt(s.duration_min)}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold text-white">{s.hands}</div>
                  <div className="text-xs text-gray-600">mãos</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
