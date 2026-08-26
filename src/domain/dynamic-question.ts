import type { Question, QuestionOption } from "@/domain/types"

function hash(value: string) {
  let result = 2166136261
  for (let index = 0; index < value.length; index += 1) {
    result ^= value.charCodeAt(index)
    result = Math.imul(result, 16777619)
  }
  return result >>> 0
}

function randomFrom(seed: number) {
  let state = seed >>> 0
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0
    return state / 0x100000000
  }
}

function shuffled<T>(items: readonly T[], random: () => number) {
  const result = items.slice()
  for (let index = result.length - 1; index > 0; index -= 1) {
    const swap = Math.floor(random() * (index + 1))
    ;[result[index], result[swap]] = [result[swap], result[index]]
  }
  return result
}

const CONTROLLED_PREFIXES = [
  "",
  "Atendiendo al contexto exacto, ",
  "Sin trasladar datos de otra escena, ",
  "Para distinguir este pasaje de los cercanos, ",
]

function rewritePrompt(question: string, exposure: number) {
  const prefix = CONTROLLED_PREFIXES[exposure % CONTROLLED_PREFIXES.length]
  if (!prefix) return question
  return `${prefix}${question.charAt(0).toLowerCase()}${question.slice(1)}`
}

export function materializeDynamicQuestion(
  question: Question,
  { seed, exposure }: { seed: number; exposure: number }
): Question {
  const variantSeed = hash(
    `${seed}:${exposure}:${question.variantId ?? question.id}`
  )
  const random = randomFrom(variantSeed)
  const correctTexts = new Set(
    question.options
      .filter((option) => question.correctAnswer.includes(option.id))
      .map((option) => option.text)
  )
  const options: QuestionOption[] = shuffled(question.options, random).map(
    (option, index) => ({ id: String.fromCharCode(65 + index), text: option.text })
  )
  const correctAnswer = options
    .filter((option) => correctTexts.has(option.text))
    .map((option) => option.id)
  return {
    ...question,
    question: rewritePrompt(question.question, exposure),
    options,
    correctAnswer,
    variantId: `${question.variantId ?? question.id}-runtime-${exposure + 1}-${variantSeed.toString(16)}`,
    metadata: {
      ...question.metadata,
      runtimeBaseVariantId: question.variantId ?? question.id,
      runtimeExposure: exposure,
      runtimeSeed: variantSeed,
    },
  }
}
