import TrendBadge from './TrendBadge'

const STATS = [
  { key: 'vpip',         label: 'VPIP',   suffix: '%' },
  { key: 'pfr',          label: 'PFR',    suffix: '%' },
  { key: 'threebet',     label: '3BET',   suffix: '%' },
  { key: 'fourbet',      label: '4BET',   suffix: '%' },
  { key: 'af',           label: 'AF',     suffix: '' },
  { key: 'cbet',         label: 'CBET',   suffix: '%' },
  { key: 'fold_to_cbet', label: 'F.CBET', suffix: '%' },
  { key: 'fold_to_3bet', label: 'F.3BET', suffix: '%' },
  { key: 'squeeze',      label: 'SQ',     suffix: '%' },
  { key: 'cold_call',    label: 'COLD',   suffix: '%' },
  { key: 'donk_bet',     label: 'DONK',   suffix: '%' },
  { key: 'wtsd',         label: 'WTSD',   suffix: '%' },
]

const RANGES = {
  vpip:         [[0,15,'blue'],[15,30,'green'],[30,100,'red']],
  pfr:          [[0,12,'blue'],[12,25,'green'],[25,100,'red']],
  threebet:     [[0,4,'blue'],[4,9,'green'],[9,100,'red']],
  fourbet:      [[0,3,'blue'],[3,8,'green'],[8,100,'red']],
  af:           [[0,1.5,'blue'],[1.5,4,'green'],[4,100,'red']],
  cbet:         [[0,45,'blue'],[45,75,'green'],[75,100,'yellow']],
  fold_to_cbet: [[0,40,'red'],[40,62,'yellow'],[62,100,'green']],
  fold_to_3bet: [[0,45,'red'],[45,65,'yellow'],[65,100,'green']],
  squeeze:      [[0,5,'blue'],[5,12,'green'],[12,100,'red']],
  cold_call:    [[0,10,'blue'],[10,25,'green'],[25,100,'red']],
  donk_bet:     [[0,10,'blue'],[10,25,'yellow'],[25,100,'red']],
  wtsd:         [[0,22,'blue'],[22,35,'green'],[35,100,'red']],
}
const COLOR_MAP = { blue:'text-blue-400', green:'text-green-400', yellow:'text-yellow-400', red:'text-red-400' }

function colorClass(key, val) {
  const ranges = RANGES[key]
  if (!ranges) return 'text-gray-300'
  const v = parseFloat(val) || 0
  for (const [lo, hi, color] of ranges) {
    if (v >= lo && v < hi) return COLOR_MAP[color]
  }
  return COLOR_MAP[ranges[ranges.length - 1][2]]
}

export default function StatGrid({ stats, trends = {} }) {
  return (
    <div className="grid grid-cols-4 gap-1">
      {STATS.map(({ key, label, suffix }) => {
        const val = stats[key]
        const display = val != null ? `${val}${suffix}` : '—'
        const trend = trends[key]
        return (
          <div key={key} className="bg-gray-800 rounded px-1 py-1.5 text-center">
            <div className="text-gray-500 text-xs leading-none mb-1">{label}</div>
            <div className={`text-sm font-bold leading-none ${colorClass(key, val)} flex items-center justify-center`}>
              {display}
              {trend && <TrendBadge dir={trend.dir} delta={trend.delta} />}
            </div>
          </div>
        )
      })}
    </div>
  )
}
