import { useState } from 'react'
import StatGrid from './StatGrid'
import BetSizingBar from './BetSizingBar'
import PositionStats from './PositionStats'
import TiltBadge from './TiltBadge'
import PushFoldHelper from './PushFoldHelper'
import TableComparison from './TableComparison'

const SEVERITY_STYLE = {
  3: { border:'border-red-800',    bg:'bg-red-950',    badge:'bg-red-900 text-red-300',       icon:'🔴', label:'CRÍTICO' },
  2: { border:'border-orange-800', bg:'bg-orange-950', badge:'bg-orange-900 text-orange-300', icon:'🟠', label:'MAJOR'   },
  1: { border:'border-yellow-800', bg:'bg-yellow-950', badge:'bg-yellow-900 text-yellow-300', icon:'🟡', label:'MENOR'   },
}
const GRADE_STYLE = { A:'text-green-400', B:'text-blue-400', C:'text-yellow-400', D:'text-orange-400', F:'text-red-400', '?':'text-gray-500' }

function LeakCard({ leak, index }) {
  const [open, setOpen] = useState(index === 0)
  const s = SEVERITY_STYLE[leak.severity] || SEVERITY_STYLE[1]
  return (
    <div className={`rounded border ${s.border} ${s.bg} overflow-hidden`}>
      <button className="w-full text-left px-3 py-2 flex items-center gap-2" onClick={() => setOpen(o => !o)}>
        <span className="text-xs">{s.icon}</span>
        <span className="text-xs font-semibold text-white flex-1 leading-tight">{leak.title}</span>
        <span className={`text-xs px-1.5 py-0.5 rounded ${s.badge} flex-shrink-0`}>{s.label}</span>
        <span className="text-gray-600 text-xs">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="px-3 pb-3 space-y-2">
          <p className="text-xs text-gray-300 leading-relaxed">{leak.detail}</p>
          <div className="flex items-start gap-1.5 bg-blue-950 rounded px-2 py-1.5 border border-blue-800">
            <span className="text-blue-400 text-xs mt-0.5 flex-shrink-0">→</span>
            <p className="text-xs text-blue-200 leading-relaxed">{leak.tip}</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default function HeroPanel({ hero, onClose, onChangeNick }) {
  const [tab, setTab] = useState('leaks')
  if (!hero) return null
  if (hero.error) {
    return (
      <div className="m-2 bg-gray-900 rounded-lg border border-gray-700 p-4 space-y-2">
        <div className="text-sm text-gray-400">{hero.error}</div>
        <button onClick={onChangeNick} className="text-xs text-green-500 hover:text-green-400 underline">Configurar nick</button>
      </div>
    )
  }

  const sa = hero.self_analysis || {}
  const leaks = sa.leaks || []
  const strengths = sa.strengths || []
  const grade = sa.grade || '?'
  const overall = sa.overall || ''

  const tabs = [
    { id: 'leaks',      label: `Leaks (${leaks.length})` },
    { id: 'stats',      label: 'Stats' },
    { id: 'position',   label: 'Posição' },
    { id: 'sizing',     label: 'Sizing' },
    { id: 'pushfold',   label: 'Push/Fold' },
    { id: 'comparison', label: 'vs Mesa' },
  ]

  return (
    <div className="m-2 bg-gray-900 rounded-lg border border-green-800 overflow-hidden">

      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-green-950 border-b border-green-800">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-green-400 text-sm">👤</span>
          <span className="font-bold text-white text-sm truncate max-w-[110px]">{hero.nickname}</span>
          <span className="text-xs text-green-700 font-semibold">SEU PERFIL</span>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <div className={`text-xl font-black leading-none ${GRADE_STYLE[grade]}`}>{grade}</div>
          <span className="text-xs text-gray-500">{hero.hands}m</span>
          {onClose && <button onClick={onClose} className="text-gray-500 hover:text-gray-200 text-sm ml-1">✕</button>}
        </div>
      </div>

      {/* Overall */}
      <div className="px-3 py-2 border-b border-gray-800">
        <p className="text-xs text-gray-300 leading-relaxed">{overall}</p>
        <p className="text-xs mt-1">
          {sa.using_recent
            ? <span className="text-green-700">Baseado nas últimas <strong className="text-green-500">{sa.window}</strong> mãos</span>
            : <span className="text-gray-600">Histórico completo ({hero.hands} mãos)</span>
          }
        </p>
      </div>

      <TiltBadge tilt={hero.tilt} />

      {/* Tabs */}
      <div className="flex border-b border-gray-800 overflow-x-auto">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex-shrink-0 px-2.5 py-1.5 text-xs font-medium transition-colors whitespace-nowrap ${
              tab === t.id ? 'text-green-400 border-b-2 border-green-500' : 'text-gray-500 hover:text-gray-300'
            }`}>{t.label}</button>
        ))}
      </div>

      {/* Leaks tab */}
      {tab === 'leaks' && (
        <div className="px-3 py-2 space-y-2 max-h-[58vh] overflow-y-auto">
          {leaks.length === 0 && <div className="text-center text-gray-600 text-xs py-6">Nenhum vazamento — jogo equilibrado!</div>}
          {leaks.map((l, i) => <LeakCard key={i} leak={l} index={i} />)}
          {strengths.length > 0 && (
            <div className="mt-3">
              <div className="text-xs font-semibold text-green-700 mb-1.5 uppercase tracking-wider">Pontos fortes</div>
              <ul className="space-y-1">
                {strengths.map((s, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-xs text-gray-400">
                    <span className="text-green-700 flex-shrink-0 mt-0.5">✓</span><span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <button onClick={onChangeNick} className="w-full mt-1 text-xs text-gray-600 hover:text-gray-400 underline text-center">Alterar nick</button>
        </div>
      )}

      {tab === 'stats'      && <div className="px-3 py-2"><StatGrid stats={hero} trends={hero.trends || {}} /></div>}
      {tab === 'position'   && <div className="px-3 py-2"><PositionStats stats={hero} /></div>}
      {tab === 'sizing'     && <div className="px-3 py-2"><BetSizingBar sizing={hero.bet_sizing} /></div>}
      {tab === 'pushfold'   && <div className="px-3 py-2"><PushFoldHelper /></div>}
      {tab === 'comparison' && <div className="px-3 py-2"><TableComparison /></div>}
    </div>
  )
}
