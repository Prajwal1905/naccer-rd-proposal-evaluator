const DIMENSION_STYLE = {
  novelty: {
    label: 'Novelty',
    style: 'bg-purple-50 border-purple-200',
    badge: 'bg-purple-100 text-purple-700',
  },
  financial_compliance: {
    label: 'Financial Compliance',
    style: 'bg-blue-50 border-blue-200',
    badge: 'bg-blue-100 text-blue-700',
  },
  feasibility_relevance: {
    label: 'Feasibility / Relevance',
    style: 'bg-orange-50 border-orange-200',
    badge: 'bg-orange-100 text-orange-700',
  },
}

export default function SuggestionsSection({ data }) {
  if (!data || data.length === 0) return null

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm">

     
      <div className="px-6 py-4 border-b border-gray-100">
        <p className="font-semibold text-gray-800">Improvement Suggestions</p>
        <p className="text-sm text-gray-500 mt-0.5">
          Actionable recommendations for resubmission
        </p>
      </div>

      
      <div className="px-6 py-5 space-y-4">
        {data.map((item, i) => {
          const dim = DIMENSION_STYLE[item.dimension] || {
            label: item.dimension,
            style: 'bg-gray-50 border-gray-200',
            badge: 'bg-gray-100 text-gray-600',
          }
          return (
            <div
              key={i}
              className={`border rounded-xl p-4 ${dim.style}`}
            >
              <div className="flex items-center gap-2 mb-2">
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${dim.badge}`}>
                  {dim.label}
                </span>
                <p className="text-sm font-semibold text-gray-700">
                  {item.issue_summary}
                </p>
              </div>
              <p className="text-sm text-gray-600 leading-relaxed">
                {item.suggestion}
              </p>
            </div>
          )
        })}
      </div>

    </div>
  )
}