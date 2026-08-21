import { Check, Layers3, LibraryBig, Sparkles } from "lucide-react"
import type { BankSelection } from "@/domain/types"

export function BankSelector({ value, onChange, legacyCount, masterCount }: {
  value: BankSelection
  onChange: (selection: BankSelection) => void
  legacyCount: number
  masterCount: number
}) {
  const options: { id: BankSelection; label: string; description: string; count: number; icon: typeof LibraryBig; recommended?: boolean }[] = [
    { id: "legacy-v1", label: "V1 — Clásica", description: "Mi banco original", count: legacyCount, icon: LibraryBig },
    { id: "master-v2", label: "V2 — Banco Maestro", description: "Banco canónico 2026", count: masterCount, icon: Sparkles, recommended: true },
    { id: "mixed", label: "Mixto — V1 + V2", description: "Combina ambos bancos", count: legacyCount + masterCount, icon: Layers3 },
  ]
  return <div role="radiogroup" aria-label="Versión del banco" className="grid gap-3 lg:grid-cols-3">
    {options.map(({ id, label, description, count, icon: Icon, recommended }) => {
      const checked = value === id
      return <label key={id} className={`relative flex cursor-pointer gap-4 rounded-xl border p-4 transition-colors focus-within:ring-2 focus-within:ring-ring ${checked ? "border-primary bg-primary/5" : "bg-card hover:bg-muted/40"}`}>
        <input className="sr-only" type="radio" name="bank-selection" value={id} checked={checked} onChange={() => onChange(id)} aria-label={`${label}: ${description}`} />
        <span className={`flex size-10 shrink-0 items-center justify-center rounded-xl ${checked ? "bg-primary text-primary-foreground" : "bg-secondary text-primary"}`}><Icon className="size-5" /></span>
        <span className="min-w-0 flex-1"><span className="flex flex-wrap items-center gap-2"><span className="font-semibold">{label}</span>{recommended ? <span className="rounded-full bg-secondary px-2 py-0.5 text-[10px] font-semibold text-primary">Recomendado</span> : null}</span><span className="mt-1 block text-sm text-muted-foreground">{description}</span><span className="mt-2 block text-xs font-medium text-muted-foreground">{count.toLocaleString("es-HN")} preguntas</span></span>
        {checked ? <Check className="size-5 shrink-0 text-primary" aria-hidden="true" /> : null}
      </label>
    })}
  </div>
}
