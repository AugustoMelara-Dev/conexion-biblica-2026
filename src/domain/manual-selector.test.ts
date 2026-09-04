import { describe, expect, it } from "vitest"
import {
  computeFacetedCounts,
  selectManualSession,
} from "@/domain/manual-selector"
import type { Question, QuestionProgress, SessionConfig } from "@/domain/types"
import { FINAL_FILTER_CATALOG } from "@/data/filter-catalog"
import { V18_AUDIT_STATUS_BY_ID } from "@/data/final-day-v18"

function mockQuestion(partial: Partial<Question>): Question {
  return {
    id: partial.id ?? "Q-01",
    bankId: "BANCO_UNICO_CONEXION_BIBLICA_2026",
    bankProfileId: "final-v7",
    type: partial.type ?? "single_choice",
    family: partial.family ?? "single_choice_direct",
    difficulty: partial.difficulty ?? 2,
    difficultyBand: partial.difficultyBand ?? "MEDIUM",
    tier: partial.tier ?? "COVERAGE_ACCEPT",
    source: {
      work: partial.source?.work ?? "Profetas y Reyes",
      version: "PDF",
      chapter: partial.source?.chapter ?? 39,
      reference: "Ref",
    },
    tags: [],
    factKey: partial.factKey ?? "F-01",
    factId: partial.factId ?? "F-01",
    question: partial.question ?? "¿Pregunta?",
    options: [{ id: "A", text: "Opción" }],
    correctAnswer: ["A"],
    metadata: partial.metadata,
  }
}

describe("manual-selector", () => {
  const pool: Question[] = [
    mockQuestion({
      id: "PR-39-1",
      source: { work: "Profetas y Reyes", chapter: 39, version: "PDF", reference: "" },
      type: "single_choice",
      difficultyBand: "BASIC",
      tier: "COVERAGE_ACCEPT",
    }),
    mockQuestion({
      id: "PR-43-1",
      source: { work: "Profetas y Reyes", chapter: 43, version: "PDF", reference: "" },
      type: "fill_blank",
      difficultyBand: "HARD",
      tier: "COMPETITIVE_ACCEPT",
    }),
    mockQuestion({
      id: "DAN-9-1",
      source: { work: "Daniel", chapter: 9, version: "RVR95", reference: "" },
      type: "true_false",
      difficultyBand: "MEDIUM",
      tier: "COVERAGE_ACCEPT",
    }),
    mockQuestion({
      id: "DAN-11-1",
      source: { work: "Daniel", chapter: 11, version: "RVR95", reference: "" },
      type: "single_choice",
      difficultyBand: "EXPERT",
      tier: "COMPETITIVE_ACCEPT",
    }),
  ]

  const emptyProgress = new Map<string, QuestionProgress>()

  it("filtra estrictamente por material PR", () => {
    const config: SessionConfig = {
      mode: "learn",
      count: 2,
      sourceWorks: ["Profetas y Reyes"],
      chapters: [],
      difficulties: [1, 2, 3, 4, 5],
      types: ["single_choice", "fill_blank", "true_false"],
      statuses: ["all"],
      shuffleQuestions: true,
      shuffleOptions: true,
      perQuestionSeconds: null,
      totalSeconds: null,
      tierFilter: "all",
    }
    const result = selectManualSession(pool, config, emptyProgress, 42)
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.questions).toHaveLength(2)
      expect(result.questions.every((q) => q.source.work === "Profetas y Reyes")).toBe(true)
      expect(result.realizedSummary.danielCount).toBe(0)
      expect(result.realizedSummary.prCount).toBe(2)
    }
  })

  it("filtra estrictamente por material Daniel", () => {
    const config: SessionConfig = {
      mode: "learn",
      count: 2,
      sourceWorks: ["Daniel"],
      chapters: [],
      difficulties: [1, 2, 3, 4, 5],
      types: ["single_choice", "fill_blank", "true_false"],
      statuses: ["all"],
      shuffleQuestions: true,
      shuffleOptions: true,
      perQuestionSeconds: null,
      totalSeconds: null,
      tierFilter: "all",
    }
    const result = selectManualSession(pool, config, emptyProgress, 42)
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.questions).toHaveLength(2)
      expect(result.questions.every((q) => q.source.work === "Daniel")).toBe(true)
      expect(result.realizedSummary.prCount).toBe(0)
    }
  })

  it("filtra por capítulo específico (PR43)", () => {
    const config: SessionConfig = {
      mode: "learn",
      count: 1,
      sourceWorks: ["Profetas y Reyes"],
      chapters: [43],
      difficulties: [1, 2, 3, 4, 5],
      types: ["single_choice", "fill_blank", "true_false"],
      statuses: ["all"],
      shuffleQuestions: true,
      shuffleOptions: true,
      perQuestionSeconds: null,
      totalSeconds: null,
      tierFilter: "all",
    }
    const result = selectManualSession(pool, config, emptyProgress, 42)
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.questions).toHaveLength(1)
      expect(result.questions[0].id).toBe("PR-43-1")
    }
  })

  it("filtra por múltiples capítulos (Daniel 9 y 11)", () => {
    const config: SessionConfig = {
      mode: "learn",
      count: 2,
      sourceWorks: ["Daniel"],
      chapters: [9, 11],
      difficulties: [1, 2, 3, 4, 5],
      types: ["single_choice", "fill_blank", "true_false"],
      statuses: ["all"],
      shuffleQuestions: true,
      shuffleOptions: true,
      perQuestionSeconds: null,
      totalSeconds: null,
      tierFilter: "all",
    }
    const result = selectManualSession(pool, config, emptyProgress, 42)
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.questions).toHaveLength(2)
      expect(result.questions.every((q) => q.source.chapter === 9 || q.source.chapter === 11)).toBe(true)
    }
  })

  it("filtra por tipo de reactivo (true_false únicamente)", () => {
    const config: SessionConfig = {
      mode: "learn",
      count: 1,
      sourceWorks: ["Daniel", "Profetas y Reyes"],
      chapters: [],
      difficulties: [1, 2, 3, 4, 5],
      types: ["true_false"],
      statuses: ["all"],
      shuffleQuestions: true,
      shuffleOptions: true,
      perQuestionSeconds: null,
      totalSeconds: null,
      tierFilter: "all",
    }
    const result = selectManualSession(pool, config, emptyProgress, 42)
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.questions).toHaveLength(1)
      expect(result.questions[0].type).toBe("true_false")
    }
  })

  it("filtra por nivel competitivo únicamente", () => {
    const config: SessionConfig = {
      mode: "learn",
      count: 2,
      sourceWorks: ["Daniel", "Profetas y Reyes"],
      chapters: [],
      difficulties: [1, 2, 3, 4, 5],
      types: ["single_choice", "fill_blank", "true_false"],
      statuses: ["all"],
      shuffleQuestions: true,
      shuffleOptions: true,
      perQuestionSeconds: null,
      totalSeconds: null,
      tierFilter: "competitive",
    }
    const result = selectManualSession(pool, config, emptyProgress, 42)
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.questions).toHaveLength(2)
      expect(result.questions.every((q) => q.tier === "COMPETITIVE_ACCEPT")).toBe(true)
      expect(result.realizedSummary.competitiveCount).toBe(2)
      expect(result.realizedSummary.coverageCount).toBe(0)
    }
  })

  it("filtra por preguntas falladas con historial", () => {
    const progressWithErrors = new Map<string, QuestionProgress>([
      [
        "PR-39-1",
        {
          questionKey: "PR-39-1",
          timesSeen: 2,
          timesCorrect: 0,
          timesIncorrect: 2,
          timesUnanswered: 0,
          currentCorrectStreak: 0,
          averageResponseTimeMs: 4000,
          bestResponseTimeMs: null,
          lastResponseTimeMs: 4000,
          lastSeenAt: Date.now(),
          masteryScore: 0,
          favorite: false,
          markedDifficult: false,
          reported: false,
          history: [],
        },
      ],
    ])

    const config: SessionConfig = {
      mode: "learn",
      count: 1,
      sourceWorks: ["Daniel", "Profetas y Reyes"],
      chapters: [],
      difficulties: [1, 2, 3, 4, 5],
      types: ["single_choice", "fill_blank", "true_false"],
      statuses: ["failed"],
      shuffleQuestions: true,
      shuffleOptions: true,
      perQuestionSeconds: null,
      totalSeconds: null,
      tierFilter: "all",
    }

    const result = selectManualSession(pool, config, progressWithErrors, 42)
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.questions).toHaveLength(1)
      expect(result.questions[0].id).toBe("PR-39-1")
    }
  })

  it("se ajusta al inventario disponible registrando el déficit cuando se solicitan más de las existentes", () => {
    const config: SessionConfig = {
      mode: "learn",
      count: 25,
      sourceWorks: ["Daniel", "Profetas y Reyes"],
      chapters: [43],
      difficulties: [1, 2, 3, 4, 5],
      types: ["single_choice", "fill_blank", "true_false"],
      statuses: ["all"],
      shuffleQuestions: true,
      shuffleOptions: true,
      perQuestionSeconds: null,
      totalSeconds: null,
      tierFilter: "all",
    }

    const result = selectManualSession(pool, config, emptyProgress, 42)
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.questions).toHaveLength(1)
      expect(result.quotaShortfalls["disponibles"]).toBe(24)
    }
  })

  it("calcula conteos facetados exactos que coinciden con los seleccionables", () => {
    const config: SessionConfig = {
      mode: "learn",
      count: 10,
      sourceWorks: ["Profetas y Reyes"],
      chapters: [],
      difficulties: [1, 2, 3, 4, 5],
      types: ["single_choice", "fill_blank", "true_false"],
      statuses: ["all"],
      shuffleQuestions: true,
      shuffleOptions: true,
      perQuestionSeconds: null,
      totalSeconds: null,
      tierFilter: "all",
    }

    const counts = computeFacetedCounts(config, emptyProgress, pool)
    expect(counts.totalEligible).toBe(2)
    expect(counts.prEligible).toBe(2)
    expect(counts.danielEligible).toBe(0)
    expect(counts.chapterCounts["PR39"]).toBe(1)
    expect(counts.chapterCounts["PR43"]).toBe(1)
  })

  it("no convierte dificultad en estado de auditoría", () => {
    const unverified = mockQuestion({ id: "HARD-NOT-AUDITED", difficultyBand: "HARD" })
    delete unverified.tier
    const config: SessionConfig = {
      mode: "learn",
      count: 1,
      sourceWorks: [],
      chapters: [],
      difficulties: [1, 2, 3, 4, 5],
      types: [],
      statuses: ["all"],
      shuffleQuestions: false,
      shuffleOptions: false,
      perQuestionSeconds: null,
      totalSeconds: null,
      tierFilter: "coverage",
    }
    expect(selectManualSession([unverified], config, emptyProgress, 1).success).toBe(false)
    expect(computeFacetedCounts(config, emptyProgress, [unverified]).totalEligible).toBe(0)
  })

  it("excluye del catálogo facetado tipos que el selector manual no ofrece", () => {
    const unsupported = mockQuestion({ id: "MULTI-NOT-SUPPORTED", type: "multi_select" })
    const config: SessionConfig = {
      mode: "learn",
      count: 1,
      sourceWorks: ["Profetas y Reyes"],
      chapters: [],
      difficulties: [1, 2, 3, 4, 5],
      types: ["single_choice", "fill_blank", "true_false"],
      statuses: ["all"],
      shuffleQuestions: false,
      shuffleOptions: false,
      perQuestionSeconds: null,
      totalSeconds: null,
      tierFilter: "all",
    }

    expect(computeFacetedCounts(config, emptyProgress, [unsupported]).totalEligible).toBe(0)
  })

  it("el catálogo final expone tier solo para IDs V18 auditados", () => {
    const withTier = FINAL_FILTER_CATALOG.filter((item) => item.tier !== null)
    expect(withTier).toHaveLength(Object.keys(V18_AUDIT_STATUS_BY_ID).length)
    for (const item of withTier) {
      const status = V18_AUDIT_STATUS_BY_ID[item.id]
      expect(item.tier).toBe(
        status === "VERIFIED_COMPETITIVE_SOL"
          ? "COMPETITIVE_ACCEPT"
          : "COVERAGE_ACCEPT",
      )
    }
  })
})
