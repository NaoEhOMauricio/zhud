export default function BehaviorList({ observations = [], vulnerabilities = [] }) {
  if (!observations.length && !vulnerabilities.length) return null

  return (
    <div className="space-y-2 mt-1">
      {observations.length > 0 && (
        <div>
          <div className="text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wider">
            Observações
          </div>
          <ul className="space-y-1">
            {observations.map((obs, i) => (
              <li key={i} className="flex items-start gap-1.5 text-xs text-gray-300 leading-tight">
                <span className="text-gray-600 mt-0.5 flex-shrink-0">•</span>
                <span>{obs}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {vulnerabilities.length > 0 && (
        <div>
          <div className="text-xs font-semibold text-yellow-600 mb-1 uppercase tracking-wider">
            Explorar
          </div>
          <ul className="space-y-1">
            {vulnerabilities.map((v, i) => (
              <li key={i} className="flex items-start gap-1.5 text-xs text-yellow-400 leading-tight">
                <span className="flex-shrink-0 mt-0.5">▶</span>
                <span>{v}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
