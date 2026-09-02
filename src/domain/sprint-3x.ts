import type { Question, SelectionStrategy } from "@/domain/types"

export type SprintSimulationMix = "70-30" | "50-50" | "30-70"

export type FactExposure3x = {
  factId: string
  sourceUnitId: string
  exposures_completed: number
  distinct_presentations_seen: string[]
  last_seen_at: number | null
  last_result: "correct" | "incorrect" | "doubted" | null
  last_response_ms: number | null
  doubted: boolean
  next_due_at: number | null
  mastery_3x: boolean
  unit_mastery_3x: boolean
  missing_fact_variants: boolean
}

export type UnitExposure3x = {
  sourceUnitId: string
  distinct_facts_seen: string[]
  distinct_presentations_seen: string[]
  errors_count: number
  doubts_count: number
  unit_mastery_3x: boolean
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

export type SprintSelectionSummary = {
  strategy: SelectionStrategy
  prCount: number
  danielCount: number
  familyCounts: {
    single_choice: number
    fill_blank: number
    true_false: number
  }
  chapterCounts: Record<string, number>
  newCount: number
  repairCount: number
  slowCount: number
  distinctFacts: number
  quotaShortfalls: Record<string, number>
}

const THREE_HOURS_MS = 3 * 60 * 60 * 1000
const TWENTY_FOUR_HOURS_MS = 24 * 60 * 60 * 1000
const SLOW_THRESHOLD_MS = 6000

export function getCanonicalPresentationId(q: Question): string {
  const raw =
    (q.metadata?.runtimeBaseVariantId as string | undefined) ??
    q.variantId ??
    q.id
  // Strip runtime suffix variations like :runtime, _shuffled, etc.
  return String(raw)
    .replace(/:(runtime|shuffled|\d+)$/, "")
    .replace(/_(shuffled|\d+)$/, "")
}

export function emptyFactExposure(factId: string, sourceUnitId = ""): FactExposure3x {
  return {
    factId,
    sourceUnitId,
    exposures_completed: 0,
    distinct_presentations_seen: [],
    last_seen_at: null,
    last_result: null,
    last_response_ms: null,
    doubted: false,
    next_due_at: null,
    mastery_3x: false,
    unit_mastery_3x: false,
    missing_fact_variants: false,
  }
}

export function recordAttempt3x(
  current: FactExposure3x,
  question: Question,
  isCorrect: boolean,
  doubted: boolean,
  responseMs: number,
  timestamp = Date.now(),
  availableFactVariantsCount = 3
): FactExposure3x {
  const presId = getCanonicalPresentationId(question)
  const distinct = current.distinct_presentations_seen.includes(presId)
    ? current.distinct_presentations_seen
    : [...current.distinct_presentations_seen, presId]

  const isSlow = responseMs > SLOW_THRESHOLD_MS
  const isEffectiveError = !isCorrect || doubted

  let nextDue = timestamp
  let newCompleted = current.exposures_completed

  if (isEffectiveError) {
    // Return after 20-40 questions or 20 minutes, plus next day
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

  const hadNextDay = current.last_seen_at
    ? (timestamp - current.last_seen_at) >= 18 * 60 * 60 * 1000
    : false

  const missingVariants = availableFactVariantsCount < 3
  // Fact mastery: 3 distinct presentations of the same fact
  const factMastery =
    !missingVariants &&
    distinct.length >= 3 &&
    newCompleted >= 3 &&
    !isEffectiveError &&
    (current.mastery_3x || hadNextDay)

  // Unit mastery: if fact has fewer than 3 variants, allow unit mastery after 3 correct presentations of unit
  const unitMastery =
    missingVariants &&
    distinct.length >= 3 &&
    newCompleted >= 3 &&
    !isEffectiveError &&
    (current.unit_mastery_3x || hadNextDay)

  return {
    factId: current.factId,
    sourceUnitId: question.sourceUnitId ?? (question.metadata?.sourceUnitId as string) ?? current.sourceUnitId,
    exposures_completed: newCompleted,
    distinct_presentations_seen: distinct,
    last_seen_at: timestamp,
    last_result: !isCorrect ? "incorrect" : doubted ? "doubted" : "correct",
    last_response_ms: responseMs,
    doubted,
    next_due_at: nextDue,
    mastery_3x: factMastery,
    unit_mastery_3x: unitMastery,
    missing_fact_variants: missingVariants,
  }
}

/**
 * Largest Remainder Method (Hamilton-Hare) to distribute integer targets without systematic bias.
 */
export function distributeByLargestRemainder<K extends string | number>(
  total: number,
  items: Array<{ key: K; weight: number }>,
  tieSeed = 0
): Record<K, number> {
  const result: Record<string | number, number> = {}
  const totalWeight = items.reduce((sum, item) => sum + item.weight, 0)
  if (totalWeight <= 0 || items.length === 0) return result as Record<K, number>

  const remainders: Array<{ key: K; floor: number; remainder: number; originalIndex: number }> = []
  let allocated = 0

  items.forEach((item, index) => {
    const raw = (total * item.weight) / totalWeight
    const fl = Math.floor(raw)
    result[item.key] = fl
    allocated += fl
    remainders.push({
      key: item.key,
      floor: fl,
      remainder: raw - fl,
      originalIndex: index,
    })
  })

  let toDistribute = total - allocated
  // Sort by remainder descending; break ties by rotating based on tieSeed
  remainders.sort((a, b) => {
    const diff = b.remainder - a.remainder
    if (Math.abs(diff) > 1e-9) return diff
    // Tie breaker: rotated index so no item is perpetually favored/penalized
    const rotA = (a.originalIndex + tieSeed) % items.length
    const rotB = (b.originalIndex + tieSeed) % items.length
    return rotA - rotB
  })

  for (let i = 0; i < toDistribute && i < remainders.length; i++) {
    result[remainders[i].key] += 1
  }

  return result as Record<K, number>
}

export type SprintQuotas = {
  total: number
  prTarget: number
  danTarget: number
  prByChapter: Record<number, number>
  danByChapter: Record<number, number>
  familyQuotas: {
    single_choice: number
    fill_blank: number
    true_false: number
  }
}

export function computeSprintQuotas(
  total: number,
  mix: SprintSimulationMix = "70-30",
  tieSeed = 0
): SprintQuotas {
  let prRatio = 0.7
  if (mix === "50-50") {
    prRatio = 0.5
  } else if (mix === "30-70") {
    prRatio = 0.3
  }

  const prTarget = Math.round(total * prRatio)
  const danTarget = total - prTarget

  // PR chapter distribution: PR39 15%, PR40 15%, PR41 15%, PR42 15%, PR43 20%, PR44 20%
  const prItems = [
    { key: 39, weight: 0.15 },
    { key: 40, weight: 0.15 },
    { key: 41, weight: 0.15 },
    { key: 42, weight: 0.15 },
    { key: 43, weight: 0.20 },
    { key: 44, weight: 0.20 },
  ]
  const prByChapter = distributeByLargestRemainder(prTarget, prItems, tieSeed)

  // Daniel chapter distribution:
  // Dan 7, 8, 9, 11: 60% of Daniel block
  // Dan 10, 12: 20% of Daniel block
  // Dan 1-6: 20% of Daniel block (all chapters 1 to 12 represented)
  const danItems = [
    // Dan 1-6 (20% total = ~3.33% each)
    { key: 1, weight: 0.20 / 6 },
    { key: 2, weight: 0.20 / 6 },
    { key: 3, weight: 0.20 / 6 },
    { key: 4, weight: 0.20 / 6 },
    { key: 5, weight: 0.20 / 6 },
    { key: 6, weight: 0.20 / 6 },
    // Dan 7, 8, 9, 11 (60% total = 15% each)
    { key: 7, weight: 0.15 },
    { key: 8, weight: 0.15 },
    { key: 9, weight: 0.15 },
    { key: 11, weight: 0.15 },
    // Dan 10, 12 (20% total = 10% each)
    { key: 10, weight: 0.10 },
    { key: 12, weight: 0.10 },
  ]
  const danByChapter = distributeByLargestRemainder(danTarget, danItems, tieSeed)

  // Overall family quotas: 45% single_choice, 30% fill_blank, 25% true_false
  const familyItems = [
    { key: "single_choice" as const, weight: 0.45 },
    { key: "fill_blank" as const, weight: 0.30 },
    { key: "true_false" as const, weight: 0.25 },
  ]
  const familyQuotas = distributeByLargestRemainder(total, familyItems, tieSeed)

  return {
    total,
    prTarget,
    danTarget,
    prByChapter: prByChapter as Record<number, number>,
    danByChapter: danByChapter as Record<number, number>,
    familyQuotas: familyQuotas as {
      single_choice: number
      fill_blank: number
      true_false: number
    },
  }
}

export function categorizeQuestionFamily(q: Question): "single_choice" | "fill_blank" | "true_false" {
  const fam = q.family ?? q.type
  if (fam === "fill_choice" || fam === "fill_blank") return "fill_blank"
  if (fam === "true_false") return "true_false"
  return "single_choice"
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

/**
 * Real Sprint Selector: Simultaneous constraint solver for material (70/30),
 * chapter distribution, and family quotas (45 single, 30 fill, 25 true/false).
 */
export function selectSprintNacionalRound(
  eligibleQuestions: Question[],
  count: number,
  seed = 42,
  historyMap = new Map<string, FactExposure3x>(),
  mix: SprintSimulationMix = "70-30"
): { questions: Question[]; summary: SprintSelectionSummary } {
  // Exclude blind and provisional questions strictly
  const validPool = eligibleQuestions.filter((q) => {
    if (q.blindPool || q.blindFinalPool) return false
    const prov = (q.metadata?.provisional as boolean | undefined) ?? (q as any).provisional
    if (prov) return false
    if (q.tier === ("R3_PROVISIONAL_UNVERIFIED" as any)) return false
    return true
  })

  const quotas = computeSprintQuotas(count, mix, seed)
  const shuffled = shuffleWithSeed(validPool, seed)

  // Prioritize candidates based on 3X Exposure needs
  const scoreCandidate = (q: Question): number => {
    const fid = q.factId ?? q.factKey
    const hist = historyMap.get(fid)
    if (!hist) return 10 // Unseen, high priority
    if (hist.mastery_3x) return 1 // Mastered, lower priority
    const presId = getCanonicalPresentationId(q)
    if (hist.distinct_presentations_seen.includes(presId)) return 2 // Seen this exact presentation
    if (hist.last_result === "incorrect" || hist.last_result === "doubted") return 25 // High priority repair
    if (hist.last_response_ms && hist.last_response_ms > SLOW_THRESHOLD_MS) return 18 // Slow repair
    return 8 // Needs next spaced exposure
  }

  shuffled.sort((a, b) => scoreCandidate(b) - scoreCandidate(a))

  // Simultaneously allocate questions respecting:
  // 1. Material (PR vs Daniel)
  // 2. Chapter target quotas
  // 3. Family target quotas (45 single_choice, 30 fill_blank, 25 true_false)
  const remainingFamily = { ...quotas.familyQuotas }
  const remainingPRChapters = { ...quotas.prByChapter }
  const remainingDanChapters = { ...quotas.danByChapter }

  const usedFactIds = new Set<string>()
  const selected: Question[] = []

  // Family quotas per material block:
  // PR: Math.round(45 * 0.70) = 31 single, Math.round(30 * 0.70) = 21 fill, 18 tf
  // Daniel: 14 single, 9 fill, 7 tf
  const prFamilyTargets = {
    single_choice: Math.round(quotas.familyQuotas.single_choice * (quotas.prTarget / count)),
    fill_blank: Math.round(quotas.familyQuotas.fill_blank * (quotas.prTarget / count)),
    true_false: 0,
  }
  prFamilyTargets.true_false = quotas.prTarget - (prFamilyTargets.single_choice + prFamilyTargets.fill_blank)

  const danFamilyTargets = {
    single_choice: quotas.familyQuotas.single_choice - prFamilyTargets.single_choice,
    fill_blank: quotas.familyQuotas.fill_blank - prFamilyTargets.fill_blank,
    true_false: quotas.familyQuotas.true_false - prFamilyTargets.true_false,
  }

  const remainingPRFamily = { ...prFamilyTargets }
  const remainingDanFamily = { ...danFamilyTargets }

  // Pass 1: Select exact chapter & family matches
  for (const q of shuffled) {
    if (selected.length >= count) break
    const fid = q.factId ?? q.factKey
    if (usedFactIds.has(fid)) continue

    const work = q.source.work
    const ch = q.source.chapter
    const fam = categorizeQuestionFamily(q)

    if (work === "Profetas y Reyes") {
      if ((remainingPRChapters[ch] ?? 0) > 0 && remainingPRFamily[fam] > 0) {
        selected.push(q)
        usedFactIds.add(fid)
        remainingPRChapters[ch] -= 1
        remainingPRFamily[fam] -= 1
        remainingFamily[fam] -= 1
      }
    } else if (work === "Daniel") {
      if ((remainingDanChapters[ch] ?? 0) > 0 && remainingDanFamily[fam] > 0) {
        selected.push(q)
        usedFactIds.add(fid)
        remainingDanChapters[ch] -= 1
        remainingDanFamily[fam] -= 1
        remainingFamily[fam] -= 1
      }
    }
  }

  // Pass 2: Fulfill remaining chapter quotas if family was full, or vice versa
  for (const q of shuffled) {
    if (selected.length >= count) break
    const fid = q.factId ?? q.factKey
    if (usedFactIds.has(fid)) continue

    const work = q.source.work
    const ch = q.source.chapter
    const fam = categorizeQuestionFamily(q)

    if (work === "Profetas y Reyes") {
      const prSelectedCount = selected.filter((item) => item.source.work === "Profetas y Reyes").length
      if (prSelectedCount < quotas.prTarget) {
        if ((remainingPRChapters[ch] ?? 0) > 0 || remainingFamily[fam] > 0) {
          selected.push(q)
          usedFactIds.add(fid)
          if ((remainingPRChapters[ch] ?? 0) > 0) remainingPRChapters[ch] -= 1
          if (remainingFamily[fam] > 0) remainingFamily[fam] -= 1
        }
      }
    } else if (work === "Daniel") {
      const danSelectedCount = selected.filter((item) => item.source.work === "Daniel").length
      if (danSelectedCount < quotas.danTarget) {
        if ((remainingDanChapters[ch] ?? 0) > 0 || remainingFamily[fam] > 0) {
          selected.push(q)
          usedFactIds.add(fid)
          if ((remainingDanChapters[ch] ?? 0) > 0) remainingDanChapters[ch] -= 1
          if (remainingFamily[fam] > 0) remainingFamily[fam] -= 1
        }
      }
    }
  }

  // Pass 3: Complete remaining count maintaining 70/30 without duplicate facts
  if (selected.length < count) {
    for (const q of shuffled) {
      if (selected.length >= count) break
      const fid = q.factId ?? q.factKey
      if (usedFactIds.has(fid)) continue
      selected.push(q)
      usedFactIds.add(fid)
    }
  }

  // Compile final metrics and record any shortfall
  const finalQuestions = shuffleWithSeed(selected.slice(0, count), seed + 1)

  let prCount = 0
  let danielCount = 0
  const familyCounts = { single_choice: 0, fill_blank: 0, true_false: 0 }
  const chapterCounts: Record<string, number> = {}
  let newCount = 0
  let repairCount = 0
  let slowCount = 0

  for (const q of finalQuestions) {
    const fid = q.factId ?? q.factKey
    const hist = historyMap.get(fid)
    if (!hist || hist.exposures_completed === 0) newCount++
    else if (hist.last_result === "incorrect" || hist.last_result === "doubted") repairCount++
    else if (hist.last_response_ms && hist.last_response_ms > SLOW_THRESHOLD_MS) slowCount++

    if (q.source.work === "Profetas y Reyes") prCount++
    else danielCount++

    const fam = categorizeQuestionFamily(q)
    familyCounts[fam]++

    const chKey = `${q.source.work === "Daniel" ? "DAN" : "PR"}${q.source.chapter}`
    chapterCounts[chKey] = (chapterCounts[chKey] ?? 0) + 1
  }

  const quotaShortfalls: Record<string, number> = {}
  if (prCount !== quotas.prTarget) quotaShortfalls["pr"] = quotas.prTarget - prCount
  if (danielCount !== quotas.danTarget) quotaShortfalls["daniel"] = quotas.danTarget - danielCount
  if (familyCounts.single_choice !== quotas.familyQuotas.single_choice)
    quotaShortfalls["single_choice"] = quotas.familyQuotas.single_choice - familyCounts.single_choice
  if (familyCounts.fill_blank !== quotas.familyQuotas.fill_blank)
    quotaShortfalls["fill_blank"] = quotas.familyQuotas.fill_blank - familyCounts.fill_blank
  if (familyCounts.true_false !== quotas.familyQuotas.true_false)
    quotaShortfalls["true_false"] = quotas.familyQuotas.true_false - familyCounts.true_false

  const summary: SprintSelectionSummary = {
    strategy: "sprint-3x",
    prCount,
    danielCount,
    familyCounts,
    chapterCounts,
    newCount,
    repairCount,
    slowCount,
    distinctFacts: usedFactIds.size,
    quotaShortfalls,
  }

  return { questions: finalQuestions, summary }
}

export function buildSprintSimulationRounds(
  eligibleQuestions: Question[],
  seed = 42,
  historyMap = new Map<string, FactExposure3x>()
): { mix: SprintSimulationMix; rounds: Question[][]; summary: SprintSelectionSummary } {
  // Hidden mix rotation: 70/30, 50/50, or 30/70
  const mixOptions: SprintSimulationMix[] = ["70-30", "50-50", "30-70"]
  const mix = mixOptions[seed % 3]

  const { questions, summary } = selectSprintNacionalRound(eligibleQuestions, 100, seed, historyMap, mix)
  const rounds: Question[][] = []
  for (let i = 0; i < 5; i++) {
    rounds.push(questions.slice(i * 20, (i + 1) * 20))
  }

  return { mix, rounds, summary }
}
