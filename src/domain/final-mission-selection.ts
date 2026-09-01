import type { Question } from "@/domain/types"

function randomGenerator(seed: number) {
  let state = seed >>> 0
  return () =>
    (state = (Math.imul(state, 1103515245) + 12345) >>> 0) / 0x100000000
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

type Bucket =
  | "direct"
  | "relational_direct"
  | "fill"
  | "tf_true"
  | "tf_false"
  | "contextual"

function roundQuotas(
  count: number,
  seed: number
): Array<[Bucket, number]> | null {
  const trueTarget =
    count === 100
      ? seed % 2 === 0
        ? 13
        : 12
      : count === 50
        ? 6
        : count === 20
          ? seed % 2 === 0
            ? 3
            : 2
          : 0
  if (count === 100)
    return [
      ["direct", 17],
      ["relational_direct", 10],
      ["fill", 30],
      ["tf_true", trueTarget],
      ["tf_false", 25 - trueTarget],
      ["contextual", 18],
    ]
  if (count === 50)
    return [
      ["direct", 14],
      ["fill", 15],
      ["tf_true", 6],
      ["tf_false", 6],
      ["contextual", 9],
    ]
  if (count === 20)
    return [
      ["direct", 5],
      ["fill", 6],
      ["tf_true", trueTarget],
      ["tf_false", 5 - trueTarget],
      ["contextual", 4],
    ]
  return null
}

function isCauseOrConsequence(question: Question) {
  return (
    question.semanticSkill === "cause_consequence" ||
    /cause|consequence/.test(String(question.metadata?.relationType ?? ""))
  )
}

export function selectMandatoryRound(
  questions: Question[],
  count: 20 | 50 | 100,
  seed: number,
  excludedFacts = new Set<string>(),
  priorityByFact = new Map<string, number>()
) {
  const quotas = roundQuotas(count, seed)!
  const eligible = shuffle(
    questions.filter((item) => !excludedFacts.has(item.factId ?? item.factKey)),
    seed
  )
  const candidates: Record<Bucket, Question[]> = {
    direct: eligible
      .filter(
        (item) =>
          item.family === "single_choice_direct" ||
          (!item.family &&
            item.type === "single_choice" &&
            item.trapType !== "true_elsewhere")
      )
      .sort(
        (left, right) =>
          (priorityByFact.get(right.factId ?? right.factKey) ?? 0) -
            (priorityByFact.get(left.factId ?? left.factKey) ?? 0) ||
          Number(isCauseOrConsequence(right)) -
            Number(isCauseOrConsequence(left))
      ),
    relational_direct: eligible
      .filter(
        (item) =>
          (item.family === "single_choice_direct" ||
            (!item.family &&
              item.type === "single_choice" &&
              item.trapType !== "true_elsewhere")) &&
          isCauseOrConsequence(item)
      )
      .sort(
        (left, right) =>
          (priorityByFact.get(right.factId ?? right.factKey) ?? 0) -
          (priorityByFact.get(left.factId ?? left.factKey) ?? 0)
      ),
    fill: eligible
      .filter(
        (item) => item.family === "fill_choice" || item.type === "fill_blank"
      )
      .sort(
        (left, right) =>
          (priorityByFact.get(right.factId ?? right.factKey) ?? 0) -
          (priorityByFact.get(left.factId ?? left.factKey) ?? 0)
      ),
    tf_true: eligible
      .filter(
        (item) =>
          (item.family === "true_false" || item.type === "true_false") &&
          item.correctAnswerText === "Verdadero"
      )
      .sort(
        (left, right) =>
          (priorityByFact.get(right.factId ?? right.factKey) ?? 0) -
          (priorityByFact.get(left.factId ?? left.factKey) ?? 0)
      ),
    tf_false: eligible
      .filter(
        (item) =>
          (item.family === "true_false" || item.type === "true_false") &&
          item.correctAnswerText === "Falso"
      )
      .sort(
        (left, right) =>
          (priorityByFact.get(right.factId ?? right.factKey) ?? 0) -
          (priorityByFact.get(left.factId ?? left.factKey) ?? 0)
      ),
    contextual: eligible
      .filter(
        (item) =>
          item.family === "single_choice_contextual" ||
          (!item.family &&
            item.type === "single_choice" &&
            item.trapType === "true_elsewhere")
      )
      .sort(
        (left, right) =>
          (priorityByFact.get(right.factId ?? right.factKey) ?? 0) -
          (priorityByFact.get(left.factId ?? left.factKey) ?? 0)
      ),
  }
  const slots = quotas
    .flatMap(([bucket, quota]) =>
      Array.from({ length: quota }, (_, index) => ({
        id: `${bucket}:${index}`,
        bucket,
      }))
    )
    .sort(
      (left, right) =>
        candidates[left.bucket].length - candidates[right.bucket].length
    )
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
    if (!assign(slot.id, new Set()))
      throw new Error(
        `El banco GOLD no alcanza la cuota obligatoria de ${slot.bucket}`
      )
  }
  const result = [...slotToQuestion.values()]
  if (
    count === 100 &&
    result.some((question) => question.family !== undefined) &&
    result.filter(isCauseOrConsequence).length < 10
  )
    throw new Error(
      "El banco GOLD no alcanza 10 preguntas de causa o consecuencia"
    )
  return shuffle(result, seed ^ 0x5f3759df)
}

export function selectMandatoryHundred(
  questions: Question[],
  seed: number,
  excludedFacts = new Set<string>()
) {
  return selectMandatoryRound(questions, 100, seed, excludedFacts)
}

export function selectMissionQuestions(input: {
  questions: Question[]
  count: number
  seed: number
  difficultyBands?: readonly ("BASIC" | "MEDIUM" | "HARD" | "EXPERT" | "UNRATED")[]
  tier?: "COMPETITIVE_ACCEPT" | "COVERAGE_ACCEPT"
  excludedFacts?: Set<string>
}) {
  const excludedFacts = new Set(input.excludedFacts ?? [])
  const bands = input.difficultyBands ? new Set(input.difficultyBands) : null
  const requiredTier = input.tier ?? null

  const eligible = input.questions.filter((question) => {
    if (question.editorialStatus !== "gold" || question.blindPool) return false
    if (question.metadata?.provisional) return false

    const qTier = question.tier ?? (question.metadata?.tier as any)

    if (requiredTier && qTier !== requiredTier) return false

    if (bands) {
      if (bands.has("HARD") || bands.has("EXPERT")) {
        if (qTier === "COVERAGE_ACCEPT") return false
      }
      if (question.difficultyBand && !bands.has(question.difficultyBand)) return false
      if (!question.difficultyBand && question.difficulty !== undefined) {
        if (question.difficulty < 4 && (bands.has("HARD") || bands.has("EXPERT"))) return false
      }
    }

    return true
  })

  if (input.count === 20 || input.count === 50 || input.count === 100)
    return selectMandatoryRound(
      eligible,
      input.count,
      input.seed,
      excludedFacts
    )

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
  excludedFacts = new Set<string>()
) {
  const used = new Set(excludedFacts)
  const result: Question[] = []
  for (const question of questions) {
    const fact = question.factId ?? question.factKey
    if (
      question.editorialStatus !== "gold" ||
      question.blindPool !== pool ||
      used.has(fact)
    )
      continue
    used.add(fact)
    result.push(question)
    if (result.length === count) break
  }
  return result
}
