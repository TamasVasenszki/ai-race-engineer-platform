import { ReactNode } from 'react'
import { ConnectionStatus } from './ConnectionStatus'

interface LayoutProps {
  connected: boolean
  sidebar: ReactNode
  main: ReactNode
  panel: ReactNode
}

export function Layout({ connected, sidebar, main, panel }: LayoutProps) {
  return (
    <div className="app-layout">
      <header className="app-header">
        <span className="app-header__title">AI Race Engineer</span>
        <ConnectionStatus connected={connected} />
      </header>
      <aside className="app-sidebar">{sidebar}</aside>
      <main className="app-main">{main}</main>
      <aside className="app-panel">{panel}</aside>
    </div>
  )
}
