import { useState, useEffect, useRef } from 'react'

const API = 'http://127.0.0.1:8765'

const RANKS = ['A','K','Q','J','T','9','8','7','6','5','4','3','2']

const RESULT_BG = {
  red:    'bg-red-950 border-red-700 text-red-300',
  orange: 'bg-orange-950 border-orange-700 text-orange-300',
  yellow: 'bg-yellow-950/60 border-yellow-700 text-yellow-300',
  blue:   'bg-blue-950 border-blue-700 text-blue-300',
  gray:   'bg-gray-900 border-gray-700 text-gray-400',
}

function CardPicker({ position, stackBb, nPlayers }) {
  const [r1, setR1]         = useState('A')
  const [r2, setR2]         = useState('K')
  const [suited, setSuited] = useState(true)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const isPair = r1 === r2

  const evaluate = async () => {
    if (!position) return
    setLoading(true)
    try {
      const r = await fetch(
        `${API}/range-tips/evaluate?r1=${r1}&r2=${r2}&suited=${isPair ? false : suited}&position=${position}&stack_bb=${stackBb}&n_players=${nPlayers}`
      )
      setResult(await r.json())
    } catch {}
    setLoading(false)
  }

  useEffect(() => { if (position) evaluate() }, [r1, r2, suited, position, stackBb, nPlayers])

  const bgClass = result ? (RESULT_BG[result.color] || RESULT_BG.gray) : ''

  return (
    <div className="space-y-2">
      <div className="text-xs text-gray-500 uppercase tracking-wider">Minhas cartas</div>

      {/* Rank selectors */}
      <div className="flex items-center gap-2">
        <div className="flex-1">
          <div className="text-xs text-gray-600 mb-1">Carta 1</div>
          <div className="grid grid-cols-7 gap-0.5">
            {RANKS.map(r => (
              <button key={r} onClick={() => setR1(r)}
                className={`py-1 rounded text-xs font-bold transition-colors ${
                  r1 === r ? 'bg-white text-gray-900' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}>{r}</button>
            ))}
          </div>
        </div>
        <div className="flex-1">
          <div className="text-xs text-gray-600 mb-1">Carta 2</div>
          <div className="grid grid-cols-7 gap-0.5">
            {RANKS.map(r => (
              <button key={r} onClick={() => setR2(r)}
                className={`py-1 rounded text-xs font-bold transition-colors ${
                  r2 === r ? 'bg-white text-gray-900' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}>{r}</button>
            ))}
          </div>
        </div>
      </div>

      {/* Suited toggle */}
      {!isPair && (
        <div className="flex gap-2">
          <button onClick={() => setSuited(true)}
            className={`flex-1 py-1 rounded text-xs font-bold border transition-colors ${suited ? 'bg-blue-900 border-blue-600 text-blue-300' : 'border-gray-700 text-gray-600'}`}>
            Suited (s)
          </button>
          <button onClick={() => setSuited(false)}
            className={`flex-1 py-1 rounded text-xs font-bold border transition-colors ${!suited ? 'bg-gray-700 border-gray-500 text-gray-300' : 'border-gray-700 text-gray-600'}`}>
            Offsuit (o)
          </button>
        </div>
      )}

      {/* Result */}
      {loading && <div className="text-center text-gray-600 text-xs py-2">...</div>}
      {result && !loading && (
        <div className={`rounded-lg border px-3 py-2.5 ${bgClass}`}>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-xl font-black tracking-widest">{result.hand}</span>
            <span className={`text-xs font-bold px-2 py-0.5 rounded flex-shrink-0 ${
              result.in_range ? 'bg-green-900 text-green-300' : 'bg-gray-800 text-gray-500'
            }`}>
              {result.in_range ? '✓ NO RANGE' : '✕ FORA'}
            </span>
          </div>
          {result.group && (
            <div className="text-xs font-bold mb-1">{result.group}</div>
          )}
          {result.advice && (
            <div className="text-xs opacity-90 leading-relaxed">{result.advice}</div>
          )}
        </div>
      )}

      {!position && (
        <div className="text-center text-gray-700 text-xs py-2">Selecione sua posição primeiro</div>
      )}
    </div>
  )
}

// All positions per table size, in BTN-rotation order (index 0 = BTN)
const TABLE_POSITIONS = {
  9: [
    {label:'BTN',   value:'btn'}, {label:'SB',    value:'sb'}, {label:'BB',    value:'bb'},
    {label:'UTG',   value:'ep'}, {label:'UTG+1', value:'ep'}, {label:'UTG+2', value:'ep'},
    {label:'LJ',    value:'hj'}, {label:'HJ',    value:'hj'}, {label:'CO',    value:'co'},
  ],
  8: [
    {label:'BTN',   value:'btn'}, {label:'SB',    value:'sb'}, {label:'BB',    value:'bb'},
    {label:'UTG',   value:'ep'}, {label:'UTG+1', value:'ep'}, {label:'MP',    value:'ep'},
    {label:'HJ',    value:'hj'}, {label:'CO',    value:'co'},
  ],
  7: [
    {label:'BTN',   value:'btn'}, {label:'SB',    value:'sb'}, {label:'BB',    value:'bb'},
    {label:'UTG',   value:'ep'}, {label:'MP',    value:'ep'},
    {label:'HJ',    value:'hj'}, {label:'CO',    value:'co'},
  ],
  6: [
    {label:'BTN',   value:'btn'}, {label:'SB',    value:'sb'}, {label:'BB',    value:'bb'},
    {label:'UTG',   value:'ep'}, {label:'HJ',    value:'hj'}, {label:'CO',    value:'co'},
  ],
  5: [
    {label:'BTN',   value:'btn'}, {label:'SB',    value:'sb'}, {label:'BB',    value:'bb'},
    {label:'UTG',   value:'ep'}, {label:'CO',    value:'co'},
  ],
  4: [
    {label:'BTN',   value:'btn'}, {label:'SB',    value:'sb'}, {label:'BB',    value:'bb'},
    {label:'CO',    value:'co'},
  ],
  3: [
    {label:'BTN',   value:'btn'}, {label:'SB',    value:'sb'}, {label:'BB',    value:'bb'},
  ],
}

// Rotate position: BTN moves forward 1 each hand, so hero moves back 1 in the list
function rotatePosition(currentLabel, tableSize) {
  const positions = TABLE_POSITIONS[tableSize] || TABLE_POSITIONS[6]
  const idx = positions.findIndex(p => p.label === currentLabel)
  if (idx === -1) return positions[0]
  // Going "back" one step = moving further from BTN = prev index with wrap
  const prevIdx = (idx - 1 + positions.length) % positions.length
  return positions[prevIdx]
}

const POS_COLOR = {
  btn:'text-green-400', co:'text-blue-400', hj:'text-yellow-400',
  ep:'text-gray-300',   sb:'text-orange-400', bb:'text-purple-400',
}

function TipCard({ tip, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="rounded border border-gray-800 overflow-hidden">
      <button onClick={() => setOpen(o => !o)}
        className="w-full text-left px-3 py-2 flex items-start gap-2 hover:bg-gray-800/50 transition-colors">
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

export default function RangeTips({ heroHandCount = 0 }) {
  const _saved = (() => { try { return JSON.parse(localStorage.getItem('zhud_range') || '{}') } catch { return {} } })()
  const [tableSize,    setTableSize]    = useState(_saved.tableSize || 6)
  const [posEntry,     setPosEntry]     = useState(_saved.posEntry  || null)
  const [stackBb,      setStackBb]      = useState(_saved.stackBb   || 40)
  const [data,         setData]         = useState(null)
  const [loading,      setLoading]      = useState(false)
  const [autoSuggestion, setAutoSuggestion] = useState(null)  // from HH detection
  const prevHandCount = useRef(heroHandCount)

  const positions = TABLE_POSITIONS[tableSize] || TABLE_POSITIONS[6]

  // Persist settings to localStorage whenever they change
  useEffect(() => {
    try { localStorage.setItem('zhud_range', JSON.stringify({ tableSize, posEntry, stackBb })) } catch {}
  }, [tableSize, posEntry, stackBb])

  // Notify backend of confirmed position so live alerts use it (not the unreliable HH prediction)
  useEffect(() => {
    if (!posEntry) return
    fetch(`${API}/hero/set-position`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pos: posEntry.value, pos_label: posEntry.label, n_players: tableSize }),
    }).catch(() => {})
  }, [posEntry, tableSize])

  // When a new hand is processed for hero, rotate position automatically
  useEffect(() => {
    if (heroHandCount > prevHandCount.current && posEntry) {
      const next = rotatePosition(posEntry.label, tableSize)
      setPosEntry(next)
    }
    prevHandCount.current = heroHandCount
  }, [heroHandCount])

  // Try to auto-detect from HH as suggestion only
  useEffect(() => {
    fetch(`${API}/live-alerts`)
      .then(r => r.json())
      .then(d => {
        const np    = d.n_players || 6
        const label = d.hero_next_label || d.hero_pos_label || null
        const stack = d.hero_stack ? Math.round(d.hero_stack) : null
        if (label) {
          setAutoSuggestion({ label, np, stack })
          if (!posEntry) setStackBb(stack || 40)
        }
      })
      .catch(() => {})
  }, [])

  // Load range tips when position/stack/size changes
  useEffect(() => {
    if (!posEntry) return
    setLoading(true)
    const label = encodeURIComponent(posEntry.label)
    fetch(`${API}/range-tips?position=${posEntry.value}&stack_bb=${stackBb}&n_players=${tableSize}&pos_label=${label}`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [posEntry, stackBb, tableSize])

  const applyAutoSuggestion = () => {
    if (!autoSuggestion) return
    const np = autoSuggestion.np
    const targetPositions = TABLE_POSITIONS[np] || TABLE_POSITIONS[6]
    const found = targetPositions.find(p => p.label === autoSuggestion.label)
    setTableSize(np)
    setPosEntry(found || targetPositions[0])
    if (autoSuggestion.stack) setStackBb(autoSuggestion.stack)
  }

  return (
    <div className="flex-1 overflow-y-auto px-3 py-2 space-y-3">

      {/* Auto-suggestion banner */}
      {autoSuggestion && !posEntry && (
        <button
          onClick={applyAutoSuggestion}
          className="w-full text-left bg-green-950/50 border border-green-800 rounded-lg px-3 py-2"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
              <span className="text-xs text-green-400 font-semibold">
                Detectado: {autoSuggestion.label} · {autoSuggestion.stack}BB · {autoSuggestion.np}max
              </span>
            </div>
            <span className="text-xs text-green-600">Usar →</span>
          </div>
          <div className="text-xs text-gray-600 mt-0.5">Clique para aplicar a detecção automática</div>
        </button>
      )}

      {/* Table size selector */}
      <div>
        <div className="text-xs text-gray-500 mb-1">Jogadores na mesa</div>
        <div className="flex gap-1">
          {[3,4,5,6,7,8,9].map(n => (
            <button key={n}
              onClick={() => { setTableSize(n); setPosEntry(null) }}
              className={`flex-1 py-1 rounded text-xs font-bold transition-colors ${
                tableSize === n
                  ? 'bg-blue-900 text-blue-300 border border-blue-700'
                  : 'text-gray-600 hover:text-gray-400 border border-transparent'
              }`}
            >{n}</button>
          ))}
        </div>
      </div>

      {/* Position selector — all positions for this table size */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <div className="text-xs text-gray-500">Sua posição agora</div>
          {posEntry && (
            <div className="text-xs text-gray-600">
              Rotaciona automático por mão ↻
            </div>
          )}
        </div>
        <div className={`grid gap-1 ${positions.length <= 6 ? 'grid-cols-3' : positions.length <= 8 ? 'grid-cols-4' : 'grid-cols-5'}`}>
          {positions.map(p => (
            <button key={p.label}
              onClick={() => setPosEntry(p)}
              className={`py-1.5 rounded text-xs font-bold transition-colors ${
                posEntry?.label === p.label
                  ? `${POS_COLOR[p.value]} bg-gray-800 border border-gray-500`
                  : 'text-gray-600 hover:text-gray-300 border border-gray-800'
              }`}
            >{p.label}</button>
          ))}
        </div>
        {autoSuggestion && posEntry && (
          <button onClick={applyAutoSuggestion}
            className="mt-1 text-xs text-green-700 hover:text-green-500 underline">
            ← Usar detecção automática ({autoSuggestion.label}, {autoSuggestion.stack}BB)
          </button>
        )}
      </div>

      {/* Stack input */}
      <div className="flex items-center gap-2">
        <div className="text-xs text-gray-500 flex-shrink-0">Stack (BB):</div>
        <input type="number" min={1} max={300} step={1} value={stackBb}
          onChange={e => setStackBb(parseFloat(e.target.value) || 40)}
          className="w-20 bg-gray-800 text-white text-xs px-2 py-1 rounded border border-gray-700 focus:outline-none focus:border-green-500" />
        {posEntry && (
          <div className={`text-xs font-bold ml-auto ${POS_COLOR[posEntry.value]}`}>
            {posEntry.label} · {stackBb}BB
          </div>
        )}
      </div>

      {/* Card picker — always visible once position is set */}
      <div className="border-t border-gray-800 pt-3">
        <CardPicker
          position={posEntry?.value || null}
          stackBb={stackBb}
          nPlayers={tableSize}
        />
      </div>

      {!posEntry && (
        <div className="text-center text-gray-600 text-xs py-4">
          Selecione o número de jogadores e sua posição atual
        </div>
      )}

      {loading && posEntry && (
        <div className="text-center text-gray-600 text-xs py-4">Carregando...</div>
      )}

      {data && posEntry && !loading && (
        <>
          {/* Hand action groups */}
          {(data.hand_groups || []).length > 0 && (
            <div>
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-1.5 px-0.5">
                O que fazer com cada mão
              </div>
              <div className="space-y-1">
                {data.hand_groups.map((g, i) => {
                  const colors = {
                    red:    {bar:'bg-red-500',    label:'text-red-300',    bg:'bg-red-950/50 border-red-900'},
                    orange: {bar:'bg-orange-400', label:'text-orange-300', bg:'bg-orange-950/50 border-orange-900'},
                    yellow: {bar:'bg-yellow-500', label:'text-yellow-300', bg:'bg-yellow-950/30 border-yellow-900/50'},
                    blue:   {bar:'bg-blue-400',   label:'text-blue-300',   bg:'bg-blue-950/40 border-blue-900'},
                    gray:   {bar:'bg-gray-600',   label:'text-gray-500',   bg:'bg-gray-900 border-gray-800'},
                  }[g.color] || {bar:'bg-gray-600', label:'text-gray-400', bg:'bg-gray-900 border-gray-800'}
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
            <div className={`rounded-lg px-3 py-2 bg-gray-900 border ${data.is_ip ? 'border-green-800' : 'border-gray-700'}`}>
              <div className="flex items-center justify-between mb-1">
                <span className={`text-xs font-bold ${POS_COLOR[posEntry.value]}`}>{data.pos_label || data.label}</span>
                <span className={`text-sm font-black ${data.is_ip ? 'text-green-400' : 'text-gray-300'}`}>{data.open_pct}%</span>
              </div>
              <p className="text-xs text-gray-400 leading-relaxed">{data.open_hands}</p>
              {data.is_ip && <span className="text-xs text-green-700 mt-0.5 block">IP — posição vantajosa ✓</span>}
            </div>
          )}

          {/* BB defense */}
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

          {/* Warnings */}
          {(data.warnings || []).length > 0 && (
            <div className="space-y-1.5">
              <div className="text-xs font-semibold text-orange-600 uppercase tracking-wider">Ajuste no seu jogo</div>
              {data.warnings.map((w, i) => <TipCard key={i} tip={w} defaultOpen={i === 0} />)}
            </div>
          )}

          {/* Tips */}
          {(data.tips || []).length > 0 && (
            <div className="space-y-1.5">
              <div className="text-xs font-semibold text-blue-500 uppercase tracking-wider">Dicas para esta posição</div>
              {data.tips.map((t, i) => <TipCard key={i} tip={t} defaultOpen={i === 0} />)}
            </div>
          )}
        </>
      )}
    </div>
  )
}
