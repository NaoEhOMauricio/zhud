import { useState, useEffect } from 'react'

const API = 'http://127.0.0.1:8765'

const STRENGTH_STYLE = {
  high:    'border-green-800 bg-green-950 text-green-300',
  warning: 'border-orange-800 bg-orange-950 text-orange-300',
  info:    'border-gray-700 bg-gray-900 text-gray-300',
}

export default function EncounterHistory({ nickname }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    setData(null)
    fetch(`${API}/player/${encodeURIComponent(nickname)}/vs-hero`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [nickname])

  if (loading) {
    return <div className="text-center text-gray-600 text-xs py-6">Carregando...</div>
  }

  if (!data || data.error) {
    return <div className="text-center text-gray-600 text-xs py-6">{data?.error || 'Erro ao carregar'}</div>
  }

  const lastSeen = data.last_seen
    ? new Date(data.last_seen).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: '2-digit' })
    : null

  return (
    <div className="space-y-3">
      {/* Encounter counter */}
      <div className="bg-gray-800 rounded-lg px-3 py-2.5 border border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs text-gray-500 mb-0.5">Mãos juntos</div>
            <div className="text-2xl font-bold text-white">
              {data.hands_together}
              <span className="text-sm font-normal text-gray-500 ml-1">mãos</span>
            </div>
          </div>
          {lastSeen && (
            <div className="text-right">
              <div className="text-xs text-gray-500 mb-0.5">Último encontro</div>
              <div className="text-sm font-semibold text-gray-300">{lastSeen}</div>
            </div>
          )}
        </div>
        {data.hands_together === 0 && (
          <p className="text-xs text-gray-600 mt-1">
            Nenhuma mão registrada juntos ainda.
          </p>
        )}
      </div>

      {/* Exploit insights */}
      {data.insights && data.insights.length > 0 && (
        <div>
          <div className="text-xs text-gray-600 uppercase tracking-wider mb-1.5 px-1">
            Como explorar
          </div>
          <div className="space-y-1.5">
            {data.insights.map((insight, i) => (
              <div
                key={i}
                className={`flex items-start gap-2 rounded-lg border px-3 py-2 ${STRENGTH_STYLE[insight.strength] || STRENGTH_STYLE.info}`}
              >
                <span className="text-base flex-shrink-0 leading-none mt-0.5">{insight.icon}</span>
                <span className="text-xs leading-relaxed">{insight.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.insights && data.insights.length === 0 && data.hands_together > 0 && (
        <div className="text-center text-gray-700 text-xs py-3">
          Sem padrões exploráveis identificados ainda.<br />
          Continue jogando para mais dados.
        </div>
      )}
    </div>
  )
}
