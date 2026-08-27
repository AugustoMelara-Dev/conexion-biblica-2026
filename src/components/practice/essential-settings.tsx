import { useEffect, useState } from "react"
import type { SessionConfig, SourceWork } from "@/domain/types"
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

const countOptions = [10, 25, 50, 100]

export function EssentialSettings({
  count,
  sourceWorks,
  onCountChange,
  onSourceWorksChange,
}: {
  count: SessionConfig["count"]
  sourceWorks: SourceWork[]
  onCountChange: (value: SessionConfig["count"]) => void
  onSourceWorksChange: (value: SourceWork[]) => void
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
          Elige el alcance y el tamaño de la ronda dentro del Banco Maestro Único.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-5">
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
                  <SelectItem value="all">Todas</SelectItem>
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
