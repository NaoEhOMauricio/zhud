import { useState } from 'react'

const API = 'http://127.0.0.1:8765'

const POSITIONS = ['BTN', 'CO', 'HJ', 'UTG', 'SB', 'BB']

export default function PushFoldHelper() {
  const [position, setPosition] = useState('BTN')
  const [stackBb, setStackBb]   = useState(10)
  const [result, setResult]     = useState(null)
  const [loading, setLoading]   = useState(false)

  const lookup = async () => {
    setLoading(true)
    try {
      const r = await fetch(`${API}/push-fold?position=${position}&stack_bb=${stackBb}`)
      setResult(await r.json())
    } catch {}
    setLoading(false)
  }

  const actionColor = {
    push:   'border-red-700 bg-red-950 text-red-300',
    call:   'border-blue-700 bg-blue-950 text-blue-300',
    normal: 'border-green-800 bg-green-950 text-green-300',
  }[result?.action] || 'border-gray-700 bg-gray-900 text-gray-300'

  return (
    <div className="space-y-3">
      {/* Controls */}
      <div className="grid grid-cols-2 gap-2">
        <div>
          <div className="text-xs text-gray-500 mb-1">Posição</div>
          <select
            value={position}
            onChange={e => { setPosition(e.target.value); setResult(null) }}
            className="w-full bg-gray-800 text-white text-xs px-2 py-1.5 rounded border border-gray-700 focus:outline-none focus:border-green-500"
          >
            {POSITIONS.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        <div>
          <div className="text-xs text-gray-500 mb-1">Stack (BB)</div>
          <input
            type="number"
            min={1} max={30} step={0.5}
            value={stackBb}
            onChange={e => { setStackBb(parseFloat(e.target.value) || 10); setResult(null) }}
            className="w-full bg-gray-800 text-white text-xs px-2 py-1.5 rounded border border-gray-700 focus:outline-none focus:border-green-500"
          />
        </div>
      </div>

      <button
        onClick={lookup}
        disabled={loading}
        className="w-full bg-green-800 hover:bg-green-700 disabled:opacity-50 text-white text-sm py-2 rounded transition-colors font-medium"
      >
        {loading ? 'Calculando...' : 'Ver Recomendação'}
      </button>

      {/* Result */}
      {result && (
        <div className={`rounded border ${actionColor} p-3 space-y-2`}>
          {result.action !== 'normal' ? (
            <>
              <div className="flex items-center justify-between">
                <span className="text-lg font-black">{result.label || result.action.toUpperCase()}</span>
                <span className="text-sm font-bold">{result.push_pct}% das mãos</span>
              </div>
              <div className="text-xs leading-relaxed border-t border-current/20 pt-2">
                <div className="font-semibold mb-0.5">Range:</div>
                <div className="text-gray-300">{result.hands}</div>
              </div>
              {result.advice && (
                <div className="text-xs text-gray-400 border-t border-current/20 pt-2 leading-relaxed">
                  {result.advice}
                </div>
              )}
            </>
          ) : (
            <div className="text-center">
              <div className="text-sm font-bold mb-1">Jogo Normal</div>
              <div className="text-xs text-gray-400">{result.advice}</div>
            </div>
          )}
        </div>
      )}

      <div className="text-xs text-gray-700 text-center leading-relaxed">
        Ranges baseados em ICM/Nash para 6-max Hyper-Turbo.
        Ajuste para ICM final de torneio quando aplicável.
      </div>
    </div>
  )
}
