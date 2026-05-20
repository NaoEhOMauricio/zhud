import { useState, useEffect, useCallback } from 'react'

const API = 'http://127.0.0.1:8765'

const POSITIONS = [
  { value: 'ep',  label: 'UTG' },
  { value: 'hj',  label: 'HJ'  },
  { value: 'co',  label: 'CO'  },
  { value: 'btn', label: 'BTN' },
  { value: 'sb',  label: 'SB'  },
  { value: 'bb',  label: 'BB'  },
]

// Map from live-alerts hero_pos (e.g. "BTN") to range-tips key (e.g. "btn")
const POS_MAP = { BTN:'btn', CO:'co', HJ:'hj', SB:'sb', BB:'bb', UTG:'ep', EP:'ep', MP:'ep' }

const POS_COLOR = {
  btn: 'text-green-400', co: 'text-blue-400', hj: 'text-yellow-400',
  ep:  'text-gray-400',  sb: 'text-orange-400', bb: 'text-purple-400',
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
  const [position, setPosition] = useState(null)   // null = waiting for detection
  const [stackBb,  setStackBb]  = useState(null)
  const [autoPos,  setAutoPos]  = useState(null)   // last auto-detected position
  const [autoStack,setAutoStack]= useState(null)
  const [data,     setData]     = useState(null)
  const [loading,  setLoading]  = useState(false)
  const [manual,   setManual]   = useState(false)  // user clicked manual override

  // Auto-detect from live-alerts (reads most recent HH file)
  const detectFromHH = useCallback(async () => {
    try {
      const r = await fetch(`${API}/live-alerts`)
      const d = await r.json()
      // Prefer next_pos (predicted for current hand) over hero_pos (last hand)
      const rawPos = d.hero_next_pos || d.hero_pos
      const pos    = POS_MAP[rawPos?.toUpperCase?.()] || null
      const stack  = d.hero_stack ? Math.round(d.hero_stack) : null
      if (pos) {
        setAutoPos(pos)
        if (!manual) setPosition(pos)
      }
      if (stack) {
        setAutoStack(stack)
        if (!manual) setStackBb(stack)
      }
    } catch {}
  }, [manual])

  // Detect on mount and every 15s
  useEffect(() => {
    detectFromHH()
    const t = setInterval(detectFromHH, 15000)
    return () => clearInterval(t)
  }, [detectFromHH])

  // Load range tips whenever position/stack changes
  useEffect(() => {
    if (!position || !stackBb) return
    setLoading(true)
    fetch(`${API}/range-tips?position=${position}&stack_bb=${stackBb}`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [position, stackBb])

  // Waiting for first detection
  if (!position && !manual) {
    return (
      <div className="px-3 py-4 text-center space-y-3">
        <div className="text-xs text-gray-500">Detectando sua posição na mesa...</div>
        <button
          onClick={() => { setManual(true); setPosition('btn'); setStackBb(40) }}
          className="text-xs text-gray-600 hover:text-gray-400 underline"
        >
          Selecionar manualmente
        </button>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-3 py-2 space-y-3">

      {/* Auto-detected badge OR manual mode selector */}
      {!manual && autoPos ? (
        <div className="bg-gray-900 rounded-lg px-3 py-2 border border-gray-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 flex-shrink-0" />
              <span className="text-xs text-gray-500">Posição estimada:</span>
              <span className={`text-sm font-bold ${POS_COLOR[position]}`}>
                {POSITIONS.find(p => p.value === position)?.label}
              </span>
              <span className="text-xs text-gray-600">·</span>
              <span className="text-xs text-gray-400 font-semibold">{stackBb}BB</span>
            </div>
            <button
              onClick={() => setManual(true)}
              className="text-xs text-gray-600 hover:text-gray-400 underline"
            >
              Editar
            </button>
          </div>
          <div className="text-xs text-gray-700 mt-0.5">
            Posição prevista para a mão atual (BTN rodou 1 cadeira)
          </div>
        </div>
      ) : (
        /* Manual selector */
        <div className="space-y-2">
          {autoPos && (
            <button
              onClick={() => { setManual(false); setPosition(autoPos); setStackBb(autoStack || stackBb) }}
              className="w-full text-xs text-green-700 hover:text-green-500 underline text-left"
            >
              ← Usar detecção automática ({POSITIONS.find(p => p.value === autoPos)?.label}, {autoStack}BB)
            </button>
          )}
          <div className="flex gap-2">
            <div className="flex-1">
              <div className="text-xs text-gray-500 mb-1">Posição</div>
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
                type="number" min={1} max={200} step={1}
                value={stackBb ?? 40}
                onChange={e => setStackBb(parseFloat(e.target.value) || 40)}
                className="w-full bg-gray-800 text-white text-xs px-2 py-1.5 rounded border border-gray-700 focus:outline-none focus:border-green-500"
              />
            </div>
          </div>
        </div>
      )}

      {loading && (
        <div className="text-center text-gray-600 text-xs py-4">Carregando...</div>
      )}

      {data && !loading && (
        <>
          {/* Hand action groups — "olhei as cartas, o que faço?" */}
          {(data.hand_groups || []).length > 0 && (
            <div>
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-1.5 px-0.5">
                O que fazer com cada mão
              </div>
              <div className="space-y-1">
                {data.hand_groups.map((g, i) => {
                  const colors = {
                    red:    { bar: 'bg-red-500',    label: 'text-red-300',    bg: 'bg-red-950/50 border-red-900' },
                    orange: { bar: 'bg-orange-400', label: 'text-orange-300', bg: 'bg-orange-950/50 border-orange-900' },
                    yellow: { bar: 'bg-yellow-500', label: 'text-yellow-300', bg: 'bg-yellow-950/30 border-yellow-900/50' },
                    blue:   { bar: 'bg-blue-400',   label: 'text-blue-300',   bg: 'bg-blue-950/40 border-blue-900' },
                    gray:   { bar: 'bg-gray-600',   label: 'text-gray-500',   bg: 'bg-gray-900 border-gray-800' },
                  }[g.color] || { bar: 'bg-gray-600', label: 'text-gray-400', bg: 'bg-gray-900 border-gray-800' }
                  return (
                    <div key={i} className={`rounded border ${colors.bg} overflow-hidden`}>
                      <div className="flex items-start gap-2 px-2.5 py-2">
                        <div className={`w-1 flex-shrink-0 rounded-full mt-0.5 self-stretch min-h-3 ${colors.bar}`} />
                        <div className="flex-1 min-w-0">
                          <div className={`text-xs font-bold leading-tight ${colors.label}`}>{g.label}</div>
                          <div className="text-xs text-gray-400 mt-0.5 leading-snug">{g.hands}</div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

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
