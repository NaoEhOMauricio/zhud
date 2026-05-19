const PROFILES = {
  'Nit':             { bg: 'bg-blue-950',   text: 'text-blue-300',   icon: '🧊' },
  'TAG':             { bg: 'bg-emerald-950', text: 'text-emerald-300', icon: '⚡' },
  'LAG':             { bg: 'bg-orange-950',  text: 'text-orange-300',  icon: '🔥' },
  'Calling Station': { bg: 'bg-purple-950',  text: 'text-purple-300',  icon: '📞' },
  'Maniac':          { bg: 'bg-red-950',     text: 'text-red-300',     icon: '💣' },
  'Passivo':         { bg: 'bg-gray-800',    text: 'text-gray-300',    icon: '🐢' },
  'Regular':       { bg: 'bg-cyan-950',    text: 'text-cyan-300',    icon: '⚖️' },
  'Amostra pequena': { bg: 'bg-gray-800',    text: 'text-gray-400',    icon: '📊' },
}

const DEFAULT = { bg: 'bg-gray-800', text: 'text-gray-400', icon: '?' }

export default function ProfileBadge({ profile, small = false }) {
  const p = PROFILES[profile] || DEFAULT
  const size = small ? 'text-xs px-1.5 py-0.5' : 'text-xs px-2 py-1'
  return (
    <span className={`${p.bg} ${p.text} ${size} rounded font-semibold whitespace-nowrap`}>
      {p.icon} {profile || 'Unknown'}
    </span>
  )
}
