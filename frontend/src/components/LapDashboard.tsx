import { Lap } from '../types/Lap'

function formatLapTime(ms: number): string {
  const minutes = Math.floor(ms / 60000)
  const seconds = Math.floor((ms % 60000) / 1000)
  const millis = ms % 1000
  return `${minutes}:${String(seconds).padStart(2, '0')}.${String(millis).padStart(3, '0')}`
}

export function LapDashboard({ lap }: { lap: Lap }) {
  return (
    <div style={{ fontFamily: 'monospace', maxWidth: 600, margin: '0 auto' }}>
      <h2>Lap #{lap.lap_number}</h2>
      <p><strong>Lap time:</strong> {formatLapTime(lap.lap_time_ms)}</p>
      {lap.max_speed_kmh !== null && (
        <p><strong>Max speed:</strong> {lap.max_speed_kmh.toFixed(1)} km/h</p>
      )}
      {lap.sector1_ms !== null && (
        <p>
          <strong>Sectors:</strong>{' '}
          S1 {formatLapTime(lap.sector1_ms)}
          {lap.sector2_ms !== null && ` · S2 ${formatLapTime(lap.sector2_ms)}`}
          {lap.sector3_ms !== null && ` · S3 ${formatLapTime(lap.sector3_ms)}`}
        </p>
      )}
      {lap.ai_summary && (
        <section style={{ marginTop: 24 }}>
          <h3>AI Analysis</h3>
          <p>{lap.ai_summary}</p>
        </section>
      )}
      {lap.ai_recommendations && lap.ai_recommendations.length > 0 && (
        <section style={{ marginTop: 16 }}>
          <h3>Recommendations</h3>
          <ul>
            {lap.ai_recommendations.map((rec, i) => (
              <li key={i}>{rec}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
