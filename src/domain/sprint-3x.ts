import type { Question } from "@/domain/types"

export type SprintSimulationMix = "70-30" | "50-50" | "30-70"

export type FactExposure3x = {
  factId: string
  exposures_completed: number
  distinct_presentations_seen: string[]
  last_seen_at: number | null
  last_result: "correct" | "incorrect" | "doubted" | null
  last_response_ms: number | null
  doubted: boolean
  next_due_at: number | null
  mastery_3x: boolean
}

export type SprintDayPlan = {
  date: string
  dayName: string
  targetTotal: number
  targetPR: number
  targetDaniel: number
  description: string
  includesSimulation: boolean
}

export const SPRINT_DAILY_PLANS: Record<string, SprintDayPlan> = {
  "2026-09-02": {
    date: "2026-09-02",
    dayName: "Miércoles 2",
    targetTotal: 700,
    targetPR: 490,
    targetDaniel: 210,
    description: "Recuperación intensiva 70/30 con simulación 5×20 incluida.",
    includesSimulation: true,
  },
  "2026-09-03": {
    date: "2026-09-03",
    dayName: "Jueves 3",
    targetTotal: 1000,
    targetPR: 700,
    targetDaniel: 300,
    description: "Consolidación de segunda y tercera exposición espaciada.",
    includesSimulation: false,
  },
  "2026-09-04": {
    date: "2026-09-04",
    dayName: "Viernes 4",
    targetTotal: 600,
    targetPR: 420,
    targetDaniel: 180,
    description: "Cierre de dudas, lentas, errores y simulación final de 100.",
    includesSimulation: true,
  },
  "2026-09-05": {
    date: "2026-09-05",
    dayName: "Sábado 5",
    targetTotal: 40,
    targetPR: 28,
    targetDaniel: 12,
    description: "Calentamiento opcional de preguntas conocidas (sin contenido nuevo).",
    includesSimulation: false,
  },
}

const THREE_HOURS_MS = 3 * 60 * 60 * 1000
const TWENTY_FOUR_HOURS_MS = 24 * 60 * 60 * 1000
const SLOW_THRESHOLD_MS = 6000

export function emptyFactExposure(factId: string): FactExposure3x {
  return {
    factId,
    exposures_completed: 0,
    distinct_presentations_seen: [],
    last_seen_at: null,
    last_result: null,
    last_response_ms: null,
    doubted: false,
    next_due_at: null,
    mastery_3x: false,
  }
}

export function recordAttempt3x(
  current: FactExposure3x,
  questionId: string,
  isCorrect: boolean,
  doubted: boolean,
  responseMs: number,
  timestamp = Date.now()
): FactExposure3x {
  const distinct = current.distinct_presentations_seen.includes(questionId)
    ? current.distinct_presentations_seen
    : [...current.distinct_presentations_seen, questionId]

  const isSlow = responseMs > SLOW_THRESHOLD_MS
  const isEffectiveError = !isCorrect || doubted

  let nextDue = timestamp
  let newCompleted = current.exposures_completed

  if (isEffectiveError) {
    // Incorrect or doubted: returns after 20-40 questions or 20 minutes, plus next day
    nextDue = timestamp + 20 * 60 * 1000
  } else if (isSlow) {
    // Slow correct: needs same day review and next day review
    nextDue = timestamp + 2 * 60 * 60 * 1000
    if (newCompleted < 1) newCompleted = 1
  } else {
    // Fast confident correct
    newCompleted += 1
    if (newCompleted === 1) {
      nextDue = timestamp + THREE_HOURS_MS
    } else if (newCompleted === 2) {
      nextDue = timestamp + TWENTY_FOUR_HOURS_MS
    } else {
      nextDue = timestamp + 72 * 60 * 60 * 1000
    }
  }

  // Check 3x Mastery condition:
  // Must have seen at least 3 distinct presentations, answered 3 successfully,
  // with at least one exposure separated by a next day interval
  const hadNextDay = current.last_seen_at
    ? (timestamp - current.last_seen_at) >= 18 * 60 * 60 * 1000
    : false

  const masteryAchieved =
    distinct.length >= 3 &&
    newCompleted >= 3 &&
    !isEffectiveError &&
    (current.mastery_3x || hadNextDay)

  return {
    factId: current.factId,
    exposures_completed: newCompleted,
    distinct_presentations_seen: distinct,
    last_seen_at: timestamp,
    last_result: !isCorrect ? "incorrect" : doubted ? "doubted" : "correct",
    last_response_ms: responseMs,
    doubted,
    next_due_at: nextDue,
    mastery_3x: masteryAchieved,
  }
}

function pseudoRandom(seed: number) {
  let s = seed >>> 0
  return () => {
    s = (Math.imul(s, 1103515245) + 12345) >>> 0
    return s / 0x100000000
  }
}

function shuffleWithSeed<T>(arr: T[], seed: number): T[] {
  const result = arr.slice()
  const rnd = pseudoRandom(seed)
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(rnd() * (i + 1))
    ;[result[i], result[j]] = [result[j], result[i]]
  }
  return result
}

export type SprintQuotas = {
  total: number
  prTarget: number
  danTarget: number
  prByChapter: Record<number, number>
  danByChapter: Record<number, number>
  familyQuotas: Record<string, number>
}

export function computeSprintQuotas(total: number, mix: SprintSimulationMix = "70-30"): SprintQuotas {
  let prRatio = 0.7
  if (mix === "50-50") {
    prRatio = 0.5
  } else if (mix === "30-70") {
    prRatio = 0.3
  }

  const prTarget = Math.round(total * prRatio)
  const danTarget = total - prTarget

  // PR chapter distribution: PR39 15%, PR40 15%, PR41 15%, PR42 15%, PR43 20%, PR44 20%
  const pr39 = Math.round(prTarget * 0.15)
  const pr40 = Math.round(prTarget * 0.15)
  const pr41 = Math.round(prTarget * 0.15)
  const pr42 = Math.round(prTarget * 0.15)
  const pr43 = Math.round(prTarget * 0.20)
  const pr44 = prTarget - (pr39 + pr40 + pr41 + pr42 + pr43)

  // Daniel chapter distribution: Dan 7,8,9,11 = 60%, Dan 10,12 = 20%, Dan 1-6 = 20%
  const danMajorTotal = Math.round(danTarget * 0.60) // Dan 7, 8, 9, 11 (15% each)
  const dan1012Total = Math.round(danTarget * 0.20)  // Dan 10, 12 (10% each)
  const dan16Total = danTarget - (danMajorTotal + dan1012Total) // Dan 1-6

  const dan7 = Math.round(danMajorTotal * 0.25)
  const dan8 = Math.round(danMajorTotal * 0.25)
  const dan9 = Math.round(danMajorTotal * 0.25)
  const dan11 = danMajorTotal - (dan7 + dan8 + dan9)

  const dan10 = Math.round(dan1012Total * 0.5)
  const dan12 = dan1012Total - dan10

  const dan16Base = Math.floor(dan16Total / 6)
  let dan16Rem = dan16Total % 6
  const dan16: Record<number, number> = {}
  for (let c = 1; c <= 6; c++) {
    dan16[c] = dan16Base + (dan16Rem > 0 ? 1 : 0)
    if (dan16Rem > 0) dan16Rem--
  }

  const singleChoice = Math.round(total * 0.45)
  const fillBlank = Math.round(total * 0.30)
  const trueFalse = total - (singleChoice + fillBlank)

  return {
    total,
    prTarget,
    danTarget,
    prByChapter: {
      39: pr39,
      40: pr40,
      41: pr41,
      42: pr42,
      43: pr43,
      44: pr44,
    },
    danByChapter: {
      ...dan16,
      7: dan7,
      8: dan8,
      9: dan9,
      10: dan10,
      11: dan11,
      12: dan12,
    },
    familyQuotas: {
      single_choice: singleChoice,
      fill_blank: fillBlank,
      true_false: trueFalse,
    },
  }
}

export function selectSprintNacionalRound(
  allQuestions: Question[],
  count: number,
  seed = 42,
  historyMap = new Map<string, FactExposure3x>(),
  mix: SprintSimulationMix = "70-30"
): Question[] {
  const quotas = computeSprintQuotas(count, mix)
  const usedFactIds = new Set<string>()
  const selected: Question[] = []

  const shuffled = shuffleWithSeed(allQuestions, seed)

  // Prioritize candidates based on 3X Exposure needs
  const scoreCandidate = (q: Question): number => {
    const fid = q.factId ?? q.factKey
    const hist = historyMap.get(fid)
    if (!hist) return 10 // Unseen, high priority
    if (hist.mastery_3x) return 1 // Mastered, low priority
    if (hist.distinct_presentations_seen.includes(q.id)) return 2 // Seen this exact question
    if (hist.last_result === "incorrect" || hist.last_result === "doubted") return 20 // High priority repair
    if (hist.last_response_ms && hist.last_response_ms > SLOW_THRESHOLD_MS) return 15 // Slow repair
    return 8 // Needs next spaced exposure
  }

  shuffled.sort((a, b) => scoreCandidate(b) - scoreCandidate(a))

  // Select PR questions by chapter quotas
  for (const [chStr, target] of Object.entries(quotas.prByChapter)) {
    const ch = parseInt(chStr, 10)
    let needed = target
    for (const q of shuffled) {
      if (needed <= 0) break
      const fid = q.factId ?? q.factKey
      if (usedFactIds.has(fid)) continue
      if (q.source.work === "Profetas y Reyes" && q.source.chapter === ch) {
        selected.push(q)
        usedFactIds.add(fid)
        needed--
      }
    }
  }

  // Select Daniel questions by chapter quotas
  for (const [chStr, target] of Object.entries(quotas.danByChapter)) {
    const ch = parseInt(chStr, 10)
    let needed = target
    for (const q of shuffled) {
      if (needed <= 0) break
      const fid = q.factId ?? q.factKey
      if (usedFactIds.has(fid)) continue
      if (q.source.work === "Daniel" && q.source.chapter === ch) {
        selected.push(q)
        usedFactIds.add(fid)
        needed--
      }
    }
  }

  // Fill any shortfall without repeating factId
  if (selected.length < count) {
    for (const q of shuffled) {
      if (selected.length >= count) break
      const fid = q.factId ?? q.factKey
      if (!usedFactIds.has(fid)) {
        selected.push(q)
        usedFactIds.add(fid)
      }
    }
  }

  // Return exactly requested count, interleaved and shuffled
  return shuffleWithSeed(selected.slice(0, count), seed + 1)
}

export function buildSprintSimulationRounds(
  allQuestions: Question[],
  seed = 42,
  historyMap = new Map<string, FactExposure3x>()
): { mix: SprintSimulationMix; rounds: Question[][] } {
  // Hidden mix rotation: 70/30, 50/50, or 30/70
  const mixOptions: SprintSimulationMix[] = ["70-30", "50-50", "30-70"]
  const mix = mixOptions[seed % 3]

  const totalQuestions = selectSprintNacionalRound(allQuestions, 100, seed, historyMap, mix)
  const rounds: Question[][] = []
  for (let i = 0; i < 5; i++) {
    rounds.push(totalQuestions.slice(i * 20, (i + 1) * 20))
  }

  return { mix, rounds }
}
