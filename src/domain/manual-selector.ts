import { FINAL_FILTER_CATALOG, type FilterCatalogItem } from "@/data/filter-catalog"
import { isMastered, isQuestionNew } from "@/domain/mastery"
import type {
  Question,
  QuestionProgress,
  SessionConfig,
} from "@/domain/types"

export type FacetedCounts = {
  totalEligible: number
  prEligible: number
  danielEligible: number
  chapterCounts: Record<string, number>
  tierCounts: {
    all: number
    coverage: number
    competitive: number
  }
  typeCounts: {
    single_choice: number
    fill_blank: number
    true_false: number
  }
  statusCounts: {
    all: number
    new: number
    failed: number
    difficult: number
    mastered: number
    favorite: number
  }
}

function isFilterCatalogQuestionType(
  type: Question["type"],
): type is FilterCatalogItem["type"] {
  return type === "single_choice" || type === "fill_blank" || type === "true_false"
}

export function filterCatalogItemMatches(
  item: FilterCatalogItem,
  config: SessionConfig,
  progressMap: Map<string, QuestionProgress>
): boolean {
  // Blind & provisional are always excluded for standard and manual training
  if (!config.includeBlind && item.blind) return false
  if (item.provisional) return false

  // 1. Material (Source Works) - never treat empty selection as "all"
  if (config.sourceWorks.length === 0 || !config.sourceWorks.includes(item.work as any)) {
    return false
  }

  // 2. Chapters (if specified, item chapter must be in list)
  if (config.chapters.length > 0 && !config.chapters.includes(item.chapter)) {
    return false
  }

  // 3. Tier / Difficulty filter
  const tierMode = config.tierFilter ?? "all"
  if (tierMode === "competitive") {
    if (
      item.tier !== "COMPETITIVE_ACCEPT" ||
      (item.difficultyBand !== "HARD" && item.difficultyBand !== "EXPERT")
    ) {
      return false
    }
  } else if (tierMode === "coverage") {
    if (item.tier !== "COVERAGE_ACCEPT") {
      return false
    }
  } else if (config.difficultyBands && config.difficultyBands.length > 0) {
    if (!config.difficultyBands.includes(item.difficultyBand as any)) {
      return false
    }
  }

  // 4. Question Types - never treat empty selection as "all"
  if (config.types.length === 0 || !config.types.includes(item.type as any)) {
    return false
  }

  // 5. Status
  const prog =
    progressMap.get(item.id) ??
    progressMap.get(`BANCO_UNICO_CONEXION_BIBLICA_2026:${item.id}`) ??
    progressMap.get(`local:${item.id}`)
  if (config.statuses.length > 0 && !config.statuses.includes("all")) {
    const matchesStatus = config.statuses.some((st) => {
      if (st === "new") return isQuestionNew(prog)
      if (st === "failed") return Boolean(prog && prog.timesIncorrect > 0)
      if (st === "difficult")
        return item.difficulty >= 4 || Boolean(prog?.markedDifficult)
      if (st === "mastered") return isMastered(prog)
      if (st === "favorite") return Boolean(prog?.favorite)
      return true
    })
    if (!matchesStatus) return false
  }

  return true
}

export function computeFacetedCounts(
  config: SessionConfig,
  progressMap: Map<string, QuestionProgress>,
  customQuestions?: Question[]
): FacetedCounts {
  let totalEligible = 0
  let prEligible = 0
  let danielEligible = 0
  const chapterCounts: Record<string, number> = {}

  const tierCounts = { all: 0, coverage: 0, competitive: 0 }
  const typeCounts = { single_choice: 0, fill_blank: 0, true_false: 0 }
  const statusCounts = {
    all: 0,
    new: 0,
    failed: 0,
    difficult: 0,
    mastered: 0,
    favorite: 0,
  }

  const catalog: FilterCatalogItem[] =
    customQuestions && customQuestions.length > 0 && (!customQuestions[0].bankId || customQuestions[0].bankId !== "BANCO_UNICO_CONEXION_BIBLICA_2026" || customQuestions.length < 100)
      ? customQuestions.flatMap((q): FilterCatalogItem[] => {
          if (!isFilterCatalogQuestionType(q.type)) return []
          return [{
          id: q.id,
          factId: q.factId ?? q.factKey,
          sourceUnitId: q.sourceUnitId ?? q.id,
          work: q.source.work,
          chapter: q.source.chapter,
          type: q.type,
          family: q.family ?? q.type,
          difficulty: q.difficulty,
          difficultyBand: (q.difficultyBand ?? "MEDIUM") as any,
          tier: q.tier ?? null,
          provisional: Boolean(q.metadata?.provisional),
          blind: Boolean(q.blindPool || q.blindFinalPool),
          }]
        })
      : FINAL_FILTER_CATALOG

  for (const item of catalog) {
    if (filterCatalogItemMatches(item, config, progressMap)) {
      totalEligible++
      if (item.work === "Profetas y Reyes") prEligible++
      else danielEligible++
    }

    // Accumulate chapter count independent of currently selected chapters
    if (filterCatalogItemMatches(item, { ...config, chapters: [] }, progressMap)) {
      const chKey = `${item.work === "Daniel" ? "DAN" : "PR"}${item.chapter}`
      chapterCounts[chKey] = (chapterCounts[chKey] ?? 0) + 1
    }

    // Compute facet counts relative to base filters (material & chapters)
    const baseConfig: SessionConfig = {
      ...config,
      tierFilter: "all",
      types: [],
      statuses: ["all"],
    }
    if (filterCatalogItemMatches(item, baseConfig, progressMap)) {
      // Tier facets
      tierCounts.all++
      if (item.tier === "COVERAGE_ACCEPT") {
        tierCounts.coverage++
      }
      if (
        item.tier === "COMPETITIVE_ACCEPT" &&
        (item.difficultyBand === "HARD" || item.difficultyBand === "EXPERT") &&
        !item.provisional &&
        !item.blind
      ) {
        tierCounts.competitive++
      }

      // Type facets
      if (item.type === "single_choice") typeCounts.single_choice++
      else if (item.type === "fill_blank") typeCounts.fill_blank++
      else if (item.type === "true_false") typeCounts.true_false++

      // Status facets
      const prog = progressMap.get(item.id) ?? progressMap.get(`local:${item.id}`)
      statusCounts.all++
      if (isQuestionNew(prog)) statusCounts.new++
      if (prog && prog.timesIncorrect > 0) statusCounts.failed++
      if (item.difficulty >= 4 || prog?.markedDifficult) statusCounts.difficult++
      if (isMastered(prog)) statusCounts.mastered++
      if (prog?.favorite) statusCounts.favorite++
    }
  }

  return {
    totalEligible,
    prEligible,
    danielEligible,
    chapterCounts,
    tierCounts,
    typeCounts,
    statusCounts,
  }
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

export type ManualSelectionResult =
  | {
      success: true
      questions: Question[]
      realizedSummary: {
        total: number
        prCount: number
        danielCount: number
        chapterCounts: Record<string, number>
        familyCounts: Record<string, number>
        competitiveCount: number
        coverageCount: number
      }
      quotaShortfalls: Record<string, number>
    }
  | {
      success: false
      error: string
      availableCount: number
      requestedCount: number
    }

export function selectManualSession(
  pool: Question[],
  config: SessionConfig,
  progressMap: Map<string, QuestionProgress>,
  seed = Date.now()
): ManualSelectionResult {
  // 1. Filter candidates strictly
  const candidates = pool.filter((q) => {
    // Blind & provisional check
    if (!config.includeBlind && (q.blindPool || q.blindFinalPool)) return false
    if (q.metadata?.provisional) return false

    // Material
    if (config.sourceWorks.length > 0 && !config.sourceWorks.includes(q.source.work)) {
      return false
    }

    // Chapters
    if (config.chapters.length > 0 && !config.chapters.includes(q.source.chapter)) {
      return false
    }

    // Tier / Difficulty
    const tierMode = config.tierFilter ?? "all"
    if (tierMode === "competitive") {
      if (
        q.tier !== "COMPETITIVE_ACCEPT" ||
        (q.difficultyBand !== "HARD" && q.difficultyBand !== "EXPERT")
      ) {
        return false
      }
    } else if (tierMode === "coverage") {
      if (q.tier !== "COVERAGE_ACCEPT") {
        return false
      }
    } else if (config.difficultyBands && config.difficultyBands.length > 0) {
      if (q.difficultyBand && !config.difficultyBands.includes(q.difficultyBand)) {
        return false
      }
    }

    // Type
    if (config.types.length > 0 && !config.types.includes(q.type)) {
      return false
    }

    // Status
    const prog =
      progressMap.get(q.id) ??
      progressMap.get(`${q.bankId ?? "local"}:${q.id}`) ??
      progressMap.get(`BANCO_UNICO_CONEXION_BIBLICA_2026:${q.id}`) ??
      progressMap.get(`local:${q.id}`)
    if (config.statuses.length > 0 && !config.statuses.includes("all")) {
      const matchesStatus = config.statuses.some((st) => {
        if (st === "new") return isQuestionNew(prog)
        if (st === "failed") return Boolean(prog && prog.timesIncorrect > 0)
        if (st === "difficult")
          return q.difficulty >= 4 || Boolean(prog?.markedDifficult)
        if (st === "mastered") return isMastered(prog)
        if (st === "favorite") return Boolean(prog?.favorite)
        return true
      })
      if (!matchesStatus) return false
    }

    return true
  })

  const targetCount = config.count === "all" ? candidates.length : config.count

  if (candidates.length === 0) {
    const diffDesc =
      config.tierFilter === "competitive"
        ? "COMPETITIVAS"
        : config.tierFilter === "coverage"
          ? "COBERTURA"
          : "solicitadas"
    return {
      success: false,
      error: `No se pudo crear una ronda de preguntas ${diffDesc}. Hay 0 disponibles con los filtros actuales.`,
      availableCount: 0,
      requestedCount: targetCount,
    }
  }

  const actualTargetCount = Math.min(targetCount, candidates.length)
  const quotaShortfalls: Record<string, number> = {}
  if (targetCount > candidates.length) {
    quotaShortfalls["disponibles"] = targetCount - candidates.length
  }

  // Shuffle candidates and pick targetCount
  const shuffled = shuffleWithRng(candidates, seed)
  const selected = shuffled.slice(0, actualTargetCount)

  let prCount = 0
  let danielCount = 0
  let competitiveCount = 0
  let coverageCount = 0
  const chapterCounts: Record<string, number> = {}
  const familyCounts: Record<string, number> = {
    single_choice: 0,
    fill_blank: 0,
    true_false: 0,
  }

  for (const q of selected) {
    if (q.source.work === "Profetas y Reyes") prCount++
    else danielCount++

    if (q.tier === "COMPETITIVE_ACCEPT") {
      competitiveCount++
    } else if (q.tier === "COVERAGE_ACCEPT") {
      coverageCount++
    }

    const chKey = `${q.source.work === "Daniel" ? "DAN" : "PR"}${q.source.chapter}`
    chapterCounts[chKey] = (chapterCounts[chKey] ?? 0) + 1

    const fam = q.family ?? q.type
    if (fam === "fill_choice" || fam === "fill_blank") familyCounts.fill_blank++
    else if (fam === "true_false") familyCounts.true_false++
    else familyCounts.single_choice++
  }

  return {
    success: true,
    questions: selected,
    realizedSummary: {
      total: selected.length,
      prCount,
      danielCount,
      chapterCounts,
      familyCounts,
      competitiveCount,
      coverageCount,
    },
    quotaShortfalls,
  }
}
