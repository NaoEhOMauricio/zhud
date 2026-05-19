import { useState, useEffect } from 'react'

const API = 'http://127.0.0.1:8765'

export default function NotesEditor({ nickname }) {
  const [notes, setNotes] = useState([])
  const [text, setText]   = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!nickname) return
    fetch(`${API}/player/${encodeURIComponent(nickname)}/notes`)
      .then(r => r.json())
      .then(setNotes)
      .catch(() => {})
  }, [nickname])

  const save = async () => {
    if (!text.trim()) return
    setSaving(true)
    try {
      const r = await fetch(`${API}/player/${encodeURIComponent(nickname)}/notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ note: text.trim() }),
      })
      const data = await r.json()
      if (!data.error) {
        setNotes(prev => [data, ...prev])
        setText('')
      }
    } catch {}
    setSaving(false)
  }

  const del = async (id) => {
    try {
      await fetch(`${API}/notes/${id}`, { method: 'DELETE' })
      setNotes(prev => prev.filter(n => n.id !== id))
    } catch {}
  }

  return (
    <div className="space-y-2">
      {/* Input */}
      <div className="flex gap-1">
        <input
          type="text"
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && save()}
          placeholder="Adicionar anotação..."
          className="flex-1 bg-gray-800 text-white text-xs px-2 py-1.5 rounded border border-gray-700 focus:outline-none focus:border-green-500 placeholder-gray-600"
        />
        <button
          onClick={save}
          disabled={saving || !text.trim()}
          className="bg-green-800 hover:bg-green-700 disabled:opacity-40 text-white text-xs px-3 py-1.5 rounded transition-colors"
        >
          {saving ? '...' : '+'}
        </button>
      </div>

      {/* List */}
      {notes.length === 0 ? (
        <div className="text-center text-gray-700 text-xs py-4">Nenhuma anotação</div>
      ) : (
        <ul className="space-y-1 max-h-48 overflow-y-auto">
          {notes.map(n => (
            <li key={n.id} className="flex items-start gap-2 bg-gray-800 rounded px-2 py-1.5 group">
              <span className="text-xs text-gray-300 flex-1 leading-snug">{n.note}</span>
              <button
                onClick={() => del(n.id)}
                className="text-gray-600 hover:text-red-400 text-xs opacity-0 group-hover:opacity-100 flex-shrink-0 transition-opacity"
              >✕</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
