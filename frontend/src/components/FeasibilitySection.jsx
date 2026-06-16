import { useState } from 'react'

export default function FeasibilitySection({ data }) {
  const [open, setOpen] = useState(false)

  if (!data) return null

  const score = data.relevance_score ?? 0
  const borderColor = score >= 70
    ? 'border-green-400'
    : score >= 40
    ? 'border-yellow-400'
    : 'border-red-400'

  const CATEGORY_SCORE = { HIGH: 40, MEDIUM: 25, LOWER: 10, UNCLEAR: 5 }
  const priorityScore = CATEGORY_SCORE[data.priority_area_match?.category] ?? null

  const subScores = [
    {
      label: 'Priority Area Match',
      value: priorityScore,
      max: 40,
      reasoning: data.priority_area_match?.reasoning,
    },
    {
      label: 'Operational Specificity',
      value: data.operational_specificity?.score_out_of_25,
      max: 25,
      reasoning: data.operational_specificity?.reasoning,
    },
    {
      label: 'Technology Domain Alignment',
      value: data.technology_domain_alignment?.score_out_of_20,
      max: 20,
      reasoning: data.technology_domain_alignment?.reasoning,
    },
    {
      label: 'Differentiation from Prior Work',
      value: data.differentiation_from_prior_work?.score_out_of_15,
      max: 15,
      reasoning: data.differentiation_from_prior_work?.reasoning,
    },
  ]

  return (
    <div className={`bg-white border border-l-4 ${borderColor} rounded-xl shadow-sm`}>

     
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-6 py-4 text-left"
      >
        <div>
          <p className="font-semibold text-gray-800">Feasibility and Relevance Check</p>
          <p className="text-sm text-gray-500 mt-0.5">
            Priority area: {data.priority_area_match?.matched_area_name || '—'}
            {' — '}
            Category: {data.priority_area_match?.category || '—'}
          </p>
        </div>
        <div className="flex items-center gap-4 shrink-0 ml-4">
          <div className="text-right">
            <p className="text-xs text-gray-400 uppercase tracking-widest">Relevance Score</p>
            <p className="text-xl font-bold text-gray-800">
              {score}<span className="text-sm font-normal text-gray-400">/100</span>
            </p>
          </div>
          <span className="text-gray-400 text-sm">{open ? '▲' : '▼'}</span>
        </div>
      </button>

      {open && (
        <div className="px-6 pb-6 border-t border-gray-100">

          
          <div className="mt-4 flex items-center gap-3">
            <span className={`text-xs font-bold px-3 py-1 rounded-full uppercase tracking-widest ${
              data.priority_area_match?.category === 'HIGH'
                ? 'bg-green-100 text-green-700'
                : data.priority_area_match?.category === 'MEDIUM'
                ? 'bg-yellow-100 text-yellow-700'
                : 'bg-gray-100 text-gray-500'
            }`}>
              {data.priority_area_match?.category} Priority
            </span>
            <p className="text-sm font-semibold text-gray-700">
              {data.priority_area_match?.matched_area_name}
            </p>
          </div>

          
          <div className="mt-5">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
              Score Breakdown
            </p>
            <div className="space-y-4">
              {subScores.map((item, i) => {
                const pct = item.value != null
                  ? Math.min((item.value / item.max) * 100, 100)
                  : 0
                return (
                  <div key={i}>
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-sm text-gray-600">{item.label}</p>
                      <p className="text-sm font-semibold text-gray-800">
                        {item.value ?? '—'}
                        <span className="text-xs font-normal text-gray-400">/{item.max}</span>
                      </p>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-1.5">
                      <div
                        className="bg-blue-500 h-1.5 rounded-full"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    {item.reasoning && (
                      <p className="text-xs text-gray-400 mt-1">{item.reasoning}</p>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          
          <div className="mt-5 bg-gray-50 rounded-lg p-4">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-2">
              Overall Reasoning
            </p>
            <p className="text-sm text-gray-600">{data.overall_reasoning}</p>
          </div>

        </div>
      )}
    </div>
  )
}