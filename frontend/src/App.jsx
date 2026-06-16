import { useState } from 'react'
import UploadPage from './pages/UploadPage'
import ReportPage from './pages/ReportPage'

export default function App() {
  const [report, setReport] = useState(null)

  return (
    <div className="min-h-screen bg-gray-50">
      
      <header className="bg-blue-900 text-white py-4 px-8 shadow-md">
        <div className="max-w-6xl mx-auto flex items-center gap-3">
          <div>
            <h1 className="text-xl font-bold tracking-tight">
              NaCCER R&D Proposal Evaluation System
            </h1>
            <p className="text-blue-300 text-sm">
              CMPDI / Coal India Limited — AI-Powered Auto-Evaluation
            </p>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-8 py-10">
        {!report ? (
          <UploadPage onReportReady={setReport} />
        ) : (
          <ReportPage report={report} onReset={() => setReport(null)} />
        )}
      </main>

      <footer className="text-center text-gray-400 text-xs py-6">
        NaCCER Auto-Evaluation System — For internal review use only
      </footer>
    </div>
  )
}