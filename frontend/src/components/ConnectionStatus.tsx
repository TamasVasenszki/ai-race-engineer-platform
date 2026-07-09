interface ConnectionStatusProps {
  connected: boolean
}

export function ConnectionStatus({ connected }: ConnectionStatusProps) {
  const cls = connected ? 'connection-status--live' : 'connection-status--offline'
  return (
    <div className={`connection-status ${cls}`}>
      <span className="connection-status__dot" />
      <span className="connection-status__label">
        {connected ? 'LIVE' : 'OFFLINE'}
      </span>
    </div>
  )
}
