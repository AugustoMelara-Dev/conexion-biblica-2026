import type { Question, QuestionProgress, SessionConfig } from '@/domain/types'

export type EmergencyModeId =
  | 'emergency-pr-intensive'
  | 'emergency-daniel-contrast'
  | 'emergency-daniel-maintenance'
  | 'emergency-personal-repair'
  | 'emergency-simulation-aah'
  | 'emergency-escudo-central'

export type EmergencyClassification =
  | 'COMPETITIVE_GOOD'
  | 'COVERAGE_GOOD'
  | 'EXCLUDE_EMERGENCY'

export function classifyEmergencyQuestion(q: Question): EmergencyClassification {
  const lengths = (q.options || []).map((o) => o.text.length)
  const minL = Math.min(...lengths)
  const maxL = Math.max(...lengths)
  const ratio = minL > 0 ? maxL / minL : 1

  const isCorrectLongest =
    q.correctAnswer &&
    q.options.find(
      (o) => q.correctAnswer.includes(o.id) || q.correctAnswer.includes(o.text)
    )?.text.length === maxL &&
    ratio > 2.8

  if (isCorrectLongest || !q.question || q.question.length < 15) {
    return 'EXCLUDE_EMERGENCY'
  }

  if (
    (q.difficultyBand === 'HARD' ||
      q.difficultyBand === 'EXPERT' ||
      q.difficulty >= 4) &&
    ratio <= 2.2
  ) {
    return 'COMPETITIVE_GOOD'
  }

  return 'COVERAGE_GOOD'
}

function pseudoRng(seed: number) {
  let s = seed >>> 0
  return () => {
    s = (Math.imul(s, 1103515245) + 12345) >>> 0
    return s / 0x100000000
  }
}

function shuffleWithRng<T>(arr: T[], seed: number): T[] {
  const copy = arr.slice()
  const rnd = pseudoRng(seed)
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(rnd() * (i + 1))
    ;[copy[i], copy[j]] = [copy[j], copy[i]]
  }
  return copy
}

export type EmergencySelectionResult = {
  success: boolean
  modeId: EmergencyModeId
  title: string
  description: string
  questions: Question[]
  config: SessionConfig
  realizedSummary: {
    total: number
    prCount: number
    danielCount: number
    scCount: number
    tfCount: number
    competitiveCount: number
    chapterCounts: Record<string, number>
  }
}

export function selectEmergencySession(
  pool: Question[],
  modeId: EmergencyModeId,
  progress: Map<string, QuestionProgress>,
  seed = Date.now()
): EmergencySelectionResult {
  const cleanPool = pool.filter(
    (q) => classifyEmergencyQuestion(q) !== 'EXCLUDE_EMERGENCY'
  )

  let selected: Question[] = []
  let title = ''
  let description = ''
  let perQuestionSeconds: number | null = null
  let totalSeconds: number | null = null
  let mode: SessionConfig['mode'] = 'learn'

  if (modeId === 'emergency-pr-intensive') {
    title = 'PR39–44 Intensivo'
    description =
      '150 preguntas: 25 por cada capítulo de Profetas y Reyes (39 al 44). Causas, secuencias y detalles exactos.'
    for (let c = 39; c <= 44; c++) {
      const chPool = cleanPool.filter(
        (q) => q.source.work === 'Profetas y Reyes' && q.source.chapter === c
      )
      const shuffled = shuffleWithRng(chPool, seed + c)
      const comp = shuffled.filter(
        (q) => classifyEmergencyQuestion(q) === 'COMPETITIVE_GOOD'
      )
      const cov = shuffled.filter(
        (q) => classifyEmergencyQuestion(q) === 'COVERAGE_GOOD'
      )
      const chSelected = [...comp.slice(0, 16), ...cov.slice(0, 9)].slice(0, 25)
      selected.push(...chSelected)
    }
  } else if (modeId === 'emergency-daniel-contrast') {
    title = 'Daniel 7–12 Contrastes'
    description =
      '150 preguntas: Enfoque profundo en Daniel 8, 9, 10, 12, con las visiones de Daniel 7 y el festín de Daniel 5.'
    const targets: Record<number, number> = {
      8: 30,
      9: 35,
      10: 25,
      12: 25,
      7: 20,
      5: 15,
    }
    for (const [chStr, count] of Object.entries(targets)) {
      const ch = Number(chStr)
      const chPool = cleanPool.filter(
        (q) => q.source.work === 'Daniel' && q.source.chapter === ch
      )
      const shuffled = shuffleWithRng(chPool, seed + ch)
      selected.push(...shuffled.slice(0, count))
    }
  } else if (modeId === 'emergency-daniel-maintenance') {
    title = 'Daniel 1–6 Mantenimiento'
    description =
      '50 preguntas: Repaso rápido de las narrativas históricas fundamentales (capítulos 1 al 6).'
    for (let c = 1; c <= 6; c++) {
      const count = c === 1 || c === 6 ? 9 : 8
      const chPool = cleanPool.filter(
        (q) => q.source.work === 'Daniel' && q.source.chapter === c
      )
      const shuffled = shuffleWithRng(chPool, seed + c)
      selected.push(...shuffled.slice(0, count))
    }
  } else if (modeId === 'emergency-personal-repair') {
    title = 'Reparar Errores y Dudas'
    description =
      'Preguntas falladas previamente, respuestas lentas (>6s) y dudas marcadas para reforzar puntos débiles.'
    mode = 'smart-review'

    // Find failed or slow questions
    const repairCandidates = cleanPool.filter((q) => {
      const p =
        progress.get(q.id) ??
        progress.get(`BANCO_UNICO_CONEXION_BIBLICA_2026:${q.id}`) ??
        progress.get(`local:${q.id}`)
      if (!p) return false
      return (
        p.timesIncorrect > 0 ||
        (p.lastResponseTimeMs !== null && p.lastResponseTimeMs > 6000) ||
        p.markedDifficult ||
        (p as any).doubted
      )
    })

    // If candidate set is small, supplement with critical historical error anchors
    const errorAnchors = cleanPool.filter((q) => {
      const txt = (
        q.question +
        ' ' +
        (q.source.reference || '')
      ).toLowerCase()
      return (
        txt.includes('9:26') ||
        txt.includes('sesenta y dos semanas') ||
        txt.includes('12:1') ||
        txt.includes('gran príncipe') ||
        txt.includes('tekel') ||
        txt.includes('ulai') ||
        txt.includes('hidekel')
      )
    })

    const combined = [...repairCandidates, ...errorAnchors]
    const uniqueMap = new Map<string, Question>()
    for (const q of combined) {
      if (!uniqueMap.has(q.id)) uniqueMap.set(q.id, q)
    }
    const shuffled = shuffleWithRng([...uniqueMap.values()], seed)
    selected = shuffled.slice(0, Math.min(50, shuffled.length))
  } else if (modeId === 'emergency-simulation-aah') {
    title = 'Simulación AAH (Oficial)'
    description =
      '100 preguntas bajo el patrón empírico del examen real: ~71 Daniel / ~29 PR, 77 Selección / 23 V-F, 20 segundos.'
    mode = 'simulation'
    perQuestionSeconds = 20
    totalSeconds = 2000

    const danPool = cleanPool.filter((q) => q.source.work === 'Daniel')
    const prPool = cleanPool.filter((q) => q.source.work === 'Profetas y Reyes')

    const danTF = shuffleWithRng(
      danPool.filter(
        (q) => q.type === 'true_false' || q.family === 'true_false'
      ),
      seed + 1
    ).slice(0, 16)
    const danSC = shuffleWithRng(
      danPool.filter(
        (q) => q.type !== 'true_false' && q.family !== 'true_false'
      ),
      seed + 2
    ).slice(0, 55)
    const prTF = shuffleWithRng(
      prPool.filter(
        (q) => q.type === 'true_false' || q.family === 'true_false'
      ),
      seed + 3
    ).slice(0, 7)
    const prSC = shuffleWithRng(
      prPool.filter(
        (q) => q.type !== 'true_false' && q.family !== 'true_false'
      ),
      seed + 4
    ).slice(0, 22)

    selected = shuffleWithRng([...danTF, ...danSC, ...prTF, ...prSC], seed)
  } else if (modeId === 'emergency-escudo-central') {
    title = 'Escudo Central'
    description =
      '100 preguntas de máxima discriminación (50 PR / 50 Daniel 7–12), 100% competitivas, sin pistas ni distractores absurdos.'
    mode = 'simulation'
    perQuestionSeconds = 25
    totalSeconds = 2500

    const compPR = cleanPool.filter(
      (q) =>
        q.source.work === 'Profetas y Reyes' &&
        classifyEmergencyQuestion(q) === 'COMPETITIVE_GOOD'
    )
    const compDan = cleanPool.filter(
      (q) =>
        q.source.work === 'Daniel' &&
        q.source.chapter >= 7 &&
        classifyEmergencyQuestion(q) === 'COMPETITIVE_GOOD'
    )

    const selPR = shuffleWithRng(compPR, seed + 10).slice(0, 50)
    const selDan = shuffleWithRng(compDan, seed + 20).slice(0, 50)

    selected = shuffleWithRng([...selPR, ...selDan], seed)
  }

  // Compute realized summary
  let prCount = 0
  let danielCount = 0
  let scCount = 0
  let tfCount = 0
  let competitiveCount = 0
  const chapterCounts: Record<string, number> = {}

  for (const q of selected) {
    if (q.source.work === 'Profetas y Reyes') prCount++
    else danielCount++

    if (q.type === 'true_false' || q.family === 'true_false') tfCount++
    else scCount++

    if (classifyEmergencyQuestion(q) === 'COMPETITIVE_GOOD') competitiveCount++

    const chKey = `${q.source.work === "Daniel" ? "DAN" : "PR"}${q.source.chapter}`
    chapterCounts[chKey] = (chapterCounts[chKey] ?? 0) + 1
  }

  const config: SessionConfig = {
    mode,
    count: selected.length,
    sourceWorks:
      prCount > 0 && danielCount > 0
        ? ['Daniel', 'Profetas y Reyes']
        : prCount > 0
          ? ['Profetas y Reyes']
          : ['Daniel'],
    chapters: Object.keys(chapterCounts).map((k) =>
      Number(k.replace(/^(DAN|PR)/, ''))
    ),
    difficulties: [1, 2, 3, 4, 5],
    types: ['single_choice', 'fill_blank', 'true_false'],
    statuses: ['all'],
    shuffleQuestions: true,
    shuffleOptions: true,
    perQuestionSeconds,
    totalSeconds,
    bankSelection: 'final-v7',
    strategy: 'adaptive',
    trainingPresetId: modeId,
    selectionOrigin: 'preset',
    massive: true,
  }

  return {
    success: true,
    modeId,
    title,
    description,
    questions: selected,
    config,
    realizedSummary: {
      total: selected.length,
      prCount,
      danielCount,
      scCount,
      tfCount,
      competitiveCount,
      chapterCounts,
    },
  }
}