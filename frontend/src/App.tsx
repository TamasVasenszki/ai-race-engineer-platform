import { useState } from 'react'
import { useLap } from './hooks/useLap'
import { LapDashboard } from './components/LapDashboard'

export default function App() {
  const [input, setInput] = useState('')
  const [lapId, setLapId] = useState<string | null>(null)
  const { lap, loading, error } = useLap(lapId)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLapId(input.trim())
  }

  return (
    <div style={{ padding: 32, fontFamily: 'monospace' }}>
      <h1>AI Race Engineer</h1>
      <form onSubmit={handleSubmit} style={{ marginBottom: 24 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Lap UUID"
          style={{ width: 320, marginRight: 8, padding: '4px 8px' }}
        />
        <button type="submit">Load lap</button>
      </form>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      {lap && <LapDashboard lap={lap} />}
    </div>
  )
}
