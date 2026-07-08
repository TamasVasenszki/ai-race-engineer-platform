import { useState } from 'react'
import { useLap } from './hooks/useLap'
import { useIncidentAnalysis } from './hooks/useIncidentAnalysis'
import { LapDashboard } from './components/LapDashboard'
import { IncidentAnalysis } from './components/IncidentAnalysis'

export default function App() {
  const [lapInput, setLapInput] = useState('')
  const [lapId, setLapId] = useState<string | null>(null)
  const { lap, loading: lapLoading, error: lapError } = useLap(lapId)

  const [sessionInput, setSessionInput] = useState('')
  const { report, loading: incLoading, error: incError, analyze } = useIncidentAnalysis()

  function handleLapSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLapId(lapInput.trim())
  }

  function handleIncidentSubmit(e: React.FormEvent) {
    e.preventDefault()
    const id = sessionInput.trim()
    if (id) analyze(id)
  }

  return (
    <div style={{ padding: 32, fontFamily: 'monospace' }}>
      <h1>AI Race Engineer</h1>

      <section style={{ marginBottom: 32 }}>
        <h2>Lap Analysis</h2>
        <form onSubmit={handleLapSubmit} style={{ marginBottom: 24 }}>
          <input
            value={lapInput}
            onChange={e => setLapInput(e.target.value)}
            placeholder="Lap UUID"
            style={{ width: 320, marginRight: 8, padding: '4px 8px' }}
          />
          <button type="submit">Load lap</button>
        </form>
        {lapLoading && <p>Loading...</p>}
        {lapError && <p style={{ color: 'red' }}>Error: {lapError}</p>}
        {lap && <LapDashboard lap={lap} />}
      </section>

      <section>
        <h2>Incident Analysis</h2>
        <form onSubmit={handleIncidentSubmit} style={{ marginBottom: 24 }}>
          <input
            value={sessionInput}
            onChange={e => setSessionInput(e.target.value)}
            placeholder="Session UUID"
            style={{ width: 320, marginRight: 8, padding: '4px 8px' }}
          />
          <button type="submit">Analyze incidents</button>
        </form>
        {incLoading && <p>Analyzing...</p>}
        {incError && <p style={{ color: 'red' }}>Error: {incError}</p>}
        {report && <IncidentAnalysis report={report} />}
      </section>
    </div>
  )
}
