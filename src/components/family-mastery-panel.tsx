import { useMemo, useState } from "react"
import { buildFamilyInsights, type FamilyStatus } from "@/domain/family-insights"
import type { Question, QuestionProgress } from "@/domain/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

const labels: Record<FamilyStatus, string> = { weak: "Débil", pending: "Pendiente", learning: "En progreso", mastered: "Dominado" }

export function FamilyMasteryPanel({ questions, progress }: { questions: Question[]; progress: ReadonlyMap<string, QuestionProgress> }) {
  const [filter, setFilter] = useState<FamilyStatus | "all">("all")
  const rows = useMemo(() => buildFamilyInsights(questions, progress), [progress, questions])
  const visible = filter === "all" ? rows : rows.filter((row) => row.status === filter)
  const count = (status: FamilyStatus) => rows.filter((row) => row.status === status).length

  return <Card className="shadow-none"><CardHeader><CardTitle>Dominio por familia de conocimiento</CardTitle><CardDescription>Cada fila agrupa las variantes del mismo hecho. Dominar una frase no basta si quedan variantes pendientes.</CardDescription></CardHeader><CardContent className="flex flex-col gap-4"><div className="flex flex-wrap gap-2"><FilterButton active={filter === "all"} onClick={() => setFilter("all")}>Todas ({rows.length})</FilterButton>{(["weak", "pending", "learning", "mastered"] as FamilyStatus[]).map((status) => <FilterButton key={status} active={filter === status} onClick={() => setFilter(status)}>{labels[status]} ({count(status)})</FilterButton>)}</div><div className="overflow-x-auto rounded-lg border"><Table><TableHeader><TableRow><TableHead>Hecho</TableHead><TableHead>Estado</TableHead><TableHead>Variantes</TableHead><TableHead>Pendientes</TableHead><TableHead>Fallos</TableHead><TableHead>Dominio</TableHead></TableRow></TableHeader><TableBody>{visible.map((row) => <TableRow key={row.factKey}><TableCell className="min-w-72"><p className="line-clamp-2 font-medium">{row.label}</p><p className="mt-1 text-xs text-muted-foreground">{row.work} · cap. {row.chapter} · {row.factKey}</p></TableCell><TableCell><Badge variant={row.status === "weak" ? "destructive" : row.status === "mastered" ? "default" : "secondary"}>{labels[row.status]}</Badge></TableCell><TableCell>{row.seenVariants} / {row.variants}</TableCell><TableCell>{row.pendingVariants}</TableCell><TableCell>{row.incorrect}</TableCell><TableCell>{row.mastery} / 5</TableCell></TableRow>)}{visible.length === 0 ? <TableRow><TableCell colSpan={6} className="h-24 text-center text-muted-foreground">No hay familias en este estado.</TableCell></TableRow> : null}</TableBody></Table></div></CardContent></Card>
}

function FilterButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return <Button type="button" size="sm" variant={active ? "default" : "outline"} onClick={onClick}>{children}</Button>
}

