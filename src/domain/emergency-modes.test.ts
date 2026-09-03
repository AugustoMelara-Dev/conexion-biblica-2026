import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  classifyEmergencyQuestion,
  selectEmergencySession,
} from './emergency-modes'
import {
  adaptFinalQuestion,
  type FinalBankManifest,
  type FinalRawQuestion,
} from '@/storage/final-bank'
import type { QuestionProgress } from './types'

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
  it('clasifica las 3,873 preguntas en las 3 categorías canónicas sin pérdida', () => {
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

    expect(competitive).toBe(1040)
    expect(coverage).toBe(2814)
    expect(excluded).toBe(19)
    expect(competitive + coverage + excluded).toBe(3873)
  })

  it('Bloque A: PR39-44 Intensivo entrega exactamente 150 preguntas (25 por capítulo)', () => {
    const progress = new Map<string, QuestionProgress>()
    const result = selectEmergencySession(allQuestions, 'emergency-pr-intensive', progress)

    expect(result.success).toBe(true)
    expect(result.questions).toHaveLength(150)
    expect(result.realizedSummary.prCount).toBe(150)
    expect(result.realizedSummary.danielCount).toBe(0)

    for (let ch = 39; ch <= 44; ch++) {
      expect(result.realizedSummary.chapterCounts[`PR${ch}`]).toBe(25)
    }
  })

  it('Bloque B: Daniel 7-12 Contrastes entrega exactamente 150 preguntas con prioridad en capítulos proféticos', () => {
    const progress = new Map<string, QuestionProgress>()
    const result = selectEmergencySession(allQuestions, 'emergency-daniel-contrast', progress)

    expect(result.success).toBe(true)
    expect(result.questions).toHaveLength(150)
    expect(result.realizedSummary.danielCount).toBe(150)
    expect(result.realizedSummary.prCount).toBe(0)

    expect(result.realizedSummary.chapterCounts['DAN8']).toBeGreaterThanOrEqual(30)
    expect(result.realizedSummary.chapterCounts['DAN9']).toBeGreaterThanOrEqual(35)
    expect(result.realizedSummary.chapterCounts['DAN10']).toBeGreaterThanOrEqual(25)
    expect(result.realizedSummary.chapterCounts['DAN12']).toBeGreaterThanOrEqual(25)
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

  it('Simulación AAH: replica el patrón empírico 100 Qs (~71 Dan / ~29 PR, 77 SC / 23 TF, 20s)', () => {
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
  })

  it('Simulación Escudo Central: entrega 100 Qs (50 PR / 50 Dan 7-12) 100% COMPETITIVE_GOOD', () => {
    const progress = new Map<string, QuestionProgress>()
    const result = selectEmergencySession(allQuestions, 'emergency-escudo-central', progress)

    expect(result.success).toBe(true)
    expect(result.questions).toHaveLength(100)
    expect(result.config.count).toBe(100)
    expect(result.config.mode).toBe('simulation')
    expect(result.config.perQuestionSeconds).toBe(25)

    expect(result.realizedSummary.prCount).toBe(50)
    expect(result.realizedSummary.danielCount).toBe(50)
    expect(result.realizedSummary.competitiveCount).toBe(100)

    for (const q of result.questions) {
      expect(classifyEmergencyQuestion(q)).toBe('COMPETITIVE_GOOD')
      if (q.source.work === 'Daniel') {
        expect(q.source.chapter).toBeGreaterThanOrEqual(7)
      } else {
        expect(q.source.chapter).toBeGreaterThanOrEqual(39)
        expect(q.source.chapter).toBeLessThanOrEqual(44)
      }
    }
  })
})