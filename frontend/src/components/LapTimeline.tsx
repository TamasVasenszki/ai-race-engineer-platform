import { Lap } from '../types/Lap'
import { formatLapTime } from '../utils/format'

interface LapTimelineProps {
  laps: Lap[]
  loading: boolean
}

export function LapTimeline({ laps, loading }: LapTimelineProps) {
  if (loading) {
    return <p className="timeline-empty">Loading laps...</p>
  }

  if (laps.length === 0) {
    return <p className="timeline-empty">No laps recorded — waiting for data</p>
  }

  const bestTime = Math.min(...laps.map(l => l.lap_time_ms))
  const maxTime = Math.max(...laps.map(l => l.lap_time_ms))

  return (
    <div className="lap-timeline">
      <h3 className="section-heading">Lap Timeline</h3>
      <div className="lap-list">
        {laps.map((lap, i) => {
          const isBest = lap.lap_time_ms === bestTime && laps.length > 1
          const barWidth = maxTime > 0 ? (lap.lap_time_ms / maxTime) * 100 : 100
          const isNew = i === laps.length - 1 && laps.length > 1

          return (
            <div
              key={lap.id}
              className={`lap-row card ${isBest ? 'lap-row--best' : ''} ${isNew ? 'lap-row--new' : ''}`}
            >
              <div className="lap-row__header">
                <span className="lap-row__number">L{lap.lap_number}</span>
                <span className={`lap-row__time ${isBest ? 'lap-row__time--best' : ''}`}>
                  {formatLapTime(lap.lap_time_ms)}
                </span>
                {isBest && <span className="badge badge--info">BEST</span>}
              </div>
              <div className="lap-row__bar-track">
                <div
                  className={`lap-row__bar ${isBest ? 'lap-row__bar--best' : ''}`}
                  style={{ width: `${barWidth}%` }}
                />
              </div>
              <div className="lap-row__details">
                {lap.sector1_ms != null && (
                  <span className="lap-row__sector">S1 {formatLapTime(lap.sector1_ms)}</span>
                )}
                {lap.sector2_ms != null && (
                  <span className="lap-row__sector">S2 {formatLapTime(lap.sector2_ms)}</span>
                )}
                {lap.sector3_ms != null && (
                  <span className="lap-row__sector">S3 {formatLapTime(lap.sector3_ms)}</span>
                )}
                {lap.max_speed_kmh != null && (
                  <span className="lap-row__speed">{lap.max_speed_kmh.toFixed(0)} km/h</span>
                )}
              </div>
              {lap.ai_summary && (
                <p className="lap-row__ai">{lap.ai_summary}</p>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
