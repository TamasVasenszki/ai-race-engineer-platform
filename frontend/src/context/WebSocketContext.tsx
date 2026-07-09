import { createContext, useContext, ReactNode } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'
import { WsMessage } from '../types/WebSocket'

interface WebSocketState {
  lastMessage: WsMessage | null
  connected: boolean
}

const WebSocketContext = createContext<WebSocketState>({
  lastMessage: null,
  connected: false,
})

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const ws = useWebSocket()
  return (
    <WebSocketContext.Provider value={ws}>
      {children}
    </WebSocketContext.Provider>
  )
}

export function useWs() {
  return useContext(WebSocketContext)
}
