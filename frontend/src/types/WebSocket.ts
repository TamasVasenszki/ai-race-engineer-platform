import { Incident } from './Incident'
import { Lap } from './Lap'

export type WsMessage =
  | { type: 'new_lap'; lap: Lap }
  | { type: 'incident_alert'; session_id: string; incidents: Incident[] }
