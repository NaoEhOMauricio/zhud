import { useState, useEffect, useRef, useCallback } from 'react'
import PlayerCard from './components/PlayerCard'
import HeroPanel from './components/HeroPanel'
import ProfileBadge from './components/ProfileBadge'
import ActiveTablePanel from './components/ActiveTablePanel'
import SessionPanel from './components/SessionPanel'
import TiltAlert from './components/TiltAlert'
import SetupWizard from './components/SetupWizard'

const API    = 'http://127.0.0.1:8765'
const WS_URL = 'ws://127.0.0.1:8765/ws'

export default function App() {
  const [configured, setConfigured]       = useState(null)   // null=loading, true/false
  const [view, setView]                   = useState('table')   // table|players|hero|session
  const [search, setSearch]               = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [recentPlayers, setRecentPlayers] = useState([])
  const [activeTables, setActiveTables]   = useState([])
  const [selectedPlayer, setSelectedPlayer] = useState(null)
  const [heroData, setHeroData]           = useState(null)
  const [heroNick, setHeroNick]           = useState('')
  const [connected, setConnected]         = useState(false)
  const [alwaysOnTop, setAlwaysOnTop]     = useState(false)
  const [showNickModal, setShowNickModal] = useState(false)
  const [nickInput, setNickInput]         = useState('')
  const [tiltAlerts, setTiltAlerts]       = useState([])   // list of tilt alert objects
  const wsRef       = useRef(null)
  const searchTimer = useRef(null)
  // Refs so WebSocket handler can read latest values without reconnecting
  const heroNickRef = useRef(heroNick)
  const viewRef     = useRef(view)
  useEffect(() => { heroNickRef.current = heroNick }, [heroNick])
  useEffect(() => { viewRef.current     = view     }, [view])

  // ── Check setup status on mount ───────────────────────────────────────────
  useEffect(() => {
    fetch(`${API}/setup/status`)
      .then(r => r.json())
      .then(d => {
        setConfigured(d.configured)
        if (d.hero_nickname) setHeroNick(d.hero_nickname)
      })
      .catch(() => setConfigured(false))
  }, [])

  // ── WebSocket — connects ONCE, never reconnects on tab switch ─────────────
  useEffect(() => {
    function connect() {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws
      ws.onopen  = () => setConnected(true)
      ws.onclose = () => { setConnected(false); setTimeout(connect, 3000) }
      ws.onerror = () => ws.close()

      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data)

        if (msg.type === 'snapshot') {
          setRecentPlayers(msg.data || [])
        }

        // Both snapshot and full update set tables the same way
        if (msg.type === 'active_tables_snapshot' || msg.type === 'active_tables_full') {
          setActiveTables(msg.data || [])
        }

        if (msg.type === 'player_update') {
          const upd = msg.data
          setRecentPlayers(prev => {
            const idx = prev.findIndex(p => p.nickname === upd.nickname)
            if (idx >= 0) { const n = [...prev]; n[idx] = upd; return n }
            return [upd, ...prev].slice(0, 30)
          })
          setSelectedPlayer(prev => prev?.nickname === upd.nickname ? { ...prev, ...upd } : prev)
          // Use refs to avoid stale closures without reconnecting
          if (upd.nickname === heroNickRef.current && viewRef.current === 'hero') loadHero()
        }

        if (msg.type === 'cluster_update') {
          const { nickname, cluster_id, cluster_label } = msg.data
          setRecentPlayers(prev => prev.map(p => p.nickname === nickname ? { ...p, cluster_id, cluster_label } : p))
          setSelectedPlayer(prev => prev?.nickname === nickname ? { ...prev, cluster_id, cluster_label } : prev)
        }

        if (msg.type === 'tilt_alert') {
          const a = msg.data
          setTiltAlerts(prev => {
            const existing = prev.findIndex(x => x.nickname === a.nickname)
            if (existing >= 0) { const n = [...prev]; n[existing] = a; return n }
            return [a, ...prev]
          })
        }
      }
    }
    connect()
    return () => wsRef.current?.close()
  }, [])   // ← empty deps: connect once, never reconnect on tab switch

  // ── Hero ──────────────────────────────────────────────────────────────────
  const loadHero = useCallback(async () => {
    try { const r = await fetch(`${API}/hero`); setHeroData(await r.json()) } catch {}
  }, [])

  const switchToHero = () => { setView('hero'); setSelectedPlayer(null); setSearch(''); loadHero() }

  // ── Save nick ─────────────────────────────────────────────────────────────
  const saveNick = async () => {
    if (!nickInput.trim()) return
    try {
      await fetch(`${API}/hero/nickname`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nickname: nickInput.trim() }),
      })
      setHeroNick(nickInput.trim())
      setShowNickModal(false)
      if (view === 'hero') loadHero()
    } catch {}
  }

  // ── Search ────────────────────────────────────────────────────────────────
  const handleSearch = useCallback((e) => {
    const q = e.target.value
    setSearch(q)
    clearTimeout(searchTimer.current)
    if (q.length < 2) { setSearchResults([]); return }
    searchTimer.current = setTimeout(async () => {
      try { const r = await fetch(`${API}/search?q=${encodeURIComponent(q)}`); setSearchResults(await r.json()) } catch {}
    }, 300)
  }, [])

  const loadPlayer = async (nickname) => {
    try { const r = await fetch(`${API}/player/${encodeURIComponent(nickname)}`); setSelectedPlayer(await r.json()) } catch {}
  }

  const toggleAlwaysOnTop = () => { const n = !alwaysOnTop; setAlwaysOnTop(n); window.zhud?.setAlwaysOnTop(n) }
  const dismissTilt = (nick) => setTiltAlerts(prev => prev.filter(a => a.nickname !== nick))

  // ── Active table refresh ───────────────────────────────────────────────────
  const fetchActiveTables = useCallback(async () => {
    try {
      const r = await fetch(`${API}/active-tables`)
      const data = await r.json()
      if (Array.isArray(data)) setActiveTables(data)
    } catch {}
  }, [])

  // Refresh when switching to Mesa tab + poll every 10s while on it
  useEffect(() => {
    if (view !== 'table') return
    fetchActiveTables()
    const t = setInterval(fetchActiveTables, 10000)
    return () => clearInterval(t)
  }, [view, fetchActiveTables])

  const TABS = [
    { id: 'table',   label: '🃏 Mesa' },
    { id: 'players', label: '👥 Jogadores' },
    { id: 'hero',    label: '👤 Eu' },
    { id: 'session', label: '📊 Sessão' },
  ]

  const displayList = search.length >= 2 ? searchResults : recentPlayers

  // Show loading or setup wizard before main UI
  if (configured === null) {
    return <div className="h-screen bg-gray-950 flex items-center justify-center text-gray-600 text-sm">Iniciando...</div>
  }

  if (!configured) {
    return <SetupWizard onDone={(nick) => { setHeroNick(nick); setConfigured(true) }} />
  }

  return (
    <div className="h-screen bg-gray-950 text-white flex flex-col select-none overflow-hidden">

      {/* Title bar */}
      <div className="drag-region flex items-center justify-between px-3 py-2 bg-gray-900 border-b border-gray-800 flex-shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-green-400 font-bold text-sm tracking-wider">Z<span className="text-white">Hud</span></span>
          <span className="text-gray-700 text-xs">v1.0.5</span>
          <span className={`w-2 h-2 rounded-full flex-shrink-0 pulse-live ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
        </div>
        <div className="flex items-center gap-1">
          <button onClick={toggleAlwaysOnTop}
            className={`text-xs px-2 py-0.5 rounded border transition-colors ${alwaysOnTop ? 'border-green-600 text-green-400' : 'border-gray-700 text-gray-500 hover:text-gray-300'}`}
            title="Sempre no topo">⬆</button>
          <button onClick={() => window.zhud?.minimize()} className="text-gray-500 hover:text-gray-200 text-xs px-2 py-0.5">—</button>
          <button onClick={() => window.zhud?.close()}    className="text-gray-500 hover:text-red-400 text-xs px-2 py-0.5">✕</button>
        </div>
      </div>

      {/* Tilt alerts */}
      {tiltAlerts.length > 0 && <TiltAlert alerts={tiltAlerts} onDismiss={dismissTilt} />}

      {/* Tab nav */}
      <div className="flex border-b border-gray-800 bg-gray-900 flex-shrink-0">
        {TABS.map(t => (
          <button key={t.id} onClick={() => { setView(t.id); if (t.id === 'hero') loadHero() }}
            className={`flex-1 py-1.5 text-xs font-medium transition-colors ${
              view === t.id ? 'text-green-400 border-b-2 border-green-500' : 'text-gray-500 hover:text-gray-300'
            }`}>{t.label}</button>
        ))}
      </div>

      {/* ══ MESA ATIVA ═══════════════════════════════════════════════════════ */}
      {view === 'table' && (
        <ActiveTablePanel
          tables={activeTables}
          heroNick={heroNick}
          onSelectPlayer={(nick) => { loadPlayer(nick); setView('players') }}
        />
      )}

      {/* ══ JOGADORES ════════════════════════════════════════════════════════ */}
      {view === 'players' && (
        <>
          <div className="px-3 py-2 bg-gray-900 border-b border-gray-800 flex-shrink-0">
            <input type="text" value={search} onChange={handleSearch}
              placeholder="Buscar jogador..."
              className="w-full bg-gray-800 text-white text-sm px-3 py-1.5 rounded border border-gray-700 focus:outline-none focus:border-green-500 placeholder-gray-600" />
          </div>

          {selectedPlayer && (
            <div className="flex-shrink-0 overflow-y-auto max-h-[60vh]">
              <PlayerCard player={selectedPlayer} onClose={() => setSelectedPlayer(null)} />
            </div>
          )}

          {!selectedPlayer && (
            <div className="flex-1 overflow-y-auto">
              <div className="px-2 py-1">
                <div className="text-xs text-gray-600 px-2 py-1 uppercase tracking-wider">
                  {search.length >= 2 ? 'Resultados' : 'Jogadores recentes'}
                </div>
                {displayList.map(p => (
                  <button key={p.nickname} onClick={() => loadPlayer(p.nickname)}
                    className="w-full text-left px-3 py-2 rounded hover:bg-gray-800 transition-colors">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white truncate flex-1" title={p.nickname}>
                        {p.nickname}{p.nickname === heroNick && <span className="ml-1 text-xs text-green-600">👤</span>}
                      </span>
                      <ProfileBadge profile={p.profile} small />
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      VPIP <span className="text-gray-400">{p.vpip}%</span>
                      &nbsp;·&nbsp;PFR <span className="text-gray-400">{p.pfr}%</span>
                      &nbsp;·&nbsp;AF <span className="text-gray-400">{p.af}</span>
                      &nbsp;·&nbsp;<span className="text-gray-600">{p.hands}m</span>
                    </div>
                  </button>
                ))}
                {displayList.length === 0 && (
                  <div className="text-center text-gray-700 text-sm py-10">
                    {connected ? (search.length >= 2 ? 'Nenhum resultado' : 'Aguardando mãos...') : 'Conectando...'}
                  </div>
                )}
              </div>
            </div>
          )}

          {selectedPlayer && (
            <div className="flex-1 overflow-y-auto border-t border-gray-800">
              <div className="px-2 py-1">
                <div className="text-xs text-gray-600 px-2 py-1 uppercase tracking-wider">Outros</div>
                {recentPlayers.filter(p => p.nickname !== selectedPlayer.nickname).slice(0, 8).map(p => (
                  <button key={p.nickname} onClick={() => loadPlayer(p.nickname)}
                    className="w-full text-left px-3 py-1.5 rounded hover:bg-gray-800 transition-colors">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs text-gray-300 truncate flex-1">{p.nickname}</span>
                      <ProfileBadge profile={p.profile} small />
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* ══ MEU PERFIL ═══════════════════════════════════════════════════════ */}
      {view === 'hero' && (
        <div className="flex-1 overflow-y-auto">
          <HeroPanel hero={heroData} onClose={() => setView('table')}
            onChangeNick={() => { setNickInput(heroNick); setShowNickModal(true) }} />
          {!heroData && (
            <div className="text-center text-gray-700 text-sm py-10">
              {connected ? 'Carregando...' : 'Conectando...'}
            </div>
          )}
        </div>
      )}

      {/* ══ SESSÃO ═══════════════════════════════════════════════════════════ */}
      {view === 'session' && <SessionPanel />}

      {/* ── Nick modal ────────────────────────────────────────────────────── */}
      {showNickModal && (
        <div className="absolute inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 mx-4 w-full max-w-xs">
            <div className="text-sm font-semibold text-white mb-1">Seu nick no PokerStars</div>
            <div className="text-xs text-gray-500 mb-3">Exatamente como aparece nas mãos.</div>
            <input autoFocus type="text" value={nickInput} onChange={e => setNickInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && saveNick()}
              placeholder="NaoEOMauricio"
              className="w-full bg-gray-800 text-white text-sm px-3 py-2 rounded border border-gray-700 focus:outline-none focus:border-green-500 mb-3" />
            <div className="flex gap-2">
              <button onClick={saveNick} className="flex-1 bg-green-700 hover:bg-green-600 text-white text-sm py-1.5 rounded transition-colors">Salvar</button>
              <button onClick={() => setShowNickModal(false)} className="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm py-1.5 rounded transition-colors">Cancelar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
