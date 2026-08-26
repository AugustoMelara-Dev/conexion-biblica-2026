import { useEffect } from "react"
import type { ReactNode } from "react"

type FocusShellProps = {
  children: ReactNode
  onExit?: () => void
}

export function FocusShell({ children, onExit }: FocusShellProps) {
  useEffect(() => {
    if (!onExit) return

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape" || event.defaultPrevented) return
      event.preventDefault()
      onExit()
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [onExit])

  return (
    <div className="min-h-screen bg-background text-foreground">
      <a
        className="sr-only fixed top-4 left-4 z-50 rounded-md bg-primary px-4 py-2 text-primary-foreground focus:not-sr-only focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
        href="#main-content"
      >
        Saltar al contenido
      </a>
      <main id="main-content" className="min-h-screen" tabIndex={-1}>
        {children}
      </main>
    </div>
  )
}
