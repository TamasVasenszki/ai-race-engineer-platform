import { useEffect, useState } from 'react'
import { Incident } from '../types/Incident'
import { useIncidentAnalysis } from '../hooks/useIncidentAnalysis'
import { useWs } from '../context/WebSocketContext'

interface IncidentPanelProps {
  sessionId: string | null
}

export function IncidentPanel({ sessionId }: IncidentPanelProps) {
  const { report, loading, error, analyze } = useIncidentAnalysis()
  const { lastMessage } = useWs()
  const [liveAlerts, setLiveAlerts] = useState<Incident[]>([])

  useEffect(() => {
    setLiveAlerts([])
  }, [sessionId])

  useEffect(() => {
    if (!lastMessage || lastMessage.type !== 'incident_alert') return
    if (lastMessage.session_id !== sessionId) return
    setLiveAlerts(prev => [...prev, ...lastMessage.incidents])
  }, [lastMessage, sessionId])

  const allIncidents = [
    ...liveAlerts,
    ...(report?.incidents ?? []),
  ]

  return (
    <div className="incident-panel">
      <h3 className="section-heading">Incidents</h3>
      {sessionId && (
        <div className="incident-panel__actions">
          <button
            className="incident-panel__btn"
            onClick={() => analyze(sessionId)}
            disabled={loading}
          >
            {loading ? 'Analyzing...' : 'Run Analysis'}
          </button>
        </div>
      )}
      {error && <p className="incident-panel__error">{error}</p>}
      {!sessionId && (
        <p className="incident-panel__empty">Select a session</p>
      )}
      {sessionId && allIncidents.length === 0 && !loading && (
        <p className="incident-panel__empty">No incidents detected</p>
      )}
      <div className="incident-list">
        {allIncidents.map((inc, i) => (
          <div key={i} className={`incident-card card incident-card--${inc.severity}`}>
            <div className="incident-card__header">
              <span className={`badge badge--${inc.severity}`}>
                {inc.severity.toUpperCase()}
              </span>
              <span className="incident-card__lap">Lap {inc.lap_number}</span>
            </div>
            <p className="incident-card__desc">{inc.description}</p>
            <p className="incident-card__cause">
              <strong>Root cause:</strong> {inc.root_cause}
            </p>
            {inc.recommendations.length > 0 && (
              <ul className="incident-card__recs">
                {inc.recommendations.map((rec, j) => (
                  <li key={j}>{rec}</li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
      {report?.provider && (
        <p className="incident-panel__provider">Provider: {report.provider}</p>
      )}
    </div>
  )
}
