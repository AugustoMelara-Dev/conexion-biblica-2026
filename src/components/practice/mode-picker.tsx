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
      className="grid gap-3 sm:grid-cols-3"
    >
      {modes.map(({ mode, label, description, icon: Icon }) => {
        const selected = mode === value
        return (
          <button
            key={mode}
            type="button"
            aria-pressed={selected}
            className={`min-h-40 rounded-xl border p-4 text-left transition-colors motion-reduce:transition-none ${
              selected
                ? "border-primary bg-primary/5"
                : "bg-card hover:bg-muted/40"
            }`}
            onClick={() => onChange(mode)}
          >
            <span className="flex items-start justify-between gap-2">
              <span
                className={`flex size-10 shrink-0 items-center justify-center rounded-lg ${
                  selected
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-primary"
                }`}
              >
                <Icon aria-hidden="true" />
              </span>
              {selected ? (
                <Check className="text-primary" aria-label="Seleccionado" />
              ) : null}
            </span>
            <span className="mt-5 block text-sm font-semibold">{label}</span>
            <span className="mt-1 block text-xs leading-5 text-muted-foreground">
              {description}
            </span>
          </button>
        )
      })}
    </section>
  )
}
