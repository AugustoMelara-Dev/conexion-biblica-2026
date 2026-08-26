import { AlertTriangle, BookOpenCheck, Layers3, LibraryBig, Sparkles } from "lucide-react"
import type { BankSelection } from "@/domain/types"

type BankSelectorProps = {
  value: BankSelection
  onChange: (selection: BankSelection) => void
  legacyCount: number
  masterCount: number
  prepCount: number
  curatedCount: number
}

type BankOption = {
  id: BankSelection
  label: string
  description: string
  count: number
  icon: typeof LibraryBig
  recommended?: boolean
  technical?: boolean
}

export function BankSelector({
  value,
  onChange,
  legacyCount,
  masterCount,
  prepCount,
  curatedCount,
}: BankSelectorProps) {
  const options: BankOption[] = [
    {
      id: "curated-v4",
      label: "V4 — Banco Curado",
      description: "Recomendado para cobertura amplia.",
      count: curatedCount,
      icon: Sparkles,
      recommended: true,
    },
    {
      id: "prep-v3",
      label: "V3 — Preparación intensiva de 4 días",
      description: "Ruta guiada y práctica concentrada.",
      count: prepCount,
      icon: BookOpenCheck,
    },
    {
      id: "legacy-v1",
      label: "V1 — Clásica",
      description: "Mi banco original.",
      count: legacyCount,
      icon: LibraryBig,
    },
    {
      id: "mixed",
      label: "Mixto curado",
      description: "V1 + V3 + V4.",
      count: legacyCount + prepCount + curatedCount,
      icon: Layers3,
    },
    {
      id: "master-v2",
      label: "V2 — Fuente técnica",
      description: "Perfil técnico para consulta especializada.",
      count: masterCount,
      icon: Sparkles,
      technical: true,
    },
  ]
  const selected = options.find((option) => option.id === value) ?? options[0]

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(15rem,0.75fr)_minmax(0,1.25fr)]">
      <div className="hidden lg:block">
        <div role="radiogroup" aria-label="Versión del banco" className="grid gap-2">
          {options.map(({ id, label, icon: Icon }) => {
            const checked = id === selected.id
            return (
              <label
                key={id}
                className={`flex min-h-14 cursor-pointer items-center gap-3 rounded-xl px-4 py-3 transition-colors focus-within:ring-2 focus-within:ring-ring ${
                  checked ? "bg-secondary text-foreground" : "hover:bg-muted/60"
                }`}
              >
                <input
                  type="radio"
                  name="bank-selection"
                  value={id}
                  checked={checked}
                  onChange={() => onChange(id)}
                  className="size-4 accent-primary"
                />
                <Icon className="size-4 shrink-0 text-primary" aria-hidden="true" />
                <span className="min-w-0 text-sm font-medium">{label}</span>
                {id === selected.id && selected.recommended ? (
                  <span className="ml-auto text-xs font-medium text-primary">Recomendado</span>
                ) : null}
              </label>
            )
          })}
        </div>
      </div>

      <div className="lg:hidden">
        <label htmlFor="bank-selection-mobile" className="mb-2 block text-sm font-medium">
          Seleccionar versión del banco
        </label>
        <select
          id="bank-selection-mobile"
          value={selected.id}
          onChange={(event) => onChange(event.target.value as BankSelection)}
          className="min-h-11 w-full rounded-lg border border-input bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          {options.map((option) => (
            <option key={option.id} value={option.id}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <section aria-label="Detalle del banco seleccionado" className="min-w-0 rounded-2xl bg-secondary/55 p-6 sm:p-8">
        <p className="text-sm font-medium text-primary">
          {selected.recommended ? "Recomendado" : "Perfil disponible"}
        </p>
        <h3 className="mt-2 text-2xl font-semibold tracking-tight">{selected.label}</h3>
        <p className="mt-3 max-w-[52ch] text-muted-foreground">{selected.description}</p>
        <p className="mt-8 text-3xl font-semibold tabular-nums">
          {selected.count.toLocaleString("es-HN")} <span className="text-sm font-normal text-muted-foreground">preguntas</span>
        </p>
        {selected.technical ? (
          <p className="mt-5 flex items-start gap-2 text-sm text-amber-700 dark:text-amber-300">
            <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
            <span>Advertencia técnica: conserva el texto original.</span>
          </p>
        ) : null}
      </section>
    </div>
  )
}
