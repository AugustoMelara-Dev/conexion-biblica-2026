import type { LucideIcon } from "lucide-react"
import type { ReactNode } from "react"

type EmptyStateProps = {
  title: string
  description: string
  action?: ReactNode
  icon?: LucideIcon
}

export function EmptyState({
  title,
  description,
  action,
  icon: Icon,
}: EmptyStateProps) {
  return (
    <section className="flex flex-col items-center rounded-xl border border-dashed border-border/70 px-6 py-12 text-center">
      {Icon ? (
        <Icon
          aria-hidden="true"
          className="mb-4 size-8 text-muted-foreground"
        />
      ) : null}
      <h2 className="text-lg font-semibold text-balance">{title}</h2>
      <p className="mt-2 max-w-md leading-6 text-pretty text-muted-foreground">
        {description}
      </p>
      {action ? <div className="mt-6 flex justify-center">{action}</div> : null}
    </section>
  )
}
