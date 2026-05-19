import { useState, useEffect } from 'react'

const API = 'http://127.0.0.1:8765'

const REASON_LABEL = {
  allin:    { label: 'All-In', color: 'bg-red-900 text-red-300' },
  showdown: { label: 'Showdown', color: 'bg-blue-900 text-blue-300' },
  big_pot:  { label: 'Pote grande', color: 'bg-orange-900 text-orange-300' },
}

const STREET_LABEL = { preflop: 'PF', flop: 'F', turn: 'T', river: 'R', showdown: 'SD' }

export default function HandHighlight({ nickname }) {
  const [hands, setHands]   = useState([])
  const [open, setOpen]     = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!nickname) return
    setLoading(true)
    fetch(`${API}/player/${encodeURIComponent(nickname)}/hands?limit=15`)
      .then(r => r.json())
      .then(d => { setHands(Array.isArray(d) ? d : []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [nickname])

  if (loading) return <div className="text-center text-gray-600 text-xs py-4">Carregando...</div>
  if (!hands.length) return <div className="text-center text-gray-700 text-xs py-4">Nenhuma mão registrada</div>

  return (
    <div className="space-y-1 max-h-60 overflow-y-auto">
      {hands.map(h => {
        const r = REASON_LABEL[h.reason] || { label: h.reason, color: 'bg-gray-800 text-gray-400' }
        const isOpen = open === h.hand_id
        return (
          <div key={h.hand_id} className="rounded border border-gray-800 overflow-hidden">
            <button
              className="w-full text-left px-3 py-2 flex items-center gap-2 hover:bg-gray-800 transition-colors"
              onClick={() => setOpen(isOpen ? null : h.hand_id)}
            >
              <span className={`text-xs px-1.5 py-0.5 rounded ${r.color} flex-shrink-0`}>{r.label}</span>
              <span className="text-xs text-gray-300 flex-1 truncate">{h.summary}</span>
              <span className="text-xs text-gray-600 flex-shrink-0">{h.pot > 0 ? `${h.pot} fichas` : ''}</span>
            </button>
            {isOpen && (
              <div className="px-3 pb-2 bg-gray-900">
                <div className="text-xs text-gray-600 mb-1">Últimas ações:</div>
                <div className="flex flex-wrap gap-1">
                  {(h.actions || []).map((a, i) => (
                    <span key={i} className="text-xs bg-gray-800 rounded px-1.5 py-0.5">
                      <span className="text-gray-500">{STREET_LABEL[a.s] || a.s} </span>
                      <span className="text-gray-300">{a.p?.split(' ')[0]}</span>
                      <span className="text-gray-500"> {a.a}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
