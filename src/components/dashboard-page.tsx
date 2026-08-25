import { ArrowRight, BarChart3, BookOpenCheck, Check, Clock3, Flame, Gauge, RotateCcw, Target } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useApp } from "@/app/app-state"
import { QuickStartButton, ImportShortcut } from "@/components/app-shell"
import { formatElapsedMs } from "@/lib/format"
import { StatCard } from "@/components/stat-card"
import { BankSelector } from "@/components/bank-selector"
import type { BankSelection } from "@/domain/types"

const activeBankLabels: Record<BankSelection, string> = {
  "curated-v4": "V4 — cobertura amplia",
  "prep-v3": "V3 — Preparación intensiva de 4 días",
  "legacy-v1": "V1 — Clásica",
  mixed: "Mixto curado",
  "master-v2": "V2 — Fuente técnica",
}

export function DashboardPage() {
  const { statistics, banks, questions, sessions, progress, setNav, bankSelection, setBankSelection, bankCounts } = useApp()
  const { general } = statistics
  const daniel = statistics.sources.find((item) => item.key === "Daniel")
  const prophets = statistics.sources.find((item) => item.key === "Profetas y Reyes")
  const coverage = questions.length ? Math.round((general.seen / questions.length) * 100) : 0
  const hasProgress = general.total > 0
  const currentStreak = progress.size ? Math.max(...[...progress.values()].map((item) => item.currentCorrectStreak), 0) : 0
  const activeBankLabel = activeBankLabels[bankSelection]
  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
        <div className="max-w-2xl">
          <p className="text-sm font-medium text-muted-foreground">Preparación para Conexión Bíblica 2026</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">Entrena con intención.</h1>
          <p className="mt-3 text-sm leading-6 text-muted-foreground sm:text-base">Precisión, velocidad y repetición en un solo lugar. Tu avance se guarda en este dispositivo.</p>
        </div>
        <div className="flex flex-wrap gap-2"><QuickStartButton /><ImportShortcut /></div>
      </section>

      <section aria-labelledby="bank-selection-title" className="flex flex-col gap-3">
        <div className="flex flex-wrap items-end justify-between gap-3"><div><h2 id="bank-selection-title" className="text-lg font-semibold">Elige tu versión</h2><p className="mt-1 text-sm text-muted-foreground">Cada pregunta conserva el progreso de su banco de origen.</p></div><Badge variant="outline">Perfil activo: {activeBankLabel}</Badge></div>
        <BankSelector value={bankSelection} onChange={setBankSelection} legacyCount={bankCounts.legacy} masterCount={bankCounts.master} prepCount={bankCounts.prep} curatedCount={bankCounts.curated} />
      </section>

      <section aria-label="Métricas generales" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Precisión general" value={`${general.accuracy}%`} detail={`${general.correct} correctas de ${general.total}`} icon={Target} />
        <StatCard label="Preguntas respondidas" value={general.total} detail={`${general.seen} apariciones registradas`} icon={BookOpenCheck} />
        <StatCard label="Tiempo promedio" value={formatElapsedMs(general.averageResponseTimeMs)} detail={`Mejor ${formatElapsedMs(general.bestResponseTimeMs)}`} icon={Clock3} />
        <StatCard label="Racha actual" value={hasProgress ? currentStreak : "0"} detail={`${sessions.length} sesiones realizadas`} icon={Flame} />
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.4fr_0.9fr]">
        <Card className="shadow-none">
          <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
            <div><CardTitle>Rendimiento por fuente</CardTitle><CardDescription>La foto actual de tu preparación.</CardDescription></div>
            <Button variant="ghost" size="sm" onClick={() => setNav("stats")}>Ver detalle <ArrowRight data-icon="inline-end" /></Button>
          </CardHeader>
          <CardContent className="grid gap-5 sm:grid-cols-2">
            <SourceMetric label="Daniel" metric={daniel} accent="bg-primary" />
            <SourceMetric label="Profetas y Reyes" metric={prophets} accent="bg-chart-2" />
          </CardContent>
        </Card>
        <Card className="shadow-none">
          <CardHeader><CardTitle>Cobertura del banco</CardTitle><CardDescription>Preguntas que ya has visto.</CardDescription></CardHeader>
          <CardContent className="flex items-center gap-5"><div className="relative flex size-24 shrink-0 items-center justify-center rounded-full border-[10px] border-secondary"><div className="absolute inset-0 rounded-full border-[10px] border-primary [clip-path:inset(0_0_0_50%)]" /><span className="relative text-xl font-semibold">{coverage}%</span></div><div className="min-w-0"><p className="text-sm font-medium">{general.unseen} preguntas nuevas</p><p className="mt-1 text-xs leading-5 text-muted-foreground">{general.mastered} dominadas · {general.difficult} difíciles</p><Button className="mt-3" size="sm" variant="outline" onClick={() => setNav("practice")}>Practicar nuevas</Button></div></CardContent>
        </Card>
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.55fr_0.85fr]">
        <Card className="shadow-none">
          <CardHeader><CardTitle>Rendimiento por capítulo</CardTitle><CardDescription>Ordenado de peor a mejor precisión.</CardDescription></CardHeader>
          <CardContent className="p-0"><div className="overflow-x-auto"><Table><TableHeader><TableRow><TableHead>Capítulo</TableHead><TableHead>Respondidas</TableHead><TableHead>Precisión</TableHead><TableHead>Tiempo medio</TableHead><TableHead>Dominio</TableHead></TableRow></TableHeader><TableBody>{statistics.chapters.slice(0, 8).map((row) => <TableRow key={row.key}><TableCell className="font-medium">{row.label}</TableCell><TableCell>{row.total}</TableCell><TableCell><div className="flex items-center gap-2"><span>{row.accuracy}%</span><Progress className="w-20" value={row.accuracy} /></div></TableCell><TableCell>{formatElapsedMs(row.averageResponseTimeMs)}</TableCell><TableCell><Badge variant={row.mastery >= 4 ? "default" : "secondary"}>{row.mastery}/5</Badge></TableCell></TableRow>)}{statistics.chapters.length === 0 ? <TableRow><TableCell colSpan={5} className="h-24 text-center text-muted-foreground">Aún no hay capítulos con preguntas cargadas.</TableCell></TableRow> : null}</TableBody></Table></div></CardContent>
        </Card>
        <Card className="shadow-none">
          <CardHeader><CardTitle>Mis puntos débiles</CardTitle><CardDescription>Se actualizan después de cada respuesta.</CardDescription></CardHeader>
          <CardContent className="flex flex-col gap-4">
            <WeakLine icon={BarChart3} label="Capítulos a reforzar" value={statistics.weakChapters[0]?.label ?? "Todavía no hay datos"} detail={statistics.weakChapters[0] ? `${statistics.weakChapters[0].accuracy}% de precisión` : "Completa una ronda"} />
            <Separator />
            <WeakLine icon={Gauge} label="Tipo más débil" value={statistics.weakTypes[0]?.label ?? "Todavía no hay datos"} detail={statistics.weakTypes[0] ? `${statistics.weakTypes[0].accuracy}% de precisión` : "Completa una ronda"} />
            <Separator />
            <WeakLine icon={RotateCcw} label="Más falladas" value={`${statistics.mostFailed.length} preguntas detectadas`} detail="Repaso recomendado" />
            <Button className="mt-1 w-full" variant="outline" onClick={() => setNav("practice")}>Abrir práctica enfocada <ArrowRight data-icon="inline-end" /></Button>
          </CardContent>
        </Card>
      </section>

      <Card className="border-dashed bg-muted/30 shadow-none"><CardContent className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-medium">Tus datos están guardados localmente</p><p className="mt-1 text-sm text-muted-foreground">{banks.length} bancos · {questions.length} preguntas · sin sincronización externa.</p></div><div className="flex items-center gap-2 text-xs text-muted-foreground"><Check className="text-chart-2" aria-hidden="true" /> IndexedDB activo</div></CardContent></Card>
    </div>
  )
}

function SourceMetric({ label, metric, accent }: { label: string; metric?: { accuracy: number; total: number; correct: number; averageResponseTimeMs: number }; accent: string }) {
  return <div className="rounded-xl border bg-muted/20 p-4"><div className="flex items-center justify-between gap-3"><div className="flex items-center gap-2"><span className={`size-2.5 rounded-full ${accent}`} aria-hidden="true" /><span className="text-sm font-medium">{label}</span></div><span className="text-2xl font-semibold">{metric?.accuracy ?? 0}%</span></div><Progress className="mt-4" value={metric?.accuracy ?? 0} /><div className="mt-3 flex justify-between text-xs text-muted-foreground"><span>{metric?.correct ?? 0}/{metric?.total ?? 0} correctas</span><span>{formatElapsedMs(metric?.averageResponseTimeMs ?? 0)} medio</span></div></div>
}

function WeakLine({ icon: Icon, label, value, detail }: { icon: typeof BarChart3; label: string; value: string; detail: string }) {
  return <div className="flex items-start gap-3"><div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-secondary text-primary"><Icon /></div><div className="min-w-0"><p className="text-xs font-semibold uppercase tracking-[0.1em] text-muted-foreground">{label}</p><p className="mt-1 truncate text-sm font-medium">{value}</p><p className="mt-0.5 text-xs text-muted-foreground">{detail}</p></div></div>
}
