export default function ScoreCard({ label, value, max = 100, invert = false, suffix = '' }) {
  const numeric = parseFloat(value) || 0
  const percent = Math.min((numeric / max) * 100, 100)

  
  const getColor = () => {
    const effective = invert ? percent : percent
    if (effective >= 70) return { bar: 'bg-green-500', text: 'text-green-700' }
    if (effective >= 40) return { bar: 'bg-yellow-400', text: 'text-yellow-700' }
    return { bar: 'bg-red-400', text: 'text-red-600' }
  }

  const color = getColor()

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
        {label}
      </p>
      <p className={`text-3xl font-bold ${color.text} mb-3`}>
        {numeric}{suffix}
        <span className="text-sm font-normal text-gray-400">/{max}{suffix}</span>
      </p>
      <div className="w-full bg-gray-100 rounded-full h-1.5">
        <div
          className={`${color.bar} h-1.5 rounded-full transition-all`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  )
}