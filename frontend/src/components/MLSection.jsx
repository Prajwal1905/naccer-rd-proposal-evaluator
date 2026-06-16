import { useState } from 'react'

export default function MLSection({ data }) {
  const [open, setOpen] = useState(false)

  if (!data) return null

  const prob = Math.round((data.approval_probability || 0) * 100)
  const approved = prob >= 50
  const borderColor = prob >= 70
    ? 'border-green-400'
    : prob >= 50
    ? 'border-yellow-400'
    : 'border-red-400'

  return (
    <div className={`bg-white border border-l-4 ${borderColor} rounded-xl shadow-sm`}>

      
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-6 py-4 text-left"
      >
        <div>
          <p className="font-semibold text-gray-800">ML Approval Prediction</p>
          <p className="text-sm text-gray-500 mt-0.5">
            {data.predicted_label} — based on historical proposal outcomes
          </p>
        </div>
        <div className="flex items-center gap-4 shrink-0 ml-4">
          <div className="text-right">
            <p className="text-xs text-gray-400 uppercase tracking-widest">
              Approval Probability
            </p>
            <p className={`text-xl font-bold ${
              approved ? 'text-green-700' : 'text-red-600'
            }`}>
              {prob}%
            </p>
          </div>
          <span className="text-gray-400 text-sm">{open ? '▲' : '▼'}</span>
        </div>
      </button>

      {open && (
        <div className="px-6 pb-6 border-t border-gray-100">

          
          <div className="mt-4">
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs text-gray-400">Rejection likelihood</p>
              <p className="text-xs text-gray-400">Approval likelihood</p>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-3 relative">
              <div
                className={`h-3 rounded-full ${approved ? 'bg-green-500' : 'bg-red-400'}`}
                style={{ width: `${prob}%` }}
              />
              <div
                className="absolute top-0 h-3 w-0.5 bg-gray-400"
                style={{ left: '50%' }}
              />
            </div>
            <div className="flex justify-between mt-1">
              <p className="text-xs text-gray-400">0%</p>
              <p className="text-xs text-gray-400 font-semibold">50% threshold</p>
              <p className="text-xs text-gray-400">100%</p>
            </div>
          </div>

        
          <div className="mt-5">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
              Input Features Used
            </p>
            <div className="grid grid-cols-3 gap-3">
              {Object.entries(data.input_features || {}).map(([key, value]) => (
                <div key={key} className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-400 capitalize">
                    {key.replace(/_/g, ' ')}
                  </p>
                  <p className="text-sm font-semibold text-gray-700 mt-0.5 capitalize">
                    {String(value)}
                  </p>
                </div>
              ))}
            </div>
          </div>

         
          <div className="mt-5">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
              Top Contributing Factors (SHAP)
            </p>
            <div className="space-y-3">
              {(data.top_factors || []).map((factor, i) => {
                const isPositive = factor.direction === 'increases'
                const barWidth = Math.min(Math.abs(factor.shap_value) * 500, 100)
                return (
                  <div key={i} className="flex items-center gap-3">
                    <p className="text-sm text-gray-600 w-56 shrink-0 capitalize">
                      {factor.feature}
                    </p>
                    <div className="flex-1 bg-gray-100 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          isPositive ? 'bg-green-500' : 'bg-red-400'
                        }`}
                        style={{ width: `${barWidth}%` }}
                      />
                    </div>
                    <p className={`text-xs font-semibold w-28 text-right ${
                      isPositive ? 'text-green-600' : 'text-red-500'
                    }`}>
                      {isPositive ? '+' : ''}{factor.shap_value.toFixed(4)}{' '}
                      <span className="font-normal text-gray-400">
                        {factor.direction} approval
                      </span>
                    </p>
                  </div>
                )
              })}
            </div>
          </div>

      
          {data.warnings?.length > 0 && (
            <div className="mt-5">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-2">
                Warnings
              </p>
              {data.warnings.map((w, i) => (
                <p key={i} className="text-xs text-yellow-700 bg-yellow-50 rounded px-3 py-2">
                  {w}
                </p>
              ))}
            </div>
          )}

        </div>
      )}
    </div>
  )
}