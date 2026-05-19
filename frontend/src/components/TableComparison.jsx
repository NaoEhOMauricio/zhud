import { useState, useEffect } from 'react'

const API = 'http://127.0.0.1:8765'

const STAT_LABELS = {
  vpip:         'VPIP',
  pfr:          'PFR',
  threebet:     '3BET',
  af:           'AF',
  cbet:         'CBET',
  fold_to_cbet: 'F.CBET',
  steal:        'Steal',
  wtsd:         'WTSD',
}

const DIR_STYLE = {
  higher:  { color: 'text-red-400',   icon: '▲', bg: 'bg-red-950/40' },
  lower:   { color: 'text-blue-400',  icon: '▼', bg: 'bg-blue-950/40' },
  similar: { color: 'text-gray-400',  icon: '≈', bg: '' },
}

export default function TableComparison() {
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const r = await fetch(`${API}/active-tables/comparison`)
      const d = await r.json()
      if (d.error) { setError(d.error); setData(null) }
      else setData(d)
    } catch { setError('Backend não disponível') }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  if (loading) return <div className="text-center text-gray-600 text-xs py-6">Calculando...</div>
  if (error)   return (
    <div className="text-center text-gray-700 text-xs py-6 space-y-2">
      <div>{error}</div>
      <button onClick={load} className="text-green-700 hover:text-green-500 underline">Tentar novamente</button>
    </div>
  )
  if (!data) return null

  return (
    <div className="space-y-2">
      <div className="text-xs text-gray-500 mb-1">
        vs {data.opponents} oponentes em {data.table || 'mesa atual'}
      </div>

      <div className="space-y-1">
        {Object.entries(data.comparison || {}).map(([stat, vals]) => {
          const style = DIR_STYLE[vals.dir] || DIR_STYLE.similar
          const suffix = stat === 'af' ? '' : '%'
          return (
            <div key={stat} className={`flex items-center justify-between px-2 py-1.5 rounded ${style.bg}`}>
              <span className="text-xs text-gray-400 w-16">{STAT_LABELS[stat] || stat}</span>
              <div className="flex items-center gap-3 text-right">
                <div className="text-center">
                  <div className="text-xs font-bold text-white">{vals.hero}{suffix}</div>
                  <div className="text-xs text-gray-600">você</div>
                </div>
                <span className={`text-xs font-bold ${style.color}`}>{style.icon}</span>
                <div className="text-center">
                  <div className="text-xs font-bold text-gray-400">{vals.table}{suffix}</div>
                  <div className="text-xs text-gray-600">mesa</div>
                </div>
                <span className={`text-xs ${style.color} w-10 text-right`}>
                  {vals.diff > 0 ? '+' : ''}{vals.diff}{suffix}
                </span>
              </div>
            </div>
          )
        })}
      </div>

      <button onClick={load} className="w-full text-xs text-gray-600 hover:text-gray-400 py-1 underline">
        Atualizar
      </button>
    </div>
  )
}
