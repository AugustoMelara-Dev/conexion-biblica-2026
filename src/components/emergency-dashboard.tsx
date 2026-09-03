import { useMemo } from 'react'
import {
  ArrowRight,
  BookOpen,
  Clock3,
  Play,
  RotateCcw,
  Shield,
  Trophy,
  Zap,
} from 'lucide-react'
import { useApp } from '@/app/app-state'
import type { Question, SessionConfig } from '@/domain/types'
import {
  type EmergencyModeId,
  selectEmergencySession,
} from '@/domain/emergency-modes'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

interface EmergencyDashboardProps {
  onStartEmergencyMode: (config: SessionConfig, questions: Question[]) => void | Promise<void>
  onConfigureRound?: () => void
  onContinueRound?: () => void
}

export function EmergencyDashboard({
  onStartEmergencyMode,
  onConfigureRound,
  onContinueRound,
}: EmergencyDashboardProps) {
  const {
    activeRound,
    sessions = [],
    progress = new Map(),
    questions = [],
  } = useApp()

  // Compute pending repairs count
  const pendingRepairsCount = useMemo(() => {
    let count = 0
    progress.forEach((p) => {
      if (
        p.timesIncorrect > 0 ||
        (p.lastResponseTimeMs !== null && p.lastResponseTimeMs > 6000) ||
        p.markedDifficult ||
        Boolean((p as any).doubted)
      ) {
        count++
      }
    })
    return Math.max(count, 0)
  }, [progress])

  // Compute today metrics
  const todayMetrics = useMemo(() => {
    const d = new Date()
    d.setHours(0, 0, 0, 0)
    const startMs = d.getTime()

    let total = 0
    let correct = 0
    let times: number[] = []

    sessions.forEach((s) => {
      if (s.startedAt >= startMs) {
        s.answers.forEach((ans) => {
          total++
          if (ans.result.isCorrect) correct++
          times.push(ans.responseTimeMs)
        })
      }
    })

    const avgTimeSec =
      times.length > 0
        ? (times.reduce((a, b) => a + b, 0) / times.length / 1000).toFixed(1)
        : "0.0"
    const accuracy = total > 0 ? Math.round((correct / total) * 100) : 0

    return { total, correct, avgTimeSec, accuracy }
  }, [sessions])

  const handleStartMode = (modeId: EmergencyModeId) => {
    const modeSessionCount = sessions.filter(
      (s) => s.config.trainingPresetId === modeId
    ).length
    const seed = Date.now() + modeSessionCount * 1009
    const result = selectEmergencySession(questions, modeId, progress, seed)
    if (result.success) {
      onStartEmergencyMode(result.config, result.questions)
    }
  }

  return (
    <div className="space-y-6 pb-12">
      {/* HEADER */}
      <div className="rounded-2x bg-gradient-to-r from-amber-500/10 via-red-500/10 to-blue-500/10 border border-amber-500/20 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Badge variant="destructive" className="font-bold uppercase tracking-wider text-xs">
                Modo Emergencia Final 2026
              </Badge>
              <Badge variant="outline" className="text-xs text-muted-foreground">
                Sábado 5 de Septiembre
              </Badge>
            </div>
            <h2 className="mt-2 text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
              Entrenamiento de Alta Utilidad
            </h2>
            <p className="mt-1 text-sm text-muted-foreground max-w-2xl">
              Consola estratégica basada en la evidencia del examen real AAH (98/100, 3.72s).
              Cero dispersión: enfócate en los puntos determinantes para la victoria.
            </p>
          </div>

          <div className="flex items-center gap-4 bg-background/80 backdrop-blur rounded-x1 p-3 border">
            <div className="text-center px-2">
              <p className="text-xs text-muted-foreground">Completadas hoy</p>
              <p className="text-xl font-bold tabular-nums text-foreground">{todayMetrics.total}</p>
            </div>
            <div className="h-8 w-px bg-border" />
            <div className="text-center px-2">
              <p className="text-xs text-muted-foreground">Precisión</p>
              <p className="text-xl font-bold tabular-nums text-foreground">{todayMetrics.accuracy}%</p>
            </div>
            <div className="h-8 w-px bg-border" />
            <div className="text-center px-2">
              <p className="text-xs text-muted-foreground">Tiempo medio</p>
              <p className="text-xl font-bold tabular-nums text-foreground">{todayMetrics.avgTimeSec}s</p>
            </div>
          </div>
        </div>
      </div>

      {/* 7. CONTINUAR RONDA ACTIVA (Si existe) */}
      {activeRound ? (
        <Card className="border-2 border-primary/50 bg-primary/5 shadow-md">
          <CardContent className="p-5 flex flex-wrap items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-primary"></span>
                </span>
                <p className="font-bold text-base text-foreground">Ronda activa en curso</p>
                <Badge variant="secondary">
                  Pregunta {activeRound.currentIndex + 1} de {activeRound.questionKeys.length}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground">
                Tienes una sesión pausada con {activeRound.answers.length} respuestas registradas.
              </p>
            </div>
            <Button
              size="lg"
              className="font-bold gap-2 min-h-12 px-6"
              onClick={() => {
                if (onContinueRound) onContinueRound()
                else if (onConfigureRound) onConfigureRound()
              }}
            >
              <Play className="h-4 w-4 fill-current" />
              Continuar ronda
            </Button>
          </CardContent>
        </Card>
      ) : null}

      {/* BLOQUES PRINCIPALES DE ENTRENAMIENTO */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {/* BLOQUE 1: PR39-44 INTENSIVO */}
        <Card className="flex flex-col justify-between hover:border-primary/40 transition-colors shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between gap-2">
              <Badge className="bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30">
                150 Preguntas
              </Badge>
              <BookOpen className="h-5 w-5 text-amber-500" />
            </div>
            <CardTitle className="text-lg mt-2">1. PR39–44 Intensivo</CardTitle>
            <CardDescription className="text-xs leading-relaxed">
              Aprendizaje, cobertura y fijación de detalles. Exactamente 25 preguntas por cada capítulo (PR 39 al 44).
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Button
              className="w-full font-semibold min-h-11 justify-between"
              onClick={() => handleStartMode('emergency-pr-intensive')}
            >
              <span>Iniciar PR Intensivo</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* BLOQUE 2: DANIEL 7-12 CONTRASTES */}
        <Card className="flex flex-col justify-between hover:border-primary/40 transition-colors shadow-sm border-blue-500/20 bg-blue-500/5">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between gap-2">
              <Badge className="bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/30">
                150 Preguntas
              </Badge>
              <Zap className="h-5 w-5 text-blue-500" />
            </div>
            <CardTitle className="text-lg mt-2">2. Daniel 7–12 Contrastes</CardTitle>
            <CardDescription className="text-xs leading-relaxed">
              150 preguntas: Enfoque profundo en Daniel 7 al 12 (Dan 7: 20, Dan 8: 25, Dan 9: 30, Dan 10: 20, Dan 11: 30, Dan 12: 25). Cero Daniel 1–6.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Button
              className="w-full font-semibold min-h-11 justify-between bg-blue-600 hover:bg-blue-700 text-white"
              onClick={() => handleStartMode('emergency-daniel-contrast')}
            >
              <span>Iniciar Dan Contrastes</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* BLOQUE 3: DANIEL 1-6 MANTENIMIENTO */}
        <Card className="flex flex-col justify-between hover:border-primary/40 transition-colors shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between gap-2">
              <Badge variant="secondary">50 Preguntas</Badge>
              <Clock3 className="h-5 w-5 text-emerald-500" />
            </div>
            <CardTitle className="text-lg mt-2">3. Daniel 1–6 Mantenimiento</CardTitle>
            <CardDescription className="text-xs leading-relaxed">
              Mantenimiento a super velocidad de las historias fundamentales de Daniel 1 al 6:
              fidelidad, horno de fuego, árbol y foso de leones.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Button
              variant="outline"
              className="w-full font-semibold min-h-11 justify-between"
              onClick={() => handleStartMode('emergency-daniel-maintenance')}
            >
              <span>Iniciar Mantenimiento</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* BLOQUE 4: REPARAR ERRORES Y DUDAS */}
        <Card className="flex flex-col justify-between hover:border-primary/40 transition-colors shadow-sm border-amber-500/20">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between gap-2">
              <Badge variant={pendingRepairsCount > 0 ? 'destructive' : 'outline'}>
                {pendingRepairsCount} Pendientes
              </Badge>
              <RotateCcw className="h-5 w-5 text-amber-500" />
            </div>
            <CardTitle className="text-lg mt-2">4. Reparar Errores y Dudas</CardTitle>
            <CardDescription className="text-xs leading-relaxed">
              Revisa todas las preguntas falladas, respuestas lentas (&gt;6s) y dudas marcadas.
              Incluye los reactivos ancla de Dan 9:26 y 12:1.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Button
              variant="outline"
              className="w-full font-semibold min-h-11 justify-between border-amber-500/40 text-amber-600 dark:text-amber-400 hover:bg-amber-500/10"
              onClick={() => handleStartMode('emergency-personal-repair')}
            >
              <span>Reparar Debilidades</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* BLOQUE 5: SIMULACIÓN PATRÓN AAH 2026 */}
        <Card className="flex flex-col justify-between hover:border-primary/40 transition-colors shadow-sm border-purple-500/20 bg-purple-500/5">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between gap-2">
              <Badge className="bg-purple-500/15 text-purple-600 dark:text-purple-400 border-purple-500/30">
                100 Qs • 20s
              </Badge>
              <Trophy className="h-5 w-5 text-purple-500" />
            </div>
            <CardTitle className="text-lg mt-2">5. Simulación patrón AAH 2026</CardTitle>
            <CardDescription className="text-xs leading-relaxed">
              Reproduce la distribución observada en tu final de asociación. No predice la distribución de la final nacional. 71 Daniel / 29 PR, 77 Selección / 23 V-F, 20 segundos por pregunta.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Button
              className="w-full font-semibold min-h-11 justify-between bg-purple-600 hover:bg-purple-700 text-white"
              onClick={() => handleStartMode('emergency-simulation-aah')}
            >
              <span>Iniciar Simulación AAH</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* BLOQUE 6: SIMULACIÓN ADVERSARIAL */}
        <Card className="flex flex-col justify-between hover:border-primary/40 transition-colors shadow-sm border-red-500/20 bg-red-500/5">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between gap-2">
              <Badge className="bg-red-500/15 text-red-600 dark:text-red-400 border-red-500/30">
                100 Qs • Verificadas
              </Badge>
              <Shield className="h-5 w-5 text-red-500" />
            </div>
            <CardTitle className="text-lg mt-2">6. Simulación Adversarial</CardTitle>
            <CardDescription className="text-xs leading-relaxed">
              50 PR / 50 Daniel 7–12. 100 reactivos con tier COMPETITIVE_ACCEPT verificado y 100 hechos distintos: distractores plausibles, opciones homogéneas y máxima discriminación textual.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Button
              className="w-full font-semibold min-h-11 justify-between bg-red-600 hover:bg-red-700 text-white"
              onClick={() => handleStartMode('emergency-adversarial-simulation')}
            >
              <span>Iniciar Simulación Adversarial</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* CONFIGURACI×N MANUAL SECUMDARIA */}
      {onConfigureRound ? (
        <details className="rounded-xl border bg-muted/20 p-4 text-xs text-muted-foreground">
          <summary className="cursor-pointer font-medium text-foreground">
            Configuración de ronda manual avanzada
          </summary>
          <div className="mt-3 pt-3 border-t flex items-center justify-between gap-4">
            <p>
              Necesitas filtrar capítulos o tipos específicos manualmente? Abre el generador manual
              completo con inventario facetado.
            </p>
            <Button variant="outline" size="sm" onClick={onConfigureRound}>
              Abrir configurador
            </Button>
          </div>
        </details>
      ) : null}
    </div>
  )
}
