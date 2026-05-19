import { useState, useEffect } from 'react'

const API = 'http://127.0.0.1:8765'

export default function SetupWizard({ onDone }) {
  const [found, setFound]   = useState(null)  // null=loading, []=not found, [...]= found
  const [selected, setSelected] = useState(null)
  const [nickInput, setNickInput] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError]   = useState('')

  useEffect(() => {
    fetch(`${API}/setup/status`)
      .then(r => r.json())
      .then(d => {
        const dirs = d.found_dirs || []
        setFound(dirs)
        if (dirs.length > 0) setSelected(dirs[0])
      })
      .catch(() => setFound([]))   // backend not ready = show manual input
  }, [])

  const retry = () => {
    setFound(null)
    setError('')
    fetch(`${API}/setup/status`)
      .then(r => r.json())
      .then(d => {
        const dirs = d.found_dirs || []
        setFound(dirs)
        if (dirs.length > 0) setSelected(dirs[0])
      })
      .catch(() => setFound([]))
  }

  const confirm = async () => {
    const nick = selected ? selected.nick : nickInput.trim()
    const path = selected ? selected.path : ''

    if (!nick) { setError('Informe seu nick do PokerStars'); return }

    setSaving(true)
    setError('')
    try {
      const r = await fetch(`${API}/setup/configure`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nick, path }),
      })
      const d = await r.json()
      if (d.error) { setError(d.error); setSaving(false) }
      else onDone(nick)
    } catch {
      setError('Não foi possível conectar ao backend. Verifique se start.bat está rodando.')
      setSaving(false)
    }
  }

  // ── Loading ────────────────────────────────────────────────────────────────
  if (found === null) {
    return (
      <div className="h-screen bg-gray-950 flex flex-col items-center justify-center gap-3">
        <div className="text-2xl font-black text-green-400">Z<span className="text-white">Hud</span></div>
        <div className="text-sm text-gray-500 animate-pulse">Detectando PokerStars...</div>
      </div>
    )
  }

  return (
    <div className="h-screen bg-gray-950 flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-xs space-y-6">

        {/* Logo */}
        <div className="text-center">
          <div className="text-3xl font-black text-green-400">Z<span className="text-white">Hud</span></div>
          <div className="text-xs text-gray-500 mt-1">
            {found.length > 0 ? 'Selecione seu perfil' : 'Configure seu perfil'}
          </div>
        </div>

        {/* ── CASE 1: Accounts found → just pick one ── */}
        {found.length > 0 && (
          <div className="space-y-2">
            {found.map(dir => (
              <button
                key={dir.path}
                onClick={() => { setSelected(dir); setError('') }}
                className={`w-full text-left px-4 py-3 rounded-lg border-2 transition-all ${
                  selected?.path === dir.path
                    ? 'border-green-500 bg-green-950 text-white'
                    : 'border-gray-700 bg-gray-900 text-gray-300 hover:border-gray-500'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-sm">{dir.nick}</span>
                  {selected?.path === dir.path && (
                    <span className="text-green-400 text-lg">✓</span>
                  )}
                </div>
                <div className="text-xs text-gray-500 mt-0.5">
                  {dir.file_count} partidas salvas
                </div>
              </button>
            ))}

            {/* Show manual nick input only when > 1 account found */}
            {found.length > 1 && (
              <button
                onClick={() => setSelected(null)}
                className="text-xs text-gray-600 hover:text-gray-400 underline w-full text-center pt-1"
              >
                Nick não está na lista?
              </button>
            )}
          </div>
        )}

        {/* ── CASE 2: Nothing found OR user wants manual entry ── */}
        {(found.length === 0 || selected === null) && (
          <div className="space-y-3">
            {found.length === 0 && (
              <div className="bg-yellow-950 border border-yellow-800 rounded-lg px-3 py-2.5 text-xs text-yellow-300 leading-relaxed">
                <div className="font-semibold mb-1">PokerStars não detectado</div>
                <div>Abra o PokerStars, jogue uma mão e clique em
                  <button onClick={retry} className="text-yellow-400 underline ml-1">Tentar novamente</button>
                </div>
              </div>
            )}

            <div>
              <div className="text-xs text-gray-400 mb-1.5">Seu nick no PokerStars</div>
              <input
                autoFocus
                type="text"
                value={nickInput}
                onChange={e => { setNickInput(e.target.value); setError('') }}
                onKeyDown={e => e.key === 'Enter' && confirm()}
                placeholder="ex: NaoEoMauricio"
                className="w-full bg-gray-800 text-white px-4 py-3 rounded-lg border border-gray-700 focus:outline-none focus:border-green-500 text-sm placeholder-gray-600"
              />
              <div className="text-xs text-gray-600 mt-1.5 leading-relaxed">
                Digite exatamente como aparece no PokerStars. O app vai localizar suas partidas automaticamente.
              </div>
            </div>

            {found.length > 0 && (
              <button
                onClick={() => setSelected(found[0])}
                className="text-xs text-gray-600 hover:text-gray-400 underline w-full text-center"
              >
                ← Voltar para seleção automática
              </button>
            )}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-950 border border-red-800 rounded-lg px-3 py-2.5 text-xs text-red-300 leading-relaxed">
            {error}
          </div>
        )}

        {/* Confirm button */}
        <button
          onClick={confirm}
          disabled={saving || (found.length > 0 && !selected && !nickInput.trim()) || (!selected && !nickInput.trim())}
          className="w-full bg-green-600 hover:bg-green-500 disabled:opacity-40 text-white font-bold text-sm py-3 rounded-lg transition-colors"
        >
          {saving ? 'Iniciando...' : 'Iniciar ZHud →'}
        </button>

      </div>
    </div>
  )
}
