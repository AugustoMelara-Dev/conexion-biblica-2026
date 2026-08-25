import { AlertTriangle, BookOpenCheck, Check, Layers3, LibraryBig, Sparkles } from "lucide-react"
import type { BankSelection } from "@/domain/types"

export function BankSelector({ value, onChange, legacyCount, masterCount, prepCount, curatedCount }: {
  value: BankSelection
  onChange: (selection: BankSelection) => void
  legacyCount: number
  masterCount: number
  prepCount: number
  curatedCount: number
}) {
  const options: { id: BankSelection; label: string; description: string; count: number; icon: typeof LibraryBig; recommended?: boolean; technical?: boolean }[] = [
    { id: "curated-v4", label: "V4 — Banco Curado", description: "Recomendado para cobertura amplia", count: curatedCount, icon: Sparkles, recommended: true },
    { id: "prep-v3", label: "V3 — Preparación intensiva de 4 días", description: "Ruta guiada y práctica concentrada", count: prepCount, icon: BookOpenCheck },
    { id: "legacy-v1", label: "V1 — Clásica", description: "Mi banco original", count: legacyCount, icon: LibraryBig },
    { id: "mixed", label: "Mixto curado", description: "V1 + V3 + V4", count: legacyCount + prepCount + curatedCount, icon: Layers3 },
    { id: "master-v2", label: "V2 — Fuente técnica", description: "puede contener redacción de auditoría", count: masterCount, icon: Sparkles, technical: true },
  ]
  return <div role="radiogroup" aria-label="Versión del banco" className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
    {options.map(({ id, label, description, count, icon: Icon, recommended, technical }) => {
      const checked = value === id
      const technicalWarningId = `${id}-technical-warning`
      return <label key={id} className={`relative flex cursor-pointer gap-4 rounded-xl border p-4 transition-colors focus-within:ring-2 focus-within:ring-ring ${checked ? "border-primary bg-primary/5" : "bg-card hover:bg-muted/40"}`}>
        <input className="sr-only" type="radio" name="bank-selection" value={id} checked={checked} onChange={() => onChange(id)} aria-label={`${label}: ${description}`} aria-describedby={technical ? technicalWarningId : undefined} />
        <span className={`flex size-10 shrink-0 items-center justify-center rounded-xl ${checked ? "bg-primary text-primary-foreground" : "bg-secondary text-primary"}`}><Icon className="size-5" /></span>
        <span className="min-w-0 flex-1"><span className="flex flex-wrap items-center gap-2"><span className="font-semibold">{label}</span>{recommended ? <span className="rounded-full bg-secondary px-2 py-0.5 text-[10px] font-semibold text-primary">Recomendado</span> : null}</span><span className="mt-1 block text-sm text-muted-foreground">{description}</span>{technical ? <span id={technicalWarningId} className="mt-2 flex items-start gap-1 text-xs font-medium text-amber-700 dark:text-amber-300"><AlertTriangle className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" /><span>Advertencia técnica: conserva el texto original.</span></span> : null}<span className="mt-2 block text-xs font-medium text-muted-foreground">{count.toLocaleString("es-HN")} preguntas</span></span>
        {checked ? <Check className="size-5 shrink-0 text-primary" aria-hidden="true" /> : null}
      </label>
    })}
  </div>
}
