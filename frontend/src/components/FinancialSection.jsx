import { useState } from 'react'

const SEVERITY_STYLE = {
  HIGH: 'bg-red-50 border-red-300 text-red-700',
  MEDIUM: 'bg-yellow-50 border-yellow-300 text-yellow-700',
  LOW: 'bg-blue-50 border-blue-200 text-blue-700',
}

export default function FinancialSection({ data }) {
  const [open, setOpen] = useState(false)

  if (!data) return null

  const score = data.compliance_score ?? 0
  const issueCount = (data.issues || []).length
  const borderColor = score >= 80
    ? 'border-green-400'
    : score >= 50
    ? 'border-yellow-400'
    : 'border-red-400'

  const pct = data.budget_percentages?.percentages_of_tpc || {}
  const CEILINGS = {
    manpower_lakhs: 40,
    equipment_lakhs: 30,
    consumables_lakhs: 15,
    contingency_travel_lakhs: 8,
    overheads_lakhs: 15,
    contractual_services_lakhs: 10,
  }

  const HEAD_LABELS = {
    manpower_lakhs: 'Manpower',
    equipment_lakhs: 'Equipment',
    consumables_lakhs: 'Consumables',
    contingency_travel_lakhs: 'Contingency & Travel',
    overheads_lakhs: 'Institutional Overhead',
    contractual_services_lakhs: 'Contractual Services',
    other_lakhs: 'Other',
  }

  return (
    <div className={`bg-white border border-l-4 ${borderColor} rounded-xl shadow-sm`}>

      
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-6 py-4 text-left"
      >
        <div>
          <p className="font-semibold text-gray-800">Financial Compliance Check</p>
          <p className="text-sm text-gray-500 mt-0.5">
            {issueCount === 0
              ? 'No compliance issues found.'
              : `${issueCount} issue${issueCount > 1 ? 's' : ''} identified.`}
          </p>
        </div>
        <div className="flex items-center gap-4 shrink-0 ml-4">
          <div className="text-right">
            <p className="text-xs text-gray-400 uppercase tracking-widest">Compliance Score</p>
            <p className="text-xl font-bold text-gray-800">
              {score}<span className="text-sm font-normal text-gray-400">/100</span>
            </p>
          </div>
          <span className="text-gray-400 text-sm">{open ? '▲' : '▼'}</span>
        </div>
      </button>

      {open && (
        <div className="px-6 pb-6 border-t border-gray-100">

          
          <div className="mt-4 grid grid-cols-3 gap-3">
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-400 uppercase tracking-widest">Total Project Cost</p>
              <p className="text-lg font-bold text-gray-800 mt-1">
                INR {data.extracted_budget?.total_project_cost_lakhs ?? '—'} Lakhs
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-400 uppercase tracking-widest">Duration</p>
              <p className="text-lg font-bold text-gray-800 mt-1">
                {data.extracted_budget?.duration_months ?? '—'} months
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-400 uppercase tracking-widest">Institution Type</p>
              <p className="text-lg font-bold text-gray-800 mt-1 capitalize">
                {data.extracted_budget?.institution_type ?? '—'}
              </p>
            </div>
          </div>

          
          <div className="mt-5">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
              Budget Head Breakdown (% of TPC)
            </p>
            <div className="space-y-2">
              {Object.entries(pct).map(([head, value]) => {
                if (value === null || value === undefined) return null
                const ceiling = CEILINGS[head]
                const over = ceiling && value > ceiling
                return (
                  <div key={head} className="flex items-center gap-3">
                    <p className="text-sm text-gray-600 w-44 shrink-0">
                      {HEAD_LABELS[head] || head}
                    </p>
                    <div className="flex-1 bg-gray-100 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${over ? 'bg-red-400' : 'bg-blue-500'}`}
                        style={{ width: `${Math.min(value, 100)}%` }}
                      />
                    </div>
                    <p className={`text-sm font-semibold w-16 text-right ${
                      over ? 'text-red-500' : 'text-gray-700'
                    }`}>
                      {value}%
                      {ceiling && (
                        <span className="text-xs font-normal text-gray-400 ml-1">
                          / {ceiling}%
                        </span>
                      )}
                    </p>
                  </div>
                )
              })}
            </div>
          </div>

         
          {data.issues?.length > 0 && (
            <div className="mt-5">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
                Compliance Issues
              </p>
              <div className="space-y-3">
                {data.issues.map((issue, i) => (
                  <div
                    key={i}
                    className={`border rounded-lg p-4 ${SEVERITY_STYLE[issue.severity] || 'bg-gray-50 border-gray-200 text-gray-600'}`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold uppercase tracking-wider">
                        {issue.severity}
                      </span>
                      <span className="text-xs text-gray-400">{issue.guideline_reference}</span>
                    </div>
                    <p className="text-sm font-medium">{issue.issue}</p>
                    <p className="text-xs mt-1 opacity-80">{issue.recommendation}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          
          <div className="mt-5 bg-gray-50 rounded-lg p-4">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-2">
              Overall Assessment
            </p>
            <p className="text-sm text-gray-600">{data.overall_assessment}</p>
          </div>

        </div>
      )}
    </div>
  )
}