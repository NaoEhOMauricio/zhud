const POSITIONS = [
  { key: 'pos_btn', label: 'BTN' },
  { key: 'pos_co',  label: 'CO'  },
  { key: 'pos_sb',  label: 'SB'  },
  { key: 'pos_bb',  label: 'BB'  },
  { key: 'pos_ep',  label: 'EP'  },
]

function colorVpip(v) {
  if (v < 15) return 'text-blue-400'
  if (v < 35) return 'text-green-400'
  return 'text-red-400'
}

function colorPfr(v) {
  if (v < 12) return 'text-blue-400'
  if (v < 28) return 'text-green-400'
  return 'text-red-400'
}

export default function PositionStats({ stats }) {
  const rows = POSITIONS
    .map(({ key, label }) => ({ label, data: stats[key] }))
    .filter(({ data }) => data && (data.hands || 0) >= 5)

  if (rows.length === 0) return null

  return (
    <div className="mt-1">
      <div className="text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wider">
        Por posição
      </div>
      <table className="w-full text-xs">
        <thead>
          <tr className="text-gray-600">
            <th className="text-left font-normal pb-1">Pos</th>
            <th className="text-right font-normal pb-1">Mãos</th>
            <th className="text-right font-normal pb-1">VPIP</th>
            <th className="text-right font-normal pb-1">PFR</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ label, data }) => (
            <tr key={label} className="border-t border-gray-800">
              <td className="py-1 text-gray-300 font-semibold">{label}</td>
              <td className="py-1 text-right text-gray-600">{data.hands}</td>
              <td className={`py-1 text-right font-bold ${colorVpip(data.vpip)}`}>
                {data.vpip}%
              </td>
              <td className={`py-1 text-right font-bold ${colorPfr(data.pfr)}`}>
                {data.pfr}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
