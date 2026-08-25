import { useState } from "react"
import { BookOpen, ChartNoAxesColumn, ClipboardList, Database, History, LayoutDashboard, Menu, Moon, PanelLeft, Sun, Upload, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { useTheme } from "@/components/theme-provider"
import type { ReactNode } from "react"
import { useApp } from "@/app/app-state"

type NavKey = "dashboard" | "banks" | "practice" | "stats" | "history" | "review"

const navItems: { key: NavKey; label: string; icon: typeof LayoutDashboard }[] = [
  { key: "dashboard", label: "Resumen", icon: LayoutDashboard },
  { key: "practice", label: "Practicar", icon: BookOpen },
  { key: "banks", label: "Banco de preguntas", icon: Database },
  { key: "stats", label: "Estadísticas", icon: ChartNoAxesColumn },
  { key: "history", label: "Historial", icon: History },
  { key: "review", label: "Revisar preguntas", icon: ClipboardList },
]

function Brand() {
  return (
    <div className="flex items-center gap-3 px-2">
      <div className="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
        <span className="font-serif text-xl font-semibold">C</span>
      </div>
      <div className="min-w-0">
        <p className="truncate text-sm font-semibold tracking-tight">Conexión Bíblica</p>
        <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">Entrenamiento 2026</p>
      </div>
    </div>
  )
}

function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const isDark = theme === "dark" || (theme === "system" && document.documentElement.classList.contains("dark"))
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button aria-label="Cambiar tema" size="icon" variant="ghost" onClick={() => setTheme(isDark ? "light" : "dark")}>
          {isDark ? <Sun data-icon="inline-start" /> : <Moon data-icon="inline-start" />}
        </Button>
      </TooltipTrigger>
      <TooltipContent>{isDark ? "Modo claro" : "Modo oscuro"}</TooltipContent>
    </Tooltip>
  )
}

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const { nav, setNav, statistics, bankSelection, setBankSelection } = useApp()
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between px-1 pb-8">
        <Brand />
        {onNavigate ? <Button aria-label="Cerrar navegación" className="md:hidden" size="icon" variant="ghost" onClick={onNavigate}><X data-icon="inline-start" /></Button> : null}
      </div>
      <nav aria-label="Navegación principal" className="flex flex-1 flex-col gap-1">
        {navItems.map(({ key, label, icon: Icon }) => {
          const active = nav === key
          return (
            <Button
              key={key}
              aria-current={active ? "page" : undefined}
              className="justify-start gap-3 px-3"
              variant={active ? "secondary" : "ghost"}
              onClick={() => { setNav(key); onNavigate?.() }}
            >
              <Icon data-icon="inline-start" />
              <span>{label}</span>
              {key === "review" && statistics.general.difficult > 0 ? <span className="ml-auto rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">{statistics.general.difficult}</span> : null}
            </Button>
          )
        })}
      </nav>
      <label className="mt-5 flex flex-col gap-2 text-xs font-semibold text-muted-foreground">
        Vista de banco
        <select
          className="h-9 rounded-md border bg-background px-2 text-sm font-medium text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          value={bankSelection}
          onChange={(event) => setBankSelection(event.target.value as typeof bankSelection)}
        >
          <option value="curated-v4">V4 — cobertura amplia</option>
          <option value="prep-v3">V3 — Preparación intensiva de 4 días</option>
          <option value="legacy-v1">V1 — Clásica</option>
          <option value="mixed">Mixto curado</option>
          <option value="master-v2">V2 — Fuente técnica</option>
        </select>
      </label>
      <Separator className="my-5" />
      <div className="flex items-center justify-between gap-2 rounded-xl border bg-card px-3 py-2">
        <div className="flex min-w-0 items-center gap-2">
          <span className="size-2 rounded-full bg-emerald-500" aria-hidden="true" />
          <span className="truncate text-xs font-medium text-muted-foreground">Guardado local</span>
        </div>
        <ThemeToggle />
      </div>
    </div>
  )
}

export function AppShell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false)
  return (
    <TooltipProvider delayDuration={200}>
      <div className="min-h-screen bg-background text-foreground">
        <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r bg-card/80 px-4 py-6 backdrop-blur md:block">
          <SidebarContent />
        </aside>
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b bg-background/95 px-4 backdrop-blur md:hidden">
          <div className="flex items-center gap-3"><Sheet open={open} onOpenChange={setOpen}><SheetTrigger asChild><Button aria-label="Abrir navegación" size="icon" variant="outline"><Menu data-icon="inline-start" /></Button></SheetTrigger><SheetContent side="left" className="w-80 p-6"><SheetTitle className="sr-only">Navegación principal</SheetTitle><SidebarContent onNavigate={() => setOpen(false)} /></SheetContent></Sheet><Brand /></div>
          <ThemeToggle />
        </header>
        <main className="min-h-screen md:pl-64">
          <div className="mx-auto max-w-[1480px] px-4 py-6 sm:px-6 lg:px-10 lg:py-9">{children}</div>
        </main>
      </div>
    </TooltipProvider>
  )
}

export function QuickStartButton() {
  const { setNav } = useApp()
  return <Button onClick={() => setNav("practice")}><BookOpen data-icon="inline-start" />Empezar una ronda</Button>
}

export function ImportShortcut() {
  const { setNav } = useApp()
  return <Button variant="outline" onClick={() => setNav("banks")}><Upload data-icon="inline-start" />Importar banco</Button>
}

export function MobilePanelButton() {
  return <PanelLeft data-icon="inline-start" />
}
