export default function TrendBadge({ dir, delta }) {
  if (!dir || dir === 'stable') return null
  const up = dir === 'up'
  return (
    <span
      className={`ml-0.5 text-xs font-bold ${up ? 'text-red-400' : 'text-blue-400'}`}
      title={`${up ? '+' : ''}${delta}% vs últimas mãos`}
    >
      {up ? '↑' : '↓'}
    </span>
  )
}
