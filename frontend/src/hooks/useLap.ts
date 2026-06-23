import { useState, useEffect } from 'react'
import { Lap } from '../types/Lap'

const API_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000'

export function useLap(lapId: string | null) {
  const [lap, setLap] = useState<Lap | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!lapId) return
    setLoading(true)
    setError(null)
    fetch(`${API_URL}/laps/${lapId}`)
      .then(r => {
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
        return r.json() as Promise<Lap>
      })
      .then(setLap)
      .catch(e => setError((e as Error).message))
      .finally(() => setLoading(false))
  }, [lapId])

  return { lap, loading, error }
}
