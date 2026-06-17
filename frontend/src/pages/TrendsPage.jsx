import { useEffect, useState } from 'react'
import axios from 'axios'

const API_URL = 'http://localhost:8000'

const STATUS_STYLE = {
  'over-funded': { bg: 'bg-green-50', border: 'border-green-300', text: 'text-green-700', badge: 'bg-green-100 text-green-700' },
  'under-funded': { bg: 'bg-red-50', border: 'border-red-300', text: 'text-red-700', badge: 'bg-red-100 text-red-700' },
  'average': { bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-600', badge: 'bg-gray-100 text-gray-500' },
}

export default function TrendsPage({ onBack }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    axios.get(`${API_URL}/trends/research-areas`)
      .then((res) => setData(res.data))
      .catch(() => setError('Could not load trend data. Make sure the backend is running.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <p className="text-center text-gray-400 mt-20">Loading trend data...</p>
  }

  if (error) {
    return <p className="text-center text-red-500 mt-20">{error}</p>
  }

  const maxTotal = Math.max(...data.historical_dataset_summary.map(d => d.total_requested_amount_lakhs))

  return (
    <div className="max-w-5xl mx-auto">

      
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800">Research Area Trend Analysis</h2>
          <p className="text-gray-500 text-sm mt-1">
            Based on {data.total_historical_proposals} historical proposals — mean approval rate {data.mean_approval_rate_percent}%
          </p>
        </div>
        <button
          onClick={onBack}
          className="text-sm px-4 py-2 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
        >
          Back to Evaluation
        </button>
      </div>

     
      <div className="space-y-3">
        {data.historical_dataset_summary.map((area) => {
          const style = STATUS_STYLE[area.funding_status]
          const barWidth = (area.total_requested_amount_lakhs / maxTotal) * 100
          return (
            <div
              key={area.research_area}
              className={`border border-l-4 rounded-xl p-5 ${style.bg} ${style.border}`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <p className="font-semibold text-gray-800">{area.research_area}</p>
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full uppercase tracking-wide ${style.badge}`}>
                    {area.funding_status}
                  </span>
                </div>
                <p className={`text-lg font-bold ${style.text}`}>
                  {area.approval_rate_percent}%
                  <span className="text-xs font-normal text-gray-400 ml-1">approval rate</span>
                </p>
              </div>

              <div className="grid grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-xs text-gray-400">Total Proposals</p>
                  <p className="font-semibold text-gray-700">{area.total_proposals}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400">Approved</p>
                  <p className="font-semibold text-gray-700">{area.approved_proposals}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400">Avg Requested</p>
                  <p className="font-semibold text-gray-700">{area.avg_requested_amount_lakhs} Lakhs</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400">Avg Duration</p>
                  <p className="font-semibold text-gray-700">{area.avg_duration_months} months</p>
                </div>
              </div>

              <div className="mt-3">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-xs text-gray-400">Total Historical Funding Requested</p>
                  <p className="text-xs text-gray-500 font-semibold">
                    {area.total_requested_amount_lakhs.toLocaleString()} Lakhs
                  </p>
                </div>
                <div className="w-full bg-white bg-opacity-60 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{ width: `${barWidth}%` }}
                  />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <p className="text-xs text-gray-400 mt-6 text-center">
        Funding status is determined relative to the mean approval rate ({data.mean_approval_rate_percent}%)
        across all research areas, using a +/- 5 percentage point threshold.
      </p>

    </div>
  )
}