import { useState, useEffect } from 'react'
import { WebSocketProvider, useWs } from './context/WebSocketContext'
import { useSessions } from './hooks/useSessions'
import { useSessionLaps } from './hooks/useSessionLaps'
import { Layout } from './components/Layout'
import { SessionSidebar } from './components/SessionSidebar'
import { LapTimeline } from './components/LapTimeline'
import { IncidentPanel } from './components/IncidentPanel'

function Dashboard() {
  const { connected, lastMessage } = useWs()
  const { sessions, refetch } = useSessions()
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const { laps, loading: lapsLoading } = useSessionLaps(activeSessionId, lastMessage)

  useEffect(() => {
    if (sessions.length > 0 && activeSessionId === null) {
      setActiveSessionId(sessions[0].id)
    }
  }, [sessions, activeSessionId])

  useEffect(() => {
    if (lastMessage?.type === 'new_lap') {
      const lapSessionId = lastMessage.lap.session_id
      if (!sessions.some(s => s.id === lapSessionId)) {
        refetch()
      }
    }
  }, [lastMessage, sessions, refetch])

  return (
    <Layout
      connected={connected}
      sidebar={
        <SessionSidebar
          sessions={sessions}
          activeId={activeSessionId}
          onSelect={setActiveSessionId}
        />
      }
      main={<LapTimeline laps={laps} loading={lapsLoading} />}
      panel={<IncidentPanel sessionId={activeSessionId} />}
    />
  )
}

export default function App() {
  return (
    <WebSocketProvider>
      <Dashboard />
    </WebSocketProvider>
  )
}
