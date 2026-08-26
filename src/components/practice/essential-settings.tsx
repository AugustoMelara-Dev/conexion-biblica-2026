import { useEffect, useState } from "react"
import type { BankSelection, SessionConfig, SourceWork } from "@/domain/types"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const bankOptions: { value: BankSelection; label: string }[] = [
  { value: "curated-v4", label: "V4 — cobertura amplia" },
  { value: "prep-v3", label: "V3 — Preparación intensiva de 4 días" },
  { value: "legacy-v1", label: "V1 — Clásica" },
  { value: "mixed", label: "Mixto curado" },
  { value: "master-v2", label: "V2 — Fuente técnica" },
]

const countOptions = [10, 25, 50, 100]

export function EssentialSettings({
  bankSelection,
  count,
  sourceWorks,
  onBankChange,
  onCountChange,
  onSourceWorksChange,
  maxCount,
}: {
  bankSelection: BankSelection
  count: SessionConfig["count"]
  sourceWorks: SourceWork[]
  onBankChange: (value: BankSelection) => void
  onCountChange: (value: SessionConfig["count"]) => void
  onSourceWorksChange: (value: SourceWork[]) => void
  maxCount?: number
}) {
  const isCustom = typeof count === "number" && !countOptions.includes(count)
  const [customCount, setCustomCount] = useState(() => (isCustom ? count : 30))

  useEffect(() => {
    if (isCustom) setCustomCount(count)
  }, [count, isCustom])

  const toggleSource = (source: SourceWork) => {
    onSourceWorksChange(
      sourceWorks.includes(source)
        ? sourceWorks.filter((item) => item !== source)
        : [...sourceWorks, source]
    )
  }

  return (
    <Card className="shadow-none">
      <CardHeader>
        <CardTitle>Ajustes esenciales</CardTitle>
        <CardDescription>
          Elige el banco, el alcance y el tamaño de la ronda.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-5">
        <label className="grid gap-2 text-sm font-medium">
          Banco de preguntas
          <select
            aria-label="Banco de preguntas"
            className="min-h-11 w-full rounded-md border bg-background px-3 text-sm font-medium focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
            value={bankSelection}
            onChange={(event) =>
              onBankChange(event.target.value as BankSelection)
            }
          >
            {bankOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <div className="grid gap-3 sm:grid-cols-2">
          {(["Daniel", "Profetas y Reyes"] as SourceWork[]).map((source) => {
            const checked = sourceWorks.includes(source)
            return (
              <label
                key={source}
                className="flex min-h-12 cursor-pointer items-center justify-between gap-3 rounded-lg border px-3 py-3 transition-colors hover:bg-muted/40"
              >
                <span className="flex items-center gap-3">
                  <Checkbox
                    checked={checked}
                    onCheckedChange={() => toggleSource(source)}
                  />
                  <span className="text-sm font-medium">{source}</span>
                </span>
                <Badge variant="secondary">Fuente</Badge>
              </label>
            )
          })}
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="grid gap-2 text-sm font-medium">
            Cantidad
            <Select
              value={isCustom ? "custom" : String(count)}
              onValueChange={(value) =>
                onCountChange(
                  value === "all"
                    ? "all"
                    : value === "custom"
                      ? customCount
                      : Number(value)
                )
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {countOptions.map((option) => (
                    <SelectItem key={option} value={String(option)}>
                      {option} preguntas
                    </SelectItem>
                  ))}
                  <SelectItem value="custom">Personalizada</SelectItem>
                  <SelectItem value="all">
                    Todas{maxCount === undefined ? "" : ` (${maxCount})`}
                  </SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
          </label>
          {isCustom ? (
            <label className="grid gap-2 text-sm font-medium">
              Cantidad personalizada
              <Input
                type="number"
                min={1}
                max={maxCount || 1}
                value={customCount}
                onChange={(event) => {
                  const next = Math.max(1, Number(event.target.value))
                  setCustomCount(next)
                  onCountChange(next)
                }}
              />
            </label>
          ) : null}
        </div>
      </CardContent>
    </Card>
  )
}
