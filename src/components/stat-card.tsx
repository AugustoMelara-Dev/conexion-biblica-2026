import type { LucideIcon } from "lucide-react"

export function StatCard({ label, value, detail, icon: Icon }: { label: string; value: string | number; detail?: string; icon: LucideIcon }) {
  return (
    <div className="flex min-w-0 items-start justify-between gap-4 border-l-2 border-primary/20 py-2 pl-4">
      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
        <p className="mt-2 truncate text-2xl font-semibold tracking-tight sm:text-3xl">{value}</p>
        {detail ? <p className="mt-1 truncate text-xs text-muted-foreground">{detail}</p> : null}
      </div>
      <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-secondary text-primary"><Icon aria-hidden="true" /></div>
    </div>
  )
}
