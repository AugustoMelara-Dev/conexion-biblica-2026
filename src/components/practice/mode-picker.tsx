import {
  BookOpen,
  Brain,
  Check,
  TimerReset,
  type LucideIcon,
} from "lucide-react"
import type { SessionMode } from "@/domain/types"

type ModeOption = {
  mode: SessionMode
  label: string
  description: string
  icon: LucideIcon
}

const modes: ModeOption[] = [
  {
    mode: "learn",
    label: "Aprender",
    description:
      "Feedback, explicación, referencia y pista. No afecta tu simulacro.",
    icon: BookOpen,
  },
  {
    mode: "smart-review",
    label: "Repaso inteligente",
    description: "Prioriza familias débiles y cambia la redacción.",
    icon: Brain,
  },
  {
    mode: "simulation",
    label: "Simulacro",
    description: "Tiempo y puntuación competitiva, separados de la práctica.",
    icon: TimerReset,
  },
]

export function getModeOption(mode: SessionMode) {
  return modes.find((item) => item.mode === mode) ?? modes[0]
}

export function ModePicker({
  value,
  onChange,
}: {
  value: SessionMode
  onChange: (mode: SessionMode) => void
}) {
  return (
    <section
      aria-label="Modo de práctica"
      className="rounded-2xl bg-secondary/55 p-2"
    >
      <div className="grid grid-cols-1 gap-1 sm:grid-cols-3">
        {modes.map(({ mode, label, icon: Icon }) => {
          const selected = mode === value
          return (
            <button
              key={mode}
              type="button"
              aria-pressed={selected}
              className={`flex min-h-14 items-center gap-3 rounded-xl px-3 py-2 text-left transition-all active:translate-y-px motion-reduce:transition-none ${
                selected
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-background/60 hover:text-foreground"
              }`}
              onClick={() => onChange(mode)}
            >
              <span className={`flex size-8 shrink-0 items-center justify-center rounded-lg ${selected ? "bg-primary text-primary-foreground" : "bg-muted text-primary"}`}>
                <Icon className="size-4" aria-hidden="true" />
              </span>
              <span className="min-w-0 flex-1 text-sm font-semibold">{label}</span>
              {selected ? <Check className="size-4 shrink-0 text-primary" aria-label="Seleccionado" /> : null}
            </button>
          )
        })}
      </div>
      <p className="px-3 pt-2 pb-1 text-xs leading-5 text-muted-foreground">
        {getModeOption(value).description}
      </p>
    </section>
  )
}
