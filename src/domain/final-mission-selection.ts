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

export function selectMissionQuestions(input: {
  questions: Question[]
  count: number
  seed: number
  excludedFacts?: Set<string>
}) {
  const used = new Set(input.excludedFacts ?? [])
  const result: Question[] = []
  for (const question of shuffle(input.questions, input.seed)) {
    const fact = question.factId ?? question.factKey
    if (question.editorialStatus !== "gold" || question.blindPool || used.has(fact)) continue
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
