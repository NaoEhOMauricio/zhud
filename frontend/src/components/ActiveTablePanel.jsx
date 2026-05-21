import ProfileBadge from './ProfileBadge'
import RangeTips from './RangeTips'

// Tilt badge shown inline next to player name on the Mesa tab
function TiltChip({ tilt }) {
  if (!tilt || tilt.score < 60) return null
  const style = tilt.score >= 80
    ? 'bg-red-900 text-red-300 border-red-700'
    : 'bg-orange-900 text-orange-300 border-orange-700'
  return (
    <span className={`text-xs px-1.5 py-0.5 rounded border font-semibold ${style} flex-shrink-0 pulse-live`}>
      TILT {tilt.label}
    </span>
  )
}

// Style tag shown inline (Maniac, Passivo, etc.) with compact appearance
function StyleChip({ profile, hands }) {
  if (!profile || hands < 5) return (
    <span className="text-xs text-gray-700 flex-shrink-0">sem dados</span>
  )
  const colors = {
    'Nit':             'text-blue-400',
    'TAG':             'text-green-400',
    'Regular':         'text-green-300',
    'LAG':             'text-orange-400',
    'Calling Station': 'text-purple-400',
    'Maniac':          'text-red-400',
    'Passivo':         'text-blue-300',
  }
  return (
    <span className={`text-xs font-semibold flex-shrink-0 ${colors[profile] || 'text-gray-400'}`}>
      {profile}
    </span>
  )
}

import { useState } from 'react'

function isHU(table) {
  return (table.players_data || []).filter(p => !p.is_hero || true).length <= 2
}

export default function ActiveTablePanel({ tables, heroNick, onSelectPlayer, heroHandCount }) {
  if (!tables || tables.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-2 text-center px-4">
        <div className="text-3xl">🃏</div>
        <div className="text-sm text-gray-500">Nenhuma mesa ativa</div>
        <div className="text-xs text-gray-700 leading-relaxed">
          Inicie uma partida no PokerStars.<br />
          Os dados aparecem após a primeira mão completada.
        </div>
      </div>
    )
  }

  // Backend already sets is_current based on most recently modified HH file
  // Sort: current table first, then by last_hand desc
  const sorted = [...tables].sort((a, b) => {
    if (a.is_current && !b.is_current) return -1
    if (!a.is_current && b.is_current) return 1
    return new Date(b.last_hand || 0) - new Date(a.last_hand || 0)
  })

  const currentTable = sorted.find(t => t.is_current)
  const [showRange, setShowRange] = useState(false)

  return (
    <div className="flex-1 overflow-y-auto">

      {/* Range tips toggle — only shown when there's a current table */}
      {currentTable && (
        <div className="mx-2 mt-2 mb-1">
          <button
            onClick={() => setShowRange(s => !s)}
            className={`w-full py-1.5 rounded text-xs font-semibold transition-colors flex items-center justify-center gap-1.5 ${
              showRange
                ? 'bg-blue-900 text-blue-300 border border-blue-700'
                : 'bg-gray-900 text-gray-500 border border-gray-800 hover:text-gray-300'
            }`}
          >
            <span>🎯</span>
            {showRange ? 'Ocultar dicas de range' : 'Dicas de range pré-flop'}
          </button>
          {showRange && (
            <div className="bg-gray-950 border border-gray-800 rounded-b-lg -mt-px max-h-96 overflow-y-auto">
              <RangeTips heroHandCount={heroHandCount} />
            </div>
          )}
        </div>
      )}

      {sorted.map((table, tableIdx) => {
        const isCurrent = !!table.is_current
        const players = table.players_data || []

        return (
          <div
            key={table.table}
            className={`mb-2 rounded-lg overflow-hidden ${
              isCurrent
                ? 'border-2 border-green-600 mx-2 mt-2'
                : 'border border-gray-800 mx-2'
            }`}
          >
            {/* Table header */}
            <div className={`flex items-center justify-between px-3 py-1.5 ${
              isCurrent ? 'bg-green-950' : 'bg-gray-900'
            }`}>
              <div className="flex items-center gap-2 min-w-0">
                {isCurrent && (
                  <span className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0 pulse-live" />
                )}
                <span className={`text-xs font-semibold truncate ${
                  isCurrent ? 'text-green-300' : 'text-gray-400'
                }`}>
                  {isCurrent ? '● MESA ATUAL' : 'Mesa'} · {table.table}
                </span>
              </div>
              <span className="text-xs text-gray-600 flex-shrink-0 ml-2">
                {table.game_type === 'tournament' ? 'Torneio' : 'Cash'}
              </span>
            </div>

            {/* Players */}
            <div className="divide-y divide-gray-800/40">
              {players.map(p => (
                <button
                  key={p.nickname}
                  onClick={() => !p.is_hero && onSelectPlayer(p.nickname)}
                  className={`w-full text-left px-3 py-2 transition-colors ${
                    p.is_hero
                      ? 'bg-green-950/20 cursor-default'
                      : 'hover:bg-gray-800/60'
                  }`}
                >
                  {/* Row 1: name + tilt/profile */}
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5 min-w-0">
                      {p.is_hero && (
                        <span className="text-green-500 text-xs flex-shrink-0">👤</span>
                      )}
                      <span
                        className={`text-sm font-semibold truncate ${
                          p.is_hero ? 'text-green-400' : 'text-white'
                        }`}
                        title={p.nickname}
                      >
                        {p.nickname}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      {/* Tilt badge — only for multi-way tables (HU has naturally high VPIP) */}
                      {!isHU(table) && <TiltChip tilt={p.tilt} />}
                      {/* Profile style (always shown, unless tilt badge is present) */}
                      {(isHU(table) || !p.tilt || p.tilt.score < 60) && (
                        <StyleChip profile={p.profile} hands={p.hands || 0} />
                      )}
                    </div>
                  </div>

                  {/* Row 2: key stats */}
                  {!p.is_hero && (p.hands || 0) >= 5 && (
                    <div className="text-xs text-gray-500 mt-0.5 flex gap-2">
                      <span>VPIP <span className="text-gray-400">{p.vpip}%</span></span>
                      <span>PFR <span className="text-gray-400">{p.pfr}%</span></span>
                      <span>AF <span className="text-gray-400">{p.af}</span></span>
                      <span>3BET <span className="text-gray-400">{p.threebet}%</span></span>
                    </div>
                  )}
                  {!p.is_hero && (p.hands || 0) < 5 && (
                    <div className="text-xs text-gray-700 mt-0.5">Sem dados — nova amostra</div>
                  )}
                </button>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
