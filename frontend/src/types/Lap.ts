export interface Lap {
  id: string
  session_id: string
  lap_number: number
  lap_time_ms: number
  sector1_ms: number | null
  sector2_ms: number | null
  sector3_ms: number | null
  max_speed_kmh: number | null
  ai_summary: string | null
  ai_recommendations: string[] | null
  created_at: string
}
