import { Session } from '../types/Session'
import { useWs } from '../context/WebSocketContext'

interface SessionSidebarProps {
  sessions: Session[]
  activeId: string | null
  onSelect: (id: string) => void
}

export function SessionSidebar({ sessions, activeId, onSelect }: SessionSidebarProps) {
  const { connected } = useWs()

  return (
    <div className="sidebar-content">
      <h3 className="section-heading">Sessions</h3>
      {sessions.length === 0 && (
        <p className="sidebar-empty">No sessions yet</p>
      )}
      <ul className="session-list">
        {sessions.map((s, i) => (
          <li
            key={s.id}
            className={`session-item ${s.id === activeId ? 'session-item--active' : ''}`}
            onClick={() => onSelect(s.id)}
          >
            <div className="session-item__header">
              <span className="session-item__track">{s.track}</span>
              {i === 0 && connected && <span className="badge badge--info">LIVE</span>}
            </div>
            <span className="session-item__car">{s.car}</span>
            <span className="session-item__time">
              {new Date(s.created_at).toLocaleString(undefined, {
                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
              })}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
