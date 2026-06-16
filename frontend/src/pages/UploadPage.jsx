import { useState } from 'react'
import axios from 'axios'

const API_URL = 'http://localhost:8000'

export default function UploadPage({ onReportReady }) {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [progress, setProgress] = useState('')

  const PROGRESS_STEPS = [
    'Extracting proposal sections from PDF...',
    'Running novelty and duplication check...',
    'Checking financial compliance...',
    'Scoring feasibility and relevance...',
    'Running ML approval prediction...',
    'Generating reviewer report...',
  ]

  const handleFileChange = (e) => {
    const selected = e.target.files[0]
    if (selected && selected.type === 'application/pdf') {
      setFile(selected)
      setError(null)
    } else {
      setError('Please select a valid PDF file.')
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    const dropped = e.dataTransfer.files[0]
    if (dropped && dropped.type === 'application/pdf') {
      setFile(dropped)
      setError(null)
    } else {
      setError('Please drop a valid PDF file.')
    }
  }

  const handleSubmit = async () => {
    if (!file) return
    setLoading(true)
    setError(null)

    let stepIndex = 0
    setProgress(PROGRESS_STEPS[0])
    const interval = setInterval(() => {
      stepIndex = Math.min(stepIndex + 1, PROGRESS_STEPS.length - 1)
      setProgress(PROGRESS_STEPS[stepIndex])
    }, 6000)

    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await axios.post(`${API_URL}/evaluate/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      onReportReady(response.data)
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Something went wrong. Make sure the backend is running on port 8000.'
      )
    } finally {
      clearInterval(interval)
      setLoading(false)
      setProgress('')
    }
  }

  return (
    <div className="max-w-2xl mx-auto">

      
      <div className="mb-8 text-center">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Upload R&D Proposal for Evaluation
        </h2>
        <p className="text-gray-500 text-sm">
          Upload a proposal PDF to automatically evaluate novelty, financial
          compliance, feasibility, and approval likelihood.
        </p>
      </div>

      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center
                   bg-white hover:border-blue-500 hover:bg-blue-50 transition-colors cursor-pointer"
        onClick={() => document.getElementById('file-input').click()}
      >
        {file ? (
          <div>
            <p className="text-blue-800 font-semibold text-lg">{file.name}</p>
            <p className="text-gray-400 text-sm mt-1">
              {(file.size / 1024).toFixed(1)} KB — Click to change
            </p>
          </div>
        ) : (
          <div>
            <p className="text-gray-500 font-medium">
              Drag and drop your proposal PDF here
            </p>
            <p className="text-gray-400 text-sm mt-2">or click to browse files</p>
          </div>
        )}
        <input
          id="file-input"
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={handleFileChange}
        />
      </div>

      
      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
          {error}
        </div>
      )}

      
      <button
        onClick={handleSubmit}
        disabled={!file || loading}
        className="mt-6 w-full py-3 px-6 bg-blue-900 text-white font-semibold
                   rounded-xl hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed
                   transition-colors"
      >
        {loading ? 'Evaluating...' : 'Run Evaluation'}
      </button>

      
      {loading && (
        <div className="mt-6 bg-white border border-gray-200 rounded-xl p-5">
          <div className="flex items-center gap-3">
            <div className="w-4 h-4 border-2 border-blue-700 border-t-transparent
                            rounded-full animate-spin shrink-0" />
            <p className="text-blue-800 text-sm font-medium">{progress}</p>
          </div>
          <p className="text-gray-400 text-xs mt-3">
            This usually takes 30 to 60 seconds depending on proposal length.
          </p>
        </div>
      )}

     
      <div className="mt-10 grid grid-cols-2 gap-4">
        {[
          { title: 'Novelty Check', desc: 'Section-level comparison against past funded proposals' },
          { title: 'Financial Compliance', desc: 'Budget validation against S&T funding guidelines' },
          { title: 'Feasibility Scoring', desc: 'Relevance to CIL and MoC priority research areas' },
          { title: 'ML Prediction', desc: 'Approval likelihood with SHAP factor explanation' },
        ].map((item) => (
          <div key={item.title} className="bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
            <p className="font-semibold text-gray-700 text-sm">{item.title}</p>
            <p className="text-gray-400 text-xs mt-1">{item.desc}</p>
          </div>
        ))}
      </div>

    </div>
  )
}