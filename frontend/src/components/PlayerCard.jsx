import { useState } from 'react'
import ProfileBadge from './ProfileBadge'
import StatGrid from './StatGrid'
import BehaviorList from './BehaviorList'
import TiltBadge from './TiltBadge'
import BetSizingBar from './BetSizingBar'
import PositionStats from './PositionStats'
import NotesEditor from './NotesEditor'
import HandHighlight from './HandHighlight'
import EncounterHistory from './EncounterHistory'

const CLUSTER_COLORS = [
  'text-blue-300','text-cyan-300','text-green-300',
  'text-yellow-300','text-orange-300','text-red-300',
]

export default function PlayerCard({ player, onClose }) {
  const [tab, setTab] = useState('stats')
  const p = player

  const aggrColor = {
    'Muito Passivo':'text-blue-400','Passivo':'text-blue-300',
    'Moderado':'text-green-400','Agressivo':'text-orange-400','Muito Agressivo':'text-red-400',
  }[p.aggression_label] || 'text-gray-400'

  const clusterColor = p.cluster_id >= 0 ? CLUSTER_COLORS[p.cluster_id] || 'text-gray-400' : 'text-gray-600'

  const tabs = [
    { id: 'stats',    label: 'Stats' },
    { id: 'history',  label: 'Vs Você' },
    { id: 'position', label: 'Posição' },
    { id: 'sizing',   label: 'Sizing' },
    { id: 'notes',    label: 'Notas' },
    { id: 'hands',    label: 'Mãos' },
  ]

  return (
    <div className="m-2 bg-gray-900 rounded-lg border border-gray-700 overflow-hidden">

      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-bold text-white text-sm truncate max-w-[110px]" title={p.nickname}>{p.nickname}</span>
          <ProfileBadge profile={p.profile} />
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="text-xs text-gray-500">{p.hands}m</span>
          {onClose && <button onClick={onClose} className="text-gray-500 hover:text-gray-200 text-sm ml-1">✕</button>}
        </div>
      </div>

      {/* Sub-header */}
      <div className="px-3 pt-1.5 pb-1 flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-1">
          <span className="text-xs text-gray-600">Agressividade:</span>
          <span className={`text-xs font-semibold ${aggrColor}`}>{p.aggression_label || '—'}</span>
        </div>
        {p.cluster_label && (
          <div className="flex items-center gap-1">
            <span className="text-xs text-gray-600">Cluster:</span>
            <span className={`text-xs font-semibold ${clusterColor}`}>{p.cluster_label}</span>
          </div>
        )}
      </div>

      <TiltBadge tilt={p.tilt} />

      {/* Tab bar */}
      <div className="flex border-b border-gray-800 overflow-x-auto">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex-shrink-0 px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap ${
              tab === t.id ? 'text-green-400 border-b-2 border-green-500' : 'text-gray-500 hover:text-gray-300'
            }`}>{t.label}</button>
        ))}
      </div>

      {tab === 'history'  && <div className="px-3 py-2"><EncounterHistory nickname={p.nickname} /></div>}
      {tab === 'stats' && (
        <div className="px-3 py-2">
          <StatGrid stats={p} trends={p.trends || {}} />
          <div className="mt-2">
            <BehaviorList observations={p.observations || []} vulnerabilities={p.vulnerabilities || []} />
          </div>
        </div>
      )}
      {tab === 'position' && <div className="px-3 py-2"><PositionStats stats={p} /></div>}
      {tab === 'sizing'   && <div className="px-3 py-2"><BetSizingBar sizing={p.bet_sizing} /></div>}
      {tab === 'notes'    && <div className="px-3 py-2"><NotesEditor nickname={p.nickname} /></div>}
      {tab === 'hands'    && <div className="px-3 py-2"><HandHighlight nickname={p.nickname} /></div>}
    </div>
  )
}
