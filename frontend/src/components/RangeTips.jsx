import { useState, useEffect } from 'react'

const API = 'http://127.0.0.1:8765'

const POSITIONS = [
  { value: 'ep',  label: 'UTG' },
  { value: 'hj',  label: 'HJ'  },
  { value: 'co',  label: 'CO'  },
  { value: 'btn', label: 'BTN' },
  { value: 'sb',  label: 'SB'  },
  { value: 'bb',  label: 'BB'  },
]

const POS_COLOR = {
  btn: 'text-green-400',
  co:  'text-blue-400',
  hj:  'text-yellow-400',
  ep:  'text-gray-400',
  sb:  'text-orange-400',
  bb:  'text-purple-400',
}

function TipCard({ tip, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="rounded border border-gray-800 overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full text-left px-3 py-2 flex items-start gap-2 hover:bg-gray-800/50 transition-colors"
      >
        <span className="text-sm flex-shrink-0 mt-0.5">{tip.icon}</span>
        <span className="text-xs font-semibold text-white flex-1 leading-snug">{tip.title}</span>
        <span className="text-gray-600 text-xs flex-shrink-0">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="px-3 pb-3 space-y-1.5">
          <p className="text-xs text-gray-300 leading-relaxed">{tip.body}</p>
          {tip.detail && (
            <p className="text-xs text-gray-500 leading-relaxed border-t border-gray-800 pt-1.5">{tip.detail}</p>
          )}
        </div>
      )}
    </div>
  )
}

export default function RangeTips() {
  const [position, setPosition] = useState('btn')
  const [stackBb, setStackBb]   = useState(40)
  const [data, setData]         = useState(null)
  const [loading, setLoading]   = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const r = await fetch(
        `${API}/range-tips?position=${position}&stack_bb=${stackBb}`
      )
      setData(await r.json())
    } catch {}
    setLoading(false)
  }

  useEffect(() => { load() }, [position, stackBb])

  return (
    <div className="flex-1 overflow-y-auto px-3 py-2 space-y-3">

      {/* Position + Stack selector */}
      <div className="flex gap-2">
        <div className="flex-1">
          <div className="text-xs text-gray-500 mb-1">Minha posição</div>
          <div className="grid grid-cols-3 gap-1">
            {POSITIONS.map(p => (
              <button
                key={p.value}
                onClick={() => setPosition(p.value)}
                className={`py-1 rounded text-xs font-bold transition-colors ${
                  position === p.value
                    ? `${POS_COLOR[p.value]} bg-gray-800 border border-gray-600`
                    : 'text-gray-600 hover:text-gray-400'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
        <div className="w-20">
          <div className="text-xs text-gray-500 mb-1">Stack (BB)</div>
          <input
            type="number"
            min={1} max={200} step={1}
            value={stackBb}
            onChange={e => setStackBb(parseFloat(e.target.value) || 40)}
            className="w-full bg-gray-800 text-white text-xs px-2 py-1.5 rounded border border-gray-700 focus:outline-none focus:border-green-500"
          />
        </div>
      </div>

      {loading && (
        <div className="text-center text-gray-600 text-xs py-4">Carregando...</div>
      )}

      {data && !loading && (
        <>
          {/* Open range summary */}
          {data.open_pct > 0 && (
            <div className={`rounded-lg px-3 py-2 bg-gray-900 border ${
              data.is_ip ? 'border-green-800' : 'border-gray-700'
            }`}>
              <div className="flex items-center justify-between mb-1">
                <span className={`text-xs font-bold ${POS_COLOR[position]}`}>{data.label}</span>
                <span className={`text-sm font-black ${data.is_ip ? 'text-green-400' : 'text-gray-300'}`}>
                  {data.open_pct}%
                </span>
              </div>
              <p className="text-xs text-gray-400 leading-relaxed">{data.open_hands}</p>
              {data.is_ip && (
                <span className="text-xs text-green-700 mt-0.5 block">IP — posição vantajosa ✓</span>
              )}
            </div>
          )}

          {/* BB defense table */}
          {data.bb_defense && (
            <div>
              <div className="text-xs font-semibold text-purple-400 mb-1.5 uppercase tracking-wider">
                Defesa do BB por tamanho do raise
              </div>
              <div className="space-y-1">
                {data.bb_defense.map(row => (
                  <div key={row.size} className="bg-gray-900 rounded px-2 py-1.5">
                    <div className="flex items-center justify-between text-xs mb-0.5">
                      <span className="font-bold text-purple-300">{row.size}</span>
                      <span className="text-gray-500">equity mín: {row.equity}</span>
                    </div>
                    <p className="text-xs text-gray-400 leading-snug">{row.range}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Warnings (self-leaks) */}
          {(data.warnings || []).length > 0 && (
            <div className="space-y-1.5">
              <div className="text-xs font-semibold text-orange-600 uppercase tracking-wider">
                Ajuste no seu jogo
              </div>
              {data.warnings.map((w, i) => (
                <TipCard key={i} tip={w} defaultOpen={i === 0} />
              ))}
            </div>
          )}

          {/* Tips (opponent-based) */}
          {(data.tips || []).length > 0 && (
            <div className="space-y-1.5">
              <div className="text-xs font-semibold text-blue-500 uppercase tracking-wider">
                Dicas para esta posição
              </div>
              {data.tips.map((t, i) => (
                <TipCard key={i} tip={t} defaultOpen={i === 0} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
