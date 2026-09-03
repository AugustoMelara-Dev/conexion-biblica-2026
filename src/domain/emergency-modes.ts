import type { Question, QuestionProgress, SessionConfig } from './types'
import { FINAL_FILTER_CATALOG } from '@/data/filter-catalog'

export type EmergencyCategory =
  | 'COMPETITIVE_GOOD'
  | 'COVERAGE_GOOD'
  | 'EXCLUDE_EMERGENCY'

export type EmergencyModeId =
  | 'emergency-pr-intensive'
  | 'emergency-daniel-contrast'
  | 'emergency-daniel-maintenance'
  | 'emergency-personal-repair'
  | 'emergency-simulation-aah'
  | 'emergency-adversarial-simulation'
  | 'emergency-escudo-central'

// Set of semantically verified competitive questions (tier COMPETITIVE_ACCEPT, non-provisional, non-blind)
export const VERIFIED_COMPETITIVE_IDS = new Set<string>(
  FINAL_FILTER_CATALOG
    .filter((item) => item.tier === 'COMPETITIVE_ACCEPT' && !item.provisional && !item.blind)
    .map((item) => item.id)
)

export function classifyEmergencyQuestion(q: Question): EmergencyCategory {
  const options = q.options ?? []
  if (options.length === 0) return 'EXCLUDE_EMERGENCY'

  const lens = options.map((o) => (o.text ?? '').trim().length)
  const maxL = Math.max(...lens)
  const minL = Math.min(...lens)
  const ratio = minL > 0 ? maxL / minL : 99

  // Exclude obvious length giveaway
  if (ratio > 2.2) return 'EXCLUDE_EMERGENCY'

  // Verified competitive tier check
  if (VERIFIED_COMPETITIVE_IDS.has(q.id)) {
    return 'COMPETITIVE_GOOD'
  }

  return 'COVERAGE_GOOD'
}

function pseudoRandom(seed: number): () => number {
  let s = seed % 2147483647
  if (s <= 0) s += 2147483646
  return () => {
    s = (s * 16807) % 2147483647
    return (s - 1) / 2147483646
  }
}

function shuffleWithRng<T>(items: T[], seed: number): T[] {
  const rng = pseudoRandom(seed)
  const copy = [...items]
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1))
    const temp = copy[i]
    copy[i] = copy[j]
    copy[j] = temp
  }
  return copy
}

function selectWithUniqueFacts(
  pool: Question[],
  targetCount: number,
  seed: number
): Question[] {
  const shuffled = shuffleWithRng(pool, seed)
  const selected: Question[] = []
  const usedFacts = new Set<string>()
  const leftovers: Question[] = []

  for (const q of shuffled) {
    const fid = q.factId ?? q.id
    if (!usedFacts.has(fid) && selected.length < targetCount) {
      usedFacts.add(fid)
      selected.push(q)
    } else {
      leftovers.push(q)
    }
  }

  while (selected.length < targetCount && leftovers.length > 0) {
    selected.push(leftovers.shift()!)
  }

  return selected
}

export interface EmergencySessionResult {
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
    coverageCount: number
    chapterCounts: Record<string, number>
    distinctFacts: number
  }
}

export function selectEmergencySession(
  allQuestions: Question[],
  modeId: EmergencyModeId,
  progress: Map<string, QuestionProgress>,
  seed: number = 20260905
): EmergencySessionResult {
  const cleanPool = allQuestions.filter(
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
      'Aprendizaje, cobertura y fijación de detalles. Exactamente 25 preguntas por cada capítulo (PR 39 al 44).'
    for (let c = 39; c <= 44; c++) {
      const chPool = cleanPool.filter(
        (q) => q.source.work === 'Profetas y Reyes' && q.source.chapter === c
      )
      const chSelected = selectWithUniqueFacts(chPool, 25, seed + c)
      selected.push(...chSelected)
    }
  } else if (modeId === 'emergency-daniel-contrast') {
    title = 'Daniel 7–12 Contrastes'
    description =
      '150 preguntas: Enfoque profundo en Daniel 7 al 12 (Dan 7: 20, Dan 8: 25, Dan 9: 30, Dan 10: 20, Dan 11: 30, Dan 12: 25). Cero Daniel 1–6.'
    const targets: Record<number, number> = {
      7: 20,
      8: 25,
      9: 30,
      10: 20,
      11: 30,
      12: 25,
    }
    for (const [chStr, count] of Object.entries(targets)) {
      const ch = Number(chStr)
      const chPool = cleanPool.filter(
        (q) => q.source.work === 'Daniel' && q.source.chapter === ch
      )
      const chSelected = selectWithUniqueFacts(chPool, count, seed + ch)
      selected.push(...chSelected)
    }
  } else if (modeId === 'emergency-daniel-maintenance') {
    title = 'Daniel 1–6 Mantenimiento'
    description =
      '50 preguntas: Repaso rápido de las narrativas fundamentales (capítulos 1 al 6).'
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
        Boolean((p as any).doubted)
      )
    })

    const dan926 = cleanPool.find(
      (q) =>
        q.source.work === 'Daniel' &&
        q.source.chapter === 9 &&
        Boolean(q.source.reference?.includes('9:26'))
    )
    const dan121 = cleanPool.find(
      (q) =>
        q.source.work === 'Daniel' &&
        q.source.chapter === 12 &&
        Boolean(q.source.reference?.includes('12:1'))
    )

    const uniqueMap = new Map<string, Question>()
    if (dan926) uniqueMap.set(dan926.id, dan926)
    if (dan121) uniqueMap.set(dan121.id, dan121)

    for (const q of repairCandidates) {
      if (!uniqueMap.has(q.id)) uniqueMap.set(q.id, q)
    }

    const shuffled = shuffleWithRng([...uniqueMap.values()], seed)
    selected = shuffled.slice(0, Math.min(50, shuffled.length))
  } else if (modeId === 'emergency-simulation-aah') {
    title = 'Simulación patrón AAH 2026'
    description =
      'Reproduce la distribución observada en tu final de asociación. No predice la distribución de la final nacional.'
    mode = 'simulation'
    perQuestionSeconds = 20
    totalSeconds = 2000

    const danPool = cleanPool.filter((q) => q.source.work === 'Daniel')
    const prPool = cleanPool.filter((q) => q.source.work === 'Profetas y Reyes')

    const usedFacts = new Set<string>()

    // Dan TF: 16
    const danTF: Question[] = []
    for (const q of shuffleWithRng(
      danPool.filter((q) => q.type === 'true_false' || q.family === 'true_false'),
      seed + 1
    )) {
      const fid = q.factId ?? q.id
      if (!usedFacts.has(fid) && danTF.length < 16) {
        usedFacts.add(fid)
        danTF.push(q)
      }
    }

    // Dan SC: 55
    const danSC: Question[] = []
    for (const q of shuffleWithRng(
      danPool.filter((q) => q.type !== 'true_false' && q.family !== 'true_false'),
      seed + 2
    )) {
      const fid = q.factId ?? q.id
      if (!usedFacts.has(fid) && danSC.length < 55) {
        usedFacts.add(fid)
        danSC.push(q)
      }
    }

    // PR TF: 7
    const prTF: Question[] = []
    for (const q of shuffleWithRng(
      prPool.filter((q) => q.type === 'true_false' || q.family === 'true_false'),
      seed + 3
    )) {
      const fid = q.factId ?? q.id
      if (!usedFacts.has(fid) && prTF.length < 7) {
        usedFacts.add(fid)
        prTF.push(q)
      }
    }

    // PR SC: 22
    const prSC: Question[] = []
    for (const q of shuffleWithRng(
      prPool.filter((q) => q.type !== 'true_false' && q.family !== 'true_false'),
      seed + 4
    )) {
      const fid = q.factId ?? q.id
      if (!usedFacts.has(fid) && prSC.length < 22) {
        usedFacts.add(fid)
        prSC.push(q)
      }
    }

    selected = shuffleWithRng([...danTF, ...danSC, ...prTF, ...prSC], seed)
  } else if (
    modeId === 'emergency-adversarial-simulation' ||
    modeId === 'emergency-escudo-central'
  ) {
    title = 'Simulación adversarial'
    description =
      '100 preguntas de máxima discriminación (50 PR / 50 Daniel 7–12) con tier COMPETITIVE_ACCEPT verificado y 100 hechos distintos.'
    mode = 'simulation'
    perQuestionSeconds = 25
    totalSeconds = 2500

    const compPR = cleanPool.filter(
      (q) =>
        q.source.work === 'Profetas y Reyes' &&
        q.source.chapter >= 39 &&
        q.source.chapter <= 44 &&
        VERIFIED_COMPETITIVE_IDS.has(q.id)
    )
    const compDan = cleanPool.filter(
      (q) =>
        q.source.work === 'Daniel' &&
        q.source.chapter >= 7 &&
        q.source.chapter <= 12 &&
        VERIFIED_COMPETITIVE_IDS.has(q.id)
    )

    const selPR = selectWithUniqueFacts(compPR, 50, seed + 10)
    const selDan = selectWithUniqueFacts(compDan, 50, seed + 20)

    selected = shuffleWithRng([...selPR, ...selDan], seed)
  }

  // Compute realized summary
  let prCount = 0
  let danielCount = 0
  let scCount = 0
  let tfCount = 0
  let competitiveCount = 0
  let coverageCount = 0
  const chapterCounts: Record<string, number> = {}

  for (const q of selected) {
    if (q.source.work === 'Profetas y Reyes') prCount++
    else danielCount++

    if (q.type === 'true_false' || q.family === 'true_false') tfCount++
    else scCount++

    if (classifyEmergencyQuestion(q) === 'COMPETITIVE_GOOD') competitiveCount++
    else coverageCount++

    const chKey = `${q.source.work === 'Daniel' ? 'DAN' : 'PR'}${q.source.chapter}`
    chapterCounts[chKey] = (chapterCounts[chKey] ?? 0) + 1
  }

  const distinctFacts = new Set(selected.map((q) => q.factId ?? q.id)).size

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
      coverageCount,
      chapterCounts,
      distinctFacts,
    },
  }
}