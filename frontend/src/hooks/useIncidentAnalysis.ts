import { useState } from 'react'
import { IncidentReport } from '../types/Incident'

const API_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000'

export function useIncidentAnalysis() {
  const [report, setReport] = useState<IncidentReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function analyze(sessionId: string) {
    setLoading(true)
    setError(null)
    setReport(null)
    fetch(`${API_URL}/sessions/${sessionId}/incidents`, { method: 'POST' })
      .then(r => {
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
        return r.json() as Promise<IncidentReport>
      })
      .then(setReport)
      .catch(e => setError((e as Error).message))
      .finally(() => setLoading(false))
  }

  return { report, loading, error, analyze }
}
