export interface Incident {
  lap_number: number
  severity: string
  description: string
  root_cause: string
  recommendations: string[]
}

export interface IncidentReport {
  incidents: Incident[]
  provider: string
}
