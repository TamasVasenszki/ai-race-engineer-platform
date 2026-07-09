import { useState, useEffect } from 'react'
import { Lap } from '../types/Lap'
import { WsMessage } from '../types/WebSocket'

const API_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000'

export function useSessionLaps(sessionId: string | null, lastMessage: WsMessage | null) {
  const [laps, setLaps] = useState<Lap[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) {
      setLaps([])
      return
    }
    setLoading(true)
    setError(null)
    fetch(`${API_URL}/sessions/${sessionId}/laps`)
      .then(r => {
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
        return r.json() as Promise<Lap[]>
      })
      .then(setLaps)
      .catch(e => setError((e as Error).message))
      .finally(() => setLoading(false))
  }, [sessionId])

  useEffect(() => {
    if (!lastMessage || lastMessage.type !== 'new_lap') return
    if (lastMessage.lap.session_id !== sessionId) return
    setLaps(prev => {
      if (prev.some(l => l.id === lastMessage.lap.id)) return prev
      return [...prev, lastMessage.lap]
    })
  }, [lastMessage, sessionId])

  return { laps, loading, error }
}
