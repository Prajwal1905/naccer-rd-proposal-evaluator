import { useState } from 'react'

export default function NoveltySection({ data }) {
  const [open, setOpen] = useState(false)

  if (!data) return null

  const flagCount = (data.flags || []).length
  const borderColor = flagCount === 0
    ? 'border-green-400'
    : data.overall_novelty_score < 50
    ? 'border-red-400'
    : 'border-yellow-400'

  return (
    <div className={`bg-white border border-l-4 ${borderColor} rounded-xl shadow-sm`}>

      
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-6 py-4 text-left"
      >
        <div>
          <p className="font-semibold text-gray-800">Novelty / Duplication Check</p>
          <p className="text-sm text-gray-500 mt-0.5">{data.summary}</p>
        </div>
        <div className="flex items-center gap-4 shrink-0 ml-4">
          <div className="text-right">
            <p className="text-xs text-gray-400 uppercase tracking-widest">Novelty Score</p>
            <p className="text-xl font-bold text-gray-800">{data.overall_novelty_score}<span className="text-sm font-normal text-gray-400">/100</span></p>
          </div>
          <span className="text-gray-400 text-sm">{open ? '▲' : '▼'}</span>
        </div>
      </button>

      
      {open && (
        <div className="px-6 pb-6 border-t border-gray-100">

          
          {data.flags?.length > 0 && (
            <div className="mt-4">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-2">
                Flags
              </p>
              <ul className="space-y-2">
                {data.flags.map((flag, i) => (
                  <li key={i} className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">
                    {flag}
                  </li>
                ))}
              </ul>
            </div>
          )}

          
          {Object.entries(data.section_results || {}).map(([section, matches]) => (
            <div key={section} className="mt-6">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
                {section} — Top Matches
              </p>
              <div className="space-y-3">
                {matches.map((match, i) => (
                  <div key={i} className="border border-gray-100 rounded-lg p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-sm font-semibold text-gray-700">
                          {match.matched_title}
                        </p>
                        <p className="text-xs text-gray-400 mt-0.5">
                          {match.matched_proposal_id} — {match.matched_research_area}
                        </p>
                      </div>
                      <div className="text-right shrink-0">
                        <p className={`text-lg font-bold ${
                          match.similarity_percent >= 75
                            ? 'text-red-500'
                            : match.similarity_percent >= 55
                            ? 'text-yellow-500'
                            : 'text-green-600'
                        }`}>
                          {match.similarity_percent}%
                        </p>
                        <p className="text-xs text-gray-400">similarity</p>
                      </div>
                    </div>
                    {match.overlap_explanation && (
                      <div className="mt-3 pt-3 border-t border-gray-100">
                        <p className="text-xs text-gray-500">{match.overlap_explanation}</p>
                        {match.verdict && (
                          <span className={`inline-block mt-2 text-xs font-semibold px-2 py-0.5 rounded-full ${
                            match.verdict === 'duplicative'
                              ? 'bg-red-100 text-red-600'
                              : match.verdict === 'extension'
                              ? 'bg-blue-100 text-blue-600'
                              : 'bg-gray-100 text-gray-500'
                          }`}>
                            {match.verdict.replace('_', ' ')}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}

        </div>
      )}
    </div>
  )
}