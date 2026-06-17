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
        timeout: 120000, // 2 minute timeout for long pipeline runs
      })
      onReportReady(response.data)
    } catch (err) {
      if (err.code === 'ECONNABORTED') {
        setError(
          'The evaluation is taking longer than expected and timed out. This can happen with ' +
          'very long proposals. Please try again.'
        )
      } else if (err.code === 'ERR_NETWORK' || !err.response) {
        setError(
          'Could not connect to the evaluation server. Please make sure the backend is running ' +
          '(uvicorn on port 8000) and try again.'
        )
      } else if (err.response.status === 422) {
        setError(err.response.data?.detail || 'The PDF could not be processed. Please check the document and try again.')
      } else if (err.response.status === 400) {
        setError(err.response.data?.detail || 'Invalid file. Please upload a valid PDF proposal.')
      } else if (err.response.status === 502) {
        setError(err.response.data?.detail || 'The AI evaluation service is temporarily unavailable. Please try again in a moment.')
      } else {
        setError(err.response?.data?.detail || 'Something went wrong while evaluating the proposal. Please try again.')
      }
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
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700 text-sm font-medium mb-1">Evaluation could not be completed</p>
          <p className="text-red-600 text-sm">{error}</p>
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
        <div className="mt-6">
          <div className="bg-white border border-gray-200 rounded-xl p-5 mb-4">
            <div className="flex items-center gap-3">
              <div className="w-4 h-4 border-2 border-blue-700 border-t-transparent
                              rounded-full animate-spin shrink-0" />
              <p className="text-blue-800 text-sm font-medium">{progress}</p>
            </div>
            <p className="text-gray-400 text-xs mt-3">
              This usually takes 30 to 60 seconds depending on proposal length.
            </p>
          </div>

          
          <div className="space-y-3 opacity-60">
           
            <div className="bg-white border border-gray-200 rounded-xl p-5">
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <div className="h-2.5 w-28 bg-gray-200 rounded animate-pulse" />
                  <div className="h-5 w-40 bg-gray-200 rounded animate-pulse" />
                </div>
                <div className="space-y-2 text-right">
                  <div className="h-2.5 w-20 bg-gray-200 rounded animate-pulse ml-auto" />
                  <div className="h-8 w-16 bg-gray-200 rounded animate-pulse ml-auto" />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-4 gap-3">
              {[0, 1, 2, 3].map((i) => (
                <div key={i} className="bg-white border border-gray-200 rounded-xl p-4">
                  <div className="h-2.5 w-16 bg-gray-200 rounded animate-pulse mb-3" />
                  <div className="h-6 w-12 bg-gray-200 rounded animate-pulse mb-3" />
                  <div className="h-1.5 w-full bg-gray-100 rounded-full" />
                </div>
              ))}
            </div>

            <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-2">
              <div className="h-2.5 w-32 bg-gray-200 rounded animate-pulse mb-2" />
              <div className="h-3 w-full bg-gray-100 rounded animate-pulse" />
              <div className="h-3 w-full bg-gray-100 rounded animate-pulse" />
              <div className="h-3 w-3/4 bg-gray-100 rounded animate-pulse" />
            </div>

            
            {[0, 1, 2].map((i) => (
              <div key={i} className="bg-white border border-gray-200 rounded-xl p-5">
                <div className="flex items-center justify-between">
                  <div className="h-3 w-44 bg-gray-200 rounded animate-pulse" />
                  <div className="h-6 w-12 bg-gray-200 rounded animate-pulse" />
                </div>
              </div>
            ))}
          </div>
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