import { IncidentReport } from '../types/Incident'

const badgeStyle = (severity: string): React.CSSProperties => ({
  display: 'inline-block',
  padding: '2px 8px',
  borderRadius: 4,
  color: '#fff',
  fontWeight: 'bold',
  fontSize: 12,
  backgroundColor: severity === 'critical' ? '#d32f2f' : '#ed6c02',
})

export function IncidentAnalysis({ report }: { report: IncidentReport }) {
  return (
    <div style={{ fontFamily: 'monospace', maxWidth: 600, margin: '0 auto' }}>
      <h2>Incident Analysis</h2>
      {report.incidents.length === 0 ? (
        <p>No incidents detected.</p>
      ) : (
        report.incidents.map((inc, i) => (
          <div key={i} style={{ marginBottom: 20, padding: 12, border: '1px solid #ccc', borderRadius: 6 }}>
            <div style={{ marginBottom: 8 }}>
              <span style={badgeStyle(inc.severity)}>{inc.severity.toUpperCase()}</span>
              <strong style={{ marginLeft: 8 }}>Lap {inc.lap_number}</strong>
            </div>
            <p style={{ margin: '4px 0' }}>{inc.description}</p>
            <p style={{ margin: '4px 0' }}>
              <strong>Root cause:</strong> {inc.root_cause}
            </p>
            {inc.recommendations.length > 0 && (
              <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
                {inc.recommendations.map((rec, j) => (
                  <li key={j}>{rec}</li>
                ))}
              </ul>
            )}
          </div>
        ))
      )}
      <p style={{ fontSize: 11, color: '#888', marginTop: 12 }}>Provider: {report.provider}</p>
    </div>
  )
}
