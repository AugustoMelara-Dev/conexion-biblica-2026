import type { Question } from "@/domain/types"

function randomGenerator(seed: number) {
  let state = seed >>> 0
  return () => ((state = (Math.imul(state, 1103515245) + 12345) >>> 0) / 0x100000000)
}

function shuffle<T>(rows: T[], seed: number) {
  const result = rows.slice()
  const random = randomGenerator(seed)
  for (let index = result.length - 1; index > 0; index -= 1) {
    const swap = Math.floor(random() * (index + 1))
    ;[result[index], result[swap]] = [result[swap], result[index]]
  }
  return result
}

const RELATIONAL_SKILLS = new Set([
  "scene_identification",
  "cause_consequence",
  "comparison",
  "narrative_order",
  "verse_difference",
])

export function selectMandatoryHundred(
  questions: Question[],
  seed: number,
  excludedFacts = new Set<string>(),
) {
  const trueTarget = seed % 2 === 0 ? 13 : 12
  const falseTarget = 25 - trueTarget
  type Bucket = "fill" | "tf_true" | "tf_false" | "mc_trap" | "mc_any"
  const quotas: Array<[Bucket, number]> = [
    ["fill", 30],
    ["tf_true", trueTarget],
    ["tf_false", falseTarget],
    ["mc_trap", 18],
    ["mc_any", 27],
  ]
  const eligible = shuffle(
    questions.filter((item) => !excludedFacts.has(item.factId ?? item.factKey)),
    seed,
  )
  const candidates: Record<Bucket, Question[]> = {
    fill: eligible.filter((item) => item.type === "fill_blank"),
    tf_true: eligible.filter((item) => item.type === "true_false" && item.correctAnswerText === "Verdadero"),
    tf_false: eligible.filter((item) => item.type === "true_false" && item.correctAnswerText === "Falso"),
    mc_trap: eligible.filter((item) => item.type === "single_choice" && item.trapType === "true_elsewhere"),
    mc_any: eligible
      .filter((item) => item.type === "single_choice")
      .sort((left, right) => Number(left.trapType === "true_elsewhere") - Number(right.trapType === "true_elsewhere")),
  }
  const slots = quotas.flatMap(([bucket, count]) =>
    Array.from({ length: count }, (_, index) => ({ id: `${bucket}:${index}`, bucket })),
  ).sort((left, right) => candidates[left.bucket].length - candidates[right.bucket].length)
  const factToSlot = new Map<string, string>()
  const slotToQuestion = new Map<string, Question>()
  const slotById = new Map(slots.map((slot) => [slot.id, slot]))

  const assign = (slotId: string, visitedFacts: Set<string>): boolean => {
    const slot = slotById.get(slotId)!
    for (const question of candidates[slot.bucket]) {
      const fact = question.factId ?? question.factKey
      if (visitedFacts.has(fact)) continue
      visitedFacts.add(fact)
      const priorSlot = factToSlot.get(fact)
      if (priorSlot && !assign(priorSlot, visitedFacts)) continue
      factToSlot.set(fact, slotId)
      slotToQuestion.set(slotId, question)
      return true
    }
    return false
  }

  for (const slot of slots) {
    if (!assign(slot.id, new Set())) {
      throw new Error(`El banco GOLD no alcanza la cuota obligatoria de ${slot.bucket}`)
    }
  }
  const result = [...slotToQuestion.values()]
  const relationalCount = result.filter((item) => RELATIONAL_SKILLS.has(item.semanticSkill ?? "")).length
  if (relationalCount < 10) throw new Error(`El banco GOLD solo aporta ${relationalCount}/10 relaciones o escenas`)
  return shuffle(result, seed ^ 0x5f3759df)
}

export function selectMissionQuestions(input: {
  questions: Question[]
  count: number
  seed: number
  excludedFacts?: Set<string>
}) {
  const excludedFacts = new Set(input.excludedFacts ?? [])
  const eligible = input.questions.filter((question) =>
    question.editorialStatus === "gold" && !question.blindPool
  )
  if (input.count === 100) return selectMandatoryHundred(eligible, input.seed, excludedFacts)

  const used = new Set(excludedFacts)
  const result: Question[] = []
  for (const question of shuffle(eligible, input.seed)) {
    const fact = question.factId ?? question.factKey
    if (used.has(fact)) continue
    used.add(fact)
    result.push(question)
    if (result.length === input.count) break
  }
  return result
}

export function selectBlindSimulation(
  questions: Question[],
  pool: "A" | "B",
  count: number,
  _seed: number,
  excludedFacts = new Set<string>(),
) {
  const used = new Set(excludedFacts)
  const result: Question[] = []
  for (const question of questions) {
    const fact = question.factId ?? question.factKey
    if (question.editorialStatus !== "gold" || question.blindPool !== pool || used.has(fact)) continue
    used.add(fact)
    result.push(question)
    if (result.length === count) break
  }
  return result
}
