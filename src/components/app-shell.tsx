import { useEffect, useState } from "react"
import {
  BookOpen,
  ChartNoAxesColumn,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Database,
  History,
  LayoutDashboard,
  Moon,
  PanelLeft,
  Sun,
  Upload,
  X,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Separator } from "@/components/ui/separator"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { useTheme } from "@/components/theme-provider"
import type { ReactNode } from "react"
import { cn } from "@/lib/utils"
import { useApp } from "@/app/app-state"

type NavKey =
  "dashboard" | "banks" | "practice" | "stats" | "history" | "review"

const navItems: { key: NavKey; label: string; icon: typeof LayoutDashboard }[] =
  [
    { key: "dashboard", label: "Resumen", icon: LayoutDashboard },
    { key: "practice", label: "Practicar", icon: BookOpen },
    { key: "banks", label: "Banco de preguntas", icon: Database },
    { key: "stats", label: "Estadísticas", icon: ChartNoAxesColumn },
    { key: "history", label: "Historial", icon: History },
    { key: "review", label: "Revisar preguntas", icon: ClipboardList },
  ]

const mobilePrimaryItems = navItems.filter(({ key }) =>
  ["dashboard", "practice", "stats"].includes(key)
)

const mobileMoreItems: {
  key: NavKey
  label: string
  icon: typeof LayoutDashboard
}[] = [
  { key: "banks", label: "Bancos", icon: Database },
  { key: "history", label: "Historial", icon: History },
  { key: "review", label: "Revisión", icon: ClipboardList },
]

const NAVIGATION_STORAGE_KEY = "conexion-biblica-navigation-collapsed"

function Brand({ collapsed = false }: { collapsed?: boolean }) {
  return (
    <div className="flex items-center gap-3 px-2">
      <div className="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
        <span className="font-serif text-xl font-semibold">C</span>
      </div>
      <div className={cn("min-w-0", collapsed && "sr-only")}>
        <p className="truncate text-sm font-semibold tracking-tight">
          Conexión Bíblica
        </p>
        <p className="text-[11px] font-medium tracking-[0.18em] text-muted-foreground uppercase">
          Entrenamiento 2026
        </p>
      </div>
    </div>
  )
}

function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const isDark =
    theme === "dark" ||
    (theme === "system" && document.documentElement.classList.contains("dark"))
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          aria-label="Cambiar tema"
          size="icon"
          variant="ghost"
          onClick={() => setTheme(isDark ? "light" : "dark")}
        >
          {isDark ? (
            <Sun data-icon="inline-start" />
          ) : (
            <Moon data-icon="inline-start" />
          )}
        </Button>
      </TooltipTrigger>
      <TooltipContent>{isDark ? "Modo claro" : "Modo oscuro"}</TooltipContent>
    </Tooltip>
  )
}

function NavigationButton({
  item,
  active,
  collapsed,
  onClick,
}: {
  item: (typeof navItems)[number]
  active: boolean
  collapsed: boolean
  onClick: () => void
}) {
  const { label, icon: Icon } = item
  const button = (
    <Button
      aria-current={active ? "page" : undefined}
      aria-label={collapsed ? label : undefined}
      className={cn(
        "min-h-11 gap-3",
        collapsed ? "w-full justify-center px-0" : "justify-start px-3"
      )}
      variant={active ? "secondary" : "ghost"}
      onClick={onClick}
    >
      <Icon aria-hidden="true" data-icon="inline-start" />
      <span className={collapsed ? "sr-only" : undefined}>{label}</span>
    </Button>
  )

  return collapsed ? (
    <Tooltip>
      <TooltipTrigger asChild>{button}</TooltipTrigger>
      <TooltipContent side="right">{label}</TooltipContent>
    </Tooltip>
  ) : (
    button
  )
}

function SidebarContent({
  collapsed,
  onNavigate,
  onToggle,
}: {
  collapsed: boolean
  onNavigate?: () => void
  onToggle?: () => void
}) {
  const { nav, setNav, statistics } = useApp()
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between px-1 pb-8">
        <Brand collapsed={collapsed} />
        {onToggle ? (
          <Button
            aria-label={
              collapsed ? "Expandir navegación" : "Contraer navegación"
            }
            size="icon"
            variant="ghost"
            onClick={onToggle}
          >
            {collapsed ? (
              <ChevronRight aria-hidden="true" />
            ) : (
              <ChevronLeft aria-hidden="true" />
            )}
          </Button>
        ) : null}
        {onNavigate ? (
          <Button
            aria-label="Cerrar navegación"
            size="icon"
            variant="ghost"
            onClick={onNavigate}
          >
            <X aria-hidden="true" />
          </Button>
        ) : null}
      </div>
      <nav
        aria-label="Navegación principal"
        className="flex flex-1 flex-col gap-1"
      >
        {navItems.map((item) => {
          const { key } = item
          const active = nav === key
          return (
            <div
              key={key}
              className={cn("relative", collapsed && "flex justify-center")}
            >
              <NavigationButton
                active={active}
                collapsed={collapsed}
                item={item}
                onClick={() => {
                  setNav(key)
                  onNavigate?.()
                }}
              />
              {key === "review" && statistics.general.difficult > 0 ? (
                <span
                  className={cn(
                    "rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground",
                    collapsed
                      ? "absolute -top-1 right-0"
                      : "absolute top-1/2 right-2 -translate-y-1/2"
                  )}
                >
                  {statistics.general.difficult}
                </span>
              ) : null}
            </div>
          )
        })}
      </nav>
      <Separator className="my-5" />
      <div
        className={cn(
          "flex items-center gap-2 rounded-xl border bg-card px-3 py-2",
          collapsed ? "justify-center" : "justify-between"
        )}
      >
        <div
          className={cn(
            "flex min-w-0 items-center gap-2",
            collapsed && "sr-only"
          )}
        >
          <span
            className="size-2 rounded-full bg-emerald-500"
            aria-hidden="true"
          />
          <span className="truncate text-xs font-medium text-muted-foreground">
            Guardado local
          </span>
        </div>
        <ThemeToggle />
      </div>
    </div>
  )
}

export function AppShell({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(() => {
    if (typeof window === "undefined") return false
    return window.localStorage.getItem(NAVIGATION_STORAGE_KEY) === "true"
  })

  useEffect(() => {
    window.localStorage.setItem(NAVIGATION_STORAGE_KEY, String(collapsed))
  }, [collapsed])

  const { nav, setNav } = useApp()

  return (
    <TooltipProvider delayDuration={200}>
      <div className="min-h-screen bg-background text-foreground">
        <a
          className="sr-only fixed top-4 left-4 z-50 rounded-md bg-primary px-4 py-2 text-primary-foreground focus:not-sr-only focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
          href="#main-content"
        >
          Saltar al contenido
        </a>
        <aside
          className={cn(
            "fixed inset-y-0 left-0 z-30 hidden border-r bg-card/80 px-3 py-6 backdrop-blur transition-[width] motion-reduce:transition-none lg:block",
            collapsed ? "w-20" : "w-56"
          )}
          data-collapsed={collapsed}
        >
          <SidebarContent
            collapsed={collapsed}
            onToggle={() => setCollapsed((current) => !current)}
          />
        </aside>
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b bg-background/95 px-4 backdrop-blur lg:hidden">
          <Brand />
          <ThemeToggle />
        </header>
        <main
          id="main-content"
          className={cn(
            "min-h-screen pb-24 lg:pb-0",
            collapsed ? "lg:pl-20" : "lg:pl-56"
          )}
        >
          <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-10 lg:py-9">
            {children}
          </div>
        </main>
        <nav
          aria-label="Navegación móvil"
          className="fixed inset-x-0 bottom-0 z-30 flex items-center justify-around border-t bg-background/95 px-2 py-2 backdrop-blur lg:hidden"
        >
          {mobilePrimaryItems.map(({ key, label, icon: Icon }) => {
            const active = nav === key
            const mobileLabel =
              key === "dashboard"
                ? "Inicio"
                : key === "stats"
                  ? "Progreso"
                  : label
            return (
              <Button
                key={key}
                aria-current={active ? "page" : undefined}
                className="min-h-11 flex-1 flex-col gap-1 px-1 text-xs"
                variant={active ? "secondary" : "ghost"}
                onClick={() => setNav(key)}
              >
                <Icon aria-hidden="true" className="size-4" />
                <span>{mobileLabel}</span>
              </Button>
            )
          })}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                aria-label="Más"
                className="min-h-11 flex-1 flex-col gap-1 px-1 text-xs"
                variant="ghost"
              >
                <PanelLeft aria-hidden="true" className="size-4" />
                <span>Más</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" side="top">
              {mobileMoreItems.map(({ key, label, icon: Icon }) => (
                <DropdownMenuItem key={key} onSelect={() => setNav(key)}>
                  <Icon aria-hidden="true" />
                  {label}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </nav>
      </div>
    </TooltipProvider>
  )
}

export function QuickStartButton() {
  const { setNav } = useApp()
  return (
    <Button onClick={() => setNav("practice")}>
      <BookOpen data-icon="inline-start" />
      Empezar una ronda
    </Button>
  )
}

export function ImportShortcut() {
  const { setNav } = useApp()
  return (
    <Button variant="outline" onClick={() => setNav("banks")}>
      <Upload data-icon="inline-start" />
      Importar banco
    </Button>
  )
}

export function MobilePanelButton() {
  return <PanelLeft data-icon="inline-start" />
}
