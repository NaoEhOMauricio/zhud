import { useState, useEffect, useCallback } from 'react'

const API = 'http://127.0.0.1:8765'

const PRIORITY_STYLE = {
  1: 'border-red-800 bg-red-950',
  2: 'border-orange-800 bg-orange-950',
  3: 'border-gray-700 bg-gray-900',
}

const STARS = (n) => '★'.repeat(n) + '☆'.repeat(5 - n)
const QUALITY_COLOR = {
  1: 'text-red-400', 2: 'text-orange-400', 3: 'text-yellow-400',
  4: 'text-green-400', 5: 'text-green-300',
}

function AlertCard({ alert, defaultOpen }) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div className={`rounded-lg border overflow-hidden ${PRIORITY_STYLE[alert.priority] || PRIORITY_STYLE[3]}`}>
      <button onClick={() => setOpen(o => !o)}
        className="w-full text-left px-3 py-2.5 flex items-start gap-2">
        <span className="text-lg flex-shrink-0 leading-none mt-0.5">{alert.icon}</span>
        <div className="flex-1 min-w-0">
          <div className="text-xs font-bold text-white leading-tight">{alert.title}</div>
          {/* Position badges */}
          {(alert.hero_pos || alert.villain_pos) && (
            <div className="flex items-center gap-1.5 mt-1 flex-wrap">
              {alert.hero_pos && (
                <span className="text-xs bg-green-900 text-green-300 px-1.5 py-0.5 rounded font-semibold">
                  Você: {alert.hero_pos}
                </span>
              )}
              {alert.villain_pos && alert.villain && (
                <span className="text-xs bg-gray-800 text-gray-300 px-1.5 py-0.5 rounded">
                  vs {alert.villain} ({alert.villain_pos})
                </span>
              )}
            </div>
          )}
          <div className="text-xs text-gray-200 mt-1.5 leading-relaxed font-medium">
            {alert.action}
          </div>
        </div>
        <span className="text-gray-600 text-xs flex-shrink-0 mt-1">{open ? '▲' : '▼'}</span>
      </button>
      {open && alert.detail && (
        <div className="px-3 pb-2.5 border-t border-current/10 pt-2">
          <p className="text-xs text-gray-400 leading-relaxed">{alert.detail}</p>
        </div>
      )}
    </div>
  )
}

export default function LiveAlerts() {
  const [data, setData]    = useState(null)
  const [loading, setLoad] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(null)

  const load = useCallback(async () => {
    setLoad(true)
    try {
      const r = await fetch(`${API}/live-alerts`)
      const d = await r.json()
      setData(d)
      setLastUpdate(new Date())
    } catch {}
    setLoad(false)
  }, [])

  // Auto-refresh every 15s
  useEffect(() => {
    load()
    const t = setInterval(load, 15000)
    return () => clearInterval(t)
  }, [load])

  return (
    <div className="space-y-2.5 px-3 py-2">

      {/* Header: position + stack auto-detected */}
      {data && (data.hero_pos || data.hero_stack) && (
        <div className="bg-gray-900 rounded-lg px-3 py-2 border border-gray-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Posição detectada:</span>
              <span className="text-sm font-bold text-green-400">{data.hero_pos}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Stack:</span>
              <span className={`text-sm font-bold ${
                data.hero_stack <= 12 ? 'text-red-400' :
                data.hero_stack <= 20 ? 'text-orange-400' : 'text-white'
              }`}>{data.hero_stack}BB</span>
            </div>
          </div>
          {data.table && (
            <div className="text-xs text-gray-700 mt-0.5">
              T{data.table} · {data.n_players} jogadores
              {data.bb_amount > 0 && ` · Blind ${data.bb_amount}`}
            </div>
          )}
        </div>
      )}

      {/* Table quality */}
      {data?.quality && (
        <div className="bg-gray-900 rounded-lg px-3 py-2 border border-gray-800">
          <div className="flex items-center justify-between">
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
          {data.quality.reason && (
            <p className="text-xs text-gray-600 mt-1 leading-snug">{data.quality.reason}</p>
          )}
        </div>
      )}

      {loading && !data && (
        <div className="text-center text-gray-600 text-xs py-6">Analisando mesa...</div>
      )}

      {/* Alerts */}
      {data && (data.alerts || []).length === 0 && (
        <div className="text-center text-gray-700 text-xs py-4 leading-relaxed">
          Nenhuma oportunidade específica detectada.<br />
          Jogue estilo GTO desta posição.
        </div>
      )}

      {(data?.alerts || []).map((alert, i) => (
        <AlertCard key={i} alert={alert} defaultOpen={i === 0} />
      ))}

      {/* Footer */}
      <div className="flex items-center justify-between pt-1">
        <span className="text-xs text-gray-700">
          {lastUpdate ? `Atualizado ${lastUpdate.toLocaleTimeString('pt-BR', {hour:'2-digit', minute:'2-digit', second:'2-digit'})}` : ''}
        </span>
        <button onClick={load}
          className="text-xs text-gray-600 hover:text-gray-400 underline">
          {loading ? 'Atualizando...' : 'Atualizar agora'}
        </button>
      </div>
    </div>
  )
}
