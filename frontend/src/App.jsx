import { useState } from 'react'
import UploadPage from './pages/UploadPage'
import ReportPage from './pages/ReportPage'
import TrendsPage from './pages/TrendsPage'

export default function App() {
  const [report, setReport] = useState(null)
  const [view, setView] = useState('upload')

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-blue-900 text-white py-4 px-8 shadow-md">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight">
              NaCCER R&D Proposal Evaluation System
            </h1>
            <p className="text-blue-300 text-sm">
              CMPDI / Coal India Limited — AI-Powered Auto-Evaluation
            </p>
          </div>
          {!report && (
            <nav className="flex gap-2">
              <button
                onClick={() => setView('upload')}
                className={`text-sm px-4 py-2 rounded-lg transition-colors ${
                  view === 'upload' ? 'bg-white text-blue-900' : 'text-blue-200 hover:bg-blue-800'
                }`}
              >
                Evaluate Proposal
              </button>
              <button
                onClick={() => setView('trends')}
                className={`text-sm px-4 py-2 rounded-lg transition-colors ${
                  view === 'trends' ? 'bg-white text-blue-900' : 'text-blue-200 hover:bg-blue-800'
                }`}
              >
                Trend Analysis
              </button>
            </nav>
          )}
        </div>
      </header>

     
      <main className="max-w-6xl mx-auto px-8 py-10">
        {report ? (
          <ReportPage report={report} onReset={() => setReport(null)} />
        ) : view === 'trends' ? (
          <TrendsPage onBack={() => setView('upload')} />
        ) : (
          <UploadPage onReportReady={setReport} />
        )}
      </main>

      <footer className="text-center text-gray-400 text-xs py-6">
        NaCCER Auto-Evaluation System — For internal review use only
      </footer>
    </div>
  )
}