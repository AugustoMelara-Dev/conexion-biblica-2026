import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  classifyEmergencyQuestion,
  selectEmergencySession,
  VERIFIED_COMPETITIVE_IDS,
} from './emergency-modes'
import { selectAdaptiveSession } from './adaptive-session'
import {
  adaptFinalQuestion,
  type FinalBankManifest,
  type FinalRawQuestion,
} from '@/storage/final-bank'
import type { QuestionProgress } from './types'
import { V18_PACKAGE_COUNTS } from '@/data/final-day-v18'

const root = resolve(import.meta.dirname, '../..')
const bankRoot = resolve(root, 'public/banks/final-2026')
const manifest = JSON.parse(
  readFileSync(resolve(bankRoot, 'manifest.json'), 'utf8')
) as FinalBankManifest

const allQuestions = manifest.shards.flatMap((shard) => {
  const rows = JSON.parse(
    readFileSync(resolve(root, 'public', shard.questions_file), 'utf8')
  ) as FinalRawQuestion[]
  return rows.filter((row) => row.blind_pool === null).map(adaptFinalQuestion)
})

describe('Entrenamiento de Emergencia Final 2026', () => {
  it('solo llama competitivas a preguntas con evidencia V18 real', () => {
    expect(allQuestions).toHaveLength(3873)

    let competitive = 0
    let coverage = 0
    let excluded = 0

    for (const q of allQuestions) {
      const cat = classifyEmergencyQuestion(q)
      if (cat === 'COMPETITIVE_GOOD') competitive++
      else if (cat === 'COVERAGE_GOOD') coverage++
      else if (cat === 'EXCLUDE_EMERGENCY') excluded++
    }

    expect(competitive).toBe(V18_PACKAGE_COUNTS.competitive)
    expect(competitive + coverage + excluded).toBe(3873)
  })

  it('Paquete A carga exactamente el subconjunto V18 verificado disponible', () => {
    const result = selectEmergencySession(
      allQuestions,
      'emergency-last-day-coverage',
      new Map(),
    )
    expect(result.questions).toHaveLength(V18_PACKAGE_COUNTS.coverage)
    expect(result.config.count).toBe(V18_PACKAGE_COUNTS.coverage)
    expect(result.realizedSummary.distinctFacts).toBe(result.questions.length)
  })

  it('Paquete C no incluye preguntas fuera de la reparación V18', () => {
    const result = selectEmergencySession(
      allQuestions,
      'emergency-last-day-repair',
      new Map(),
    )
    expect(result.questions).toHaveLength(V18_PACKAGE_COUNTS.repair)
    expect(result.config.count).toBe(V18_PACKAGE_COUNTS.repair)
  })

  it('Bloque A: PR39-44 Intensivo entrega exactamente 150 preguntas (25 por capítulo) con hechos únicos', () => {
    const progress = new Map<string, QuestionProgress>()
    const result = selectEmergencySession(allQuestions, 'emergency-pr-intensive', progress)

    expect(result.success).toBe(true)
    expect(result.questions).toHaveLength(150)
    expect(result.realizedSummary.prCount).toBe(150)
    expect(result.realizedSummary.danielCount).toBe(0)

    for (let ch = 39; ch <= 44; ch++) {
      expect(result.realizedSummary.chapterCounts[`PR${ch}`]).toBe(25)
    }

    expect(result.realizedSummary.distinctFacts).toBe(150)
  })

  it('Bloque B: Daniel 7-12 Contrastes entrega cuotas exactas (Dan 7: 20, 8: 25, 9: 30, 10: 20, 11: 30, 12: 25) y cero Dan 5', () => {
    const progress = new Map<string, QuestionProgress>()
    const result = selectEmergencySession(allQuestions, 'emergency-daniel-contrast', progress)

    expect(result.success).toBe(true)
    expect(result.questions).toHaveLength(150)
    expect(result.realizedSummary.danielCount).toBe(150)
    expect(result.realizedSummary.prCount).toBe(0)

    expect(result.realizedSummary.chapterCounts['DAN7']).toBe(20)
    expect(result.realizedSummary.chapterCounts['DAN8']).toBe(25)
    expect(result.realizedSummary.chapterCounts['DAN9']).toBe(30)
    expect(result.realizedSummary.chapterCounts['DAN10']).toBe(20)
    expect(result.realizedSummary.chapterCounts['DAN11']).toBe(30)
    expect(result.realizedSummary.chapterCounts['DAN12']).toBe(25)

    expect(result.realizedSummary.chapterCounts['DAN5']).toBeUndefined()
    for (const q of result.questions) {
      expect(q.source.chapter).toBeGreaterThanOrEqual(7)
      expect(q.source.chapter).toBeLessThanOrEqual(12)
    }
  })

  it('Bloque C: Daniel 1-6 Mantenimiento entrega exactamente 50 preguntas únicamente de Dan 1 a 6', () => {
    const progress = new Map<string, QuestionProgress>()
    const result = selectEmergencySession(allQuestions, 'emergency-daniel-maintenance', progress)

    expect(result.success).toBe(true)
    expect(result.questions).toHaveLength(50)
    expect(result.realizedSummary.danielCount).toBe(50)
    expect(result.realizedSummary.prCount).toBe(0)

    for (const q of result.questions) {
      expect(q.source.work).toBe('Daniel')
      expect(q.source.chapter).toBeGreaterThanOrEqual(1)
      expect(q.source.chapter).toBeLessThanOrEqual(6)
    }
  })

  it('Bloque D: Reparar Errores y Dudas incluye las anclas históricas obligatorias de la final', () => {
    const progress = new Map<string, QuestionProgress>()
    const result = selectEmergencySession(allQuestions, 'emergency-personal-repair', progress)

    expect(result.success).toBe(true)
    expect(result.questions.length).toBeGreaterThanOrEqual(2)

    const hasDan926 = result.questions.some(
      (q) => q.source.work === 'Daniel' && q.source.chapter === 9 && q.source.reference.includes('9:26')
    )
    const hasDan121 = result.questions.some(
      (q) => q.source.work === 'Daniel' && q.source.chapter === 12 && q.source.reference.includes('12:1')
    )

    expect(hasDan926).toBe(true)
    expect(hasDan121).toBe(true)
  })

  it('Simulación AAH: replica el patrón empírico 100 Qs (71 Dan / 29 PR, 77 SC / 23 TF, 100 hechos distintos)', () => {
    const progress = new Map<string, QuestionProgress>()
    const result = selectEmergencySession(allQuestions, 'emergency-simulation-aah', progress)

    expect(result.success).toBe(true)
    expect(result.questions).toHaveLength(100)
    expect(result.config.count).toBe(100)
    expect(result.config.mode).toBe('simulation')
    expect(result.config.perQuestionSeconds).toBe(20)

    expect(result.realizedSummary.danielCount).toBe(71)
    expect(result.realizedSummary.prCount).toBe(29)
    expect(result.realizedSummary.scCount).toBe(77)
    expect(result.realizedSummary.tfCount).toBe(23)
    expect(result.realizedSummary.distinctFacts).toBe(100)
  })

  it('Simulación Adversarial usa solamente el subconjunto competitivo V18 disponible', () => {
    const progress = new Map<string, QuestionProgress>()
    const result = selectEmergencySession(allQuestions, 'emergency-adversarial-simulation', progress)

    expect(result.success).toBe(true)
    expect(result.questions).toHaveLength(V18_PACKAGE_COUNTS.competitive)
    expect(result.config.count).toBe(V18_PACKAGE_COUNTS.competitive)
    expect(result.config.mode).toBe('simulation')
    expect(result.config.perQuestionSeconds).toBe(25)

    expect(result.realizedSummary.competitiveCount).toBe(V18_PACKAGE_COUNTS.competitive)
    expect(result.realizedSummary.distinctFacts).toBe(result.questions.length)

    for (const q of result.questions) {
      expect(VERIFIED_COMPETITIVE_IDS.has(q.id)).toBe(true)
      if (q.source.work === 'Daniel') {
        expect(q.source.chapter).toBeGreaterThanOrEqual(7)
      } else {
        expect(q.source.chapter).toBeGreaterThanOrEqual(39)
        expect(q.source.chapter).toBeLessThanOrEqual(44)
      }
    }
  })

  it('falla inmediatamente si un preset emergency-* llega a selectAdaptiveSession', () => {
    expect(() =>
      selectAdaptiveSession({
        questions: allQuestions.slice(0, 50),
        exposures: [],
        count: 50,
        weakChapters: [],
        includeBlind: false,
        seed: 1234,
        presetId: 'emergency-simulation-aah',
      })
    ).toThrowError(/Violation: Emergency preset "emergency-simulation-aah" must never reach selectAdaptiveSession/)
  })

  describe('Rotación de Semilla y Cuotas en Sesiones Consecutivas', () => {
    const seed1 = 20260905
    const seed2 = 20260906

    it('PR Intensivo: conserva 25 por capítulo y al menos 100 de 150 preguntas son diferentes', () => {
      const progress = new Map<string, QuestionProgress>()
      const r1 = selectEmergencySession(allQuestions, 'emergency-pr-intensive', progress, seed1)
      const r2 = selectEmergencySession(allQuestions, 'emergency-pr-intensive', progress, seed2)

      expect(r1.questions).toHaveLength(150)
      expect(r2.questions).toHaveLength(150)

      for (let c = 39; c <= 44; c++) {
        expect(r1.realizedSummary.chapterCounts[`PR${c}`]).toBe(25)
        expect(r2.realizedSummary.chapterCounts[`PR${c}`]).toBe(25)
      }

      const ids1 = new Set(r1.questions.map((q) => q.id))
      const diffCount = r2.questions.filter((q) => !ids1.has(q.id)).length
      expect(diffCount).toBeGreaterThanOrEqual(100)
    })

    it('Daniel Contrastes: conserva cuotas exactas y al menos 100 de 150 preguntas son diferentes', () => {
      const progress = new Map<string, QuestionProgress>()
      const r1 = selectEmergencySession(allQuestions, 'emergency-daniel-contrast', progress, seed1)
      const r2 = selectEmergencySession(allQuestions, 'emergency-daniel-contrast', progress, seed2)

      expect(r1.questions).toHaveLength(150)
      expect(r2.questions).toHaveLength(150)

      const expectedQuotas: Record<number, number> = {
        7: 20,
        8: 25,
        9: 30,
        10: 20,
        11: 30,
        12: 25,
      }

      for (const [ch, count] of Object.entries(expectedQuotas)) {
        expect(r1.realizedSummary.chapterCounts[`DAN${ch}`]).toBe(count)
        expect(r2.realizedSummary.chapterCounts[`DAN${ch}`]).toBe(count)
      }

      const ids1 = new Set(r1.questions.map((q) => q.id))
      const diffCount = r2.questions.filter((q) => !ids1.has(q.id)).length
      expect(diffCount).toBeGreaterThanOrEqual(100)
    })

    it('Simulación AAH: conserva 71/29 y 77/23 y al menos 60 de 100 preguntas son diferentes', () => {
      const progress = new Map<string, QuestionProgress>()
      const r1 = selectEmergencySession(allQuestions, 'emergency-simulation-aah', progress, seed1)
      const r2 = selectEmergencySession(allQuestions, 'emergency-simulation-aah', progress, seed2)

      expect(r1.questions).toHaveLength(100)
      expect(r2.questions).toHaveLength(100)

      expect(r1.realizedSummary.danielCount).toBe(71)
      expect(r1.realizedSummary.prCount).toBe(29)
      expect(r1.realizedSummary.scCount).toBe(77)
      expect(r1.realizedSummary.tfCount).toBe(23)
      expect(r1.realizedSummary.distinctFacts).toBe(100)

      expect(r2.realizedSummary.danielCount).toBe(71)
      expect(r2.realizedSummary.prCount).toBe(29)
      expect(r2.realizedSummary.scCount).toBe(77)
      expect(r2.realizedSummary.tfCount).toBe(23)
      expect(r2.realizedSummary.distinctFacts).toBe(100)

      const ids1 = new Set(r1.questions.map((q) => q.id))
      const diffCount = r2.questions.filter((q) => !ids1.has(q.id)).length
      expect(diffCount).toBeGreaterThanOrEqual(60)
    })

    it('Simulación Adversarial nunca amplía el pool más allá de V18', () => {
      const progress = new Map<string, QuestionProgress>()
      const r1 = selectEmergencySession(allQuestions, 'emergency-adversarial-simulation', progress, seed1)
      const r2 = selectEmergencySession(allQuestions, 'emergency-adversarial-simulation', progress, seed2)

      expect(r1.questions).toHaveLength(V18_PACKAGE_COUNTS.competitive)
      expect(r2.questions).toHaveLength(V18_PACKAGE_COUNTS.competitive)
      expect(r1.realizedSummary.competitiveCount).toBe(V18_PACKAGE_COUNTS.competitive)
      expect(r2.realizedSummary.competitiveCount).toBe(V18_PACKAGE_COUNTS.competitive)

      for (const q of [...r1.questions, ...r2.questions]) {
        expect(VERIFIED_COMPETITIVE_IDS.has(q.id)).toBe(true)
      }

      expect(new Set(r1.questions.map((q) => q.id))).toEqual(
        new Set(r2.questions.map((q) => q.id))
      )
    })

    it('Priorización: selecciona preguntas nunca vistas antes que preguntas vistas hoy', () => {
      const progress = new Map<string, QuestionProgress>()
      const r1 = selectEmergencySession(allQuestions, 'emergency-pr-intensive', progress, seed1)

      // Simular que todas las preguntas de r1 fueron vistas hoy
      const now = Date.now()
      for (const q of r1.questions) {
        progress.set(q.id, {
          questionKey: `local:${q.id}`,
          timesSeen: 1,
          timesCorrect: 1,
          timesIncorrect: 0,
          timesUnanswered: 0,
          currentCorrectStreak: 1,
          averageResponseTimeMs: 3000,
          bestResponseTimeMs: 3000,
          lastResponseTimeMs: 3000,
          lastSeenAt: now,
          masteryScore: 1,
          favorite: false,
          markedDifficult: false,
          reported: false,
          history: [],
        })
      }

      // En la siguiente ronda, el selector debe priorizar las preguntas no vistas
      const r2 = selectEmergencySession(allQuestions, 'emergency-pr-intensive', progress, seed2)
      const seenIds = new Set(r1.questions.map((q) => q.id))
      
      // La gran mayoría deben ser preguntas nuevas
      const newQuestions = r2.questions.filter((q) => !seenIds.has(q.id))
      expect(newQuestions.length).toBeGreaterThanOrEqual(120)
    })
  })
})
