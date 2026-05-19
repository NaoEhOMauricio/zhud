const BARS = [
  { key: 'overbet',  label: 'Overbet',  color: 'bg-red-500',    desc: '>100% pot' },
  { key: 'potbet',   label: 'Pot bet',  color: 'bg-orange-500', desc: '67-100%'   },
  { key: 'halfpot',  label: 'Half pot', color: 'bg-green-500',  desc: '25-66%'    },
  { key: 'underbet', label: 'Underbet', color: 'bg-blue-500',   desc: '<25%'      },
]

export default function BetSizingBar({ sizing }) {
  if (!sizing || (sizing.total || 0) < 5) return null

  return (
    <div className="mt-1">
      <div className="text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wider">
        Bet Sizing <span className="text-gray-700 normal-case font-normal">({sizing.total} apostas)</span>
      </div>
      <div className="space-y-1">
        {BARS.map(({ key, label, color, desc }) => {
          const pct = sizing[key] || 0
          return (
            <div key={key} className="flex items-center gap-2">
              <span className="text-xs text-gray-500 w-14 flex-shrink-0">{label}</span>
              <div className="flex-1 bg-gray-800 rounded-full h-1.5">
                <div
                  className={`${color} h-1.5 rounded-full transition-all duration-500`}
                  style={{ width: `${Math.min(pct, 100)}%` }}
                />
              </div>
              <span className="text-xs text-gray-400 w-8 text-right flex-shrink-0">{pct}%</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
