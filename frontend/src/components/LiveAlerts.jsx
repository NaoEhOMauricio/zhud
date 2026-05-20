import { useState, useEffect } from 'react'

const API = 'http://127.0.0.1:8765'

const POSITIONS = [
  { v: 'ep',  l: 'UTG' },
  { v: 'hj',  l: 'HJ'  },
  { v: 'co',  l: 'CO'  },
  { v: 'btn', l: 'BTN' },
  { v: 'sb',  l: 'SB'  },
  { v: 'bb',  l: 'BB'  },
]

const PRIORITY_STYLE = {
  1: 'border-red-800 bg-red-950',
  2: 'border-orange-800 bg-orange-950',
  3: 'border-gray-700 bg-gray-900',
}

const STARS = (n) => '★'.repeat(n) + '☆'.repeat(5 - n)
const QUALITY_COLOR = { 1:'text-red-400', 2:'text-orange-400', 3:'text-yellow-400', 4:'text-green-400', 5:'text-green-300' }

export default function LiveAlerts() {
  const [pos, setPos]       = useState('btn')
  const [stack, setStack]   = useState(40)
  const [data, setData]     = useState(null)
  const [loading, setLoad]  = useState(false)
  const [expanded, setExp]  = useState({})

  const load = async () => {
    setLoad(true)
    try {
      const r = await fetch(`${API}/live-alerts?position=${pos}&stack_bb=${stack}`)
      setData(await r.json())
    } catch {}
    setLoad(false)
  }

  useEffect(() => { load() }, [pos, stack])

  const toggle = (i) => setExp(e => ({ ...e, [i]: !e[i] }))

  return (
    <div className="space-y-3 px-3 py-2">

      {/* Controls */}
      <div className="flex gap-2">
        <div className="flex-1">
          <div className="text-xs text-gray-500 mb-1">Minha posição agora</div>
          <div className="grid grid-cols-3 gap-1">
            {POSITIONS.map(p => (
              <button key={p.v} onClick={() => setPos(p.v)}
                className={`py-1 rounded text-xs font-bold transition-colors ${
                  pos === p.v ? 'bg-green-900 text-green-300 border border-green-700' : 'text-gray-600 hover:text-gray-400'
                }`}
              >{p.l}</button>
            ))}
          </div>
        </div>
        <div className="w-20">
          <div className="text-xs text-gray-500 mb-1">Stack (BB)</div>
          <input type="number" min={1} max={200} step={1} value={stack}
            onChange={e => setStack(parseFloat(e.target.value) || 40)}
            className="w-full bg-gray-800 text-white text-xs px-2 py-1.5 rounded border border-gray-700 focus:outline-none focus:border-green-500"
          />
        </div>
      </div>

      {loading && <div className="text-center text-gray-600 text-xs py-3">Analisando...</div>}

      {data && !loading && (
        <>
          {/* Table quality */}
          {data.quality && (
            <div className="bg-gray-900 rounded-lg px-3 py-2 border border-gray-800 flex items-center justify-between">
              <div>
                <div className="text-xs text-gray-500 mb-0.5">Qualidade da mesa</div>
                <div className={`text-sm font-bold ${QUALITY_COLOR[data.quality.stars] || 'text-gray-400'}`}>
                  {STARS(data.quality.stars)} {data.quality.label}
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-gray-600">VPIP médio</div>
                <div className="text-sm font-bold text-gray-300">{data.quality.avg_vpip}%</div>
              </div>
            </div>
          )}
          {data.quality?.reason && (
            <div className="text-xs text-gray-600 -mt-2 px-1 leading-snug">{data.quality.reason}</div>
          )}

          {/* Alerts */}
          {(data.alerts || []).length === 0 && (
            <div className="text-center text-gray-700 text-xs py-4">
              Nenhuma oportunidade detectada no momento
            </div>
          )}

          {(data.alerts || []).map((alert, i) => (
            <div key={i} className={`rounded-lg border overflow-hidden ${PRIORITY_STYLE[alert.priority] || PRIORITY_STYLE[3]}`}>
              <button
                onClick={() => toggle(i)}
                className="w-full text-left px-3 py-2 flex items-start gap-2"
              >
                <span className="text-base flex-shrink-0">{alert.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-bold text-white leading-tight">{alert.title}</div>
                  <div className="text-xs text-gray-300 mt-0.5 leading-snug">{alert.action}</div>
                </div>
                <span className="text-gray-600 text-xs flex-shrink-0">{expanded[i] ? '▲' : '▼'}</span>
              </button>
              {expanded[i] && alert.reason && (
                <div className="px-3 pb-2 text-xs text-gray-500 leading-relaxed border-t border-current/10 pt-1.5">
                  {alert.reason}
                </div>
              )}
            </div>
          ))}

          <button onClick={load}
            className="w-full text-xs text-gray-700 hover:text-gray-500 underline text-center py-1"
          >
            Atualizar alertas
          </button>
        </>
      )}
    </div>
  )
}
