import type { LucideIcon } from "lucide-react"
import type { ReactNode } from "react"

type MetricItem = {
  label: string
  value: ReactNode
  detail?: string
  icon?: LucideIcon
}

type MetricStripProps = {
  items: MetricItem[]
}

export function MetricStrip({ items }: MetricStripProps) {
  return (
    <ul className="grid gap-px overflow-hidden rounded-xl border border-border/70 bg-border/70 sm:grid-cols-2 lg:grid-cols-4">
      {items.map(({ label, value, detail, icon: Icon }) => (
        <li key={label} className="min-w-0 bg-card p-5">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            {Icon ? <Icon aria-hidden="true" className="size-4" /> : null}
            <span>{label}</span>
          </div>
          <p
            data-slot="metric-value"
            className="mt-2 text-2xl font-semibold tracking-[-0.025em]"
          >
            {value}
          </p>
          {detail ? (
            <p className="mt-1 text-sm text-muted-foreground">{detail}</p>
          ) : null}
        </li>
      ))}
    </ul>
  )
}
