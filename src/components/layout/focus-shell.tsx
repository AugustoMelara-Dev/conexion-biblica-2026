import type { ReactNode } from "react"

type FocusShellProps = {
  children: ReactNode
  onExit?: () => void
}

export function FocusShell({ children }: FocusShellProps) {
  return (
    <div className="min-h-screen bg-background text-foreground">{children}</div>
  )
}
