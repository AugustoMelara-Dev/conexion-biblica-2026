import { createHash } from "node:crypto"

function familyMatches(row, family) {
  if (family === "true_false_false")
    return row.family === "true_false" && row.correct_answer === "Falso"
  return row.family === family
}

function deterministicRank(row) {
  return createHash("sha256").update(String(row.id)).digest("hex")
}

export function buildCompetitiveAuditReport({
  bank,
  bankQuestions,
  chapters,
  families,
  perStratum,
  automaticFlags,
  sample,
}) {
  return {
    bank,
    bank_questions: bankQuestions,
    sample_size: sample.length,
    design: {
      chapters,
      families,
      per_stratum: perStratum,
      strata: chapters.length * families.length,
    },
    automatic_flags: automaticFlags,
    sample,
  }
}

export function selectStratifiedSample(
  rows,
  { chapters, families, perStratum }
) {
  const selected = []
  for (const chapter of chapters) {
    for (const family of families) {
      const stratum = rows
        .filter((row) => row.chapter === chapter && familyMatches(row, family))
        .sort((left, right) =>
          deterministicRank(left).localeCompare(deterministicRank(right))
        )
      if (stratum.length < perStratum)
        throw new Error(
          `Estrato insuficiente ${chapter}/${family}: ${stratum.length}/${perStratum}`
        )
      selected.push(...stratum.slice(0, perStratum))
    }
  }
  return selected
}

export function semanticAuditFlags(row) {
  const flags = []
  const options = Array.isArray(row.options) ? row.options : []
  if (options[row.correct_option] !== row.correct_answer)
    flags.push("answer_index_mismatch")
  if (
    row.family !== "true_false" &&
    !String(row.source_quote ?? "").includes(String(row.correct_answer ?? ""))
  )
    flags.push("answer_not_in_source_quote")
  if (row.family === "fill_choice") {
    const blanks = String(row.question ?? "").match(/_{4,}/g) ?? []
    if (blanks.length !== 1) flags.push("invalid_blank_count")
  }
  if (row.family === "true_false" && row.correct_answer === "Falso") {
    if (!row.incorrect_detail) flags.push("missing_incorrect_detail")
    if (!row.correction) flags.push("missing_correction")
    if (!row.corrected_statement) flags.push("missing_corrected_statement")
    if (
      row.correction &&
      !String(row.source_quote ?? "")
        .toLocaleLowerCase("es")
        .includes(String(row.correction).toLocaleLowerCase("es"))
    )
      flags.push("correction_not_in_source_quote")
  }
  if (row.family === "single_choice_contextual") {
    if (row.trap_type !== "true_in_other_context")
      flags.push("missing_contextual_trap")
    if (Object.keys(row.why_distractors_fail ?? {}).length !== 3)
      flags.push("incomplete_distractor_explanations")
  }
  return flags
}

function normalizeText(value) {
  return String(value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("es")
    .replace(/\s+/g, " ")
    .trim()
}

export function exhaustiveRiskFlags(row) {
  const flags = [...semanticAuditFlags(row)]
  const options = Array.isArray(row.options) ? row.options : []
  const normalizedOptions = options.map(normalizeText)
  if (new Set(normalizedOptions).size !== normalizedOptions.length)
    flags.push("duplicate_normalized_option")
  if (normalizedOptions.some((option) => option.length === 0))
    flags.push("empty_option")

  if (row.family === "single_choice_contextual") {
    const explanations = Object.values(row.why_distractors_fail ?? {}).map(
      String
    )
    const sourceReferencePattern =
      /(?:Daniel\s+\d{1,2}:\d{1,2}|(?:PR|Profetas y Reyes)\s*\d{1,2}(?:\s*,?\s*(?:p\.|párrafo)\s*\d+)?)/iu
    if (
      explanations.length !== 3 ||
      explanations.some(
        (explanation) => !sourceReferencePattern.test(explanation)
      )
    )
      flags.push("contextual_distractor_without_source_reference")
    if (
      Array.isArray(row.option_slot_signatures) &&
      new Set(row.option_slot_signatures).size !== 1
    )
      flags.push("contextual_slot_signature_mismatch")
  }

  if (
    row.family === "true_false" &&
    row.correct_answer === "Falso" &&
    normalizeText(row.statement ?? row.question).includes(
      "aparece la expresion"
    )
  )
    flags.push("deprecated_generic_false_wording")

  return [...new Set(flags)]
}

const RISK_WEIGHT = {
  answer_index_mismatch: 100,
  answer_not_in_source_quote: 100,
  invalid_blank_count: 100,
  missing_incorrect_detail: 100,
  missing_correction: 100,
  missing_corrected_statement: 100,
  correction_not_in_source_quote: 100,
  duplicate_normalized_option: 100,
  empty_option: 100,
  missing_contextual_trap: 80,
  incomplete_distractor_explanations: 80,
  contextual_slot_signature_mismatch: 80,
  deprecated_generic_false_wording: 60,
  contextual_distractor_without_source_reference: 40,
}

export function buildExhaustiveReviewQueue(rows) {
  const seen = new Set()
  const queue = rows.map((row) => {
    if (!row?.id || seen.has(row.id))
      throw new Error(`ID de auditoría inválido o duplicado: ${row?.id}`)
    seen.add(row.id)
    const automaticFlags = exhaustiveRiskFlags(row)
    const contentSha256 = createHash("sha256")
      .update(
        JSON.stringify({
          question: row.question ?? null,
          statement: row.statement ?? null,
          options: row.options ?? null,
          correct_option: row.correct_option ?? null,
          correct_answer: row.correct_answer ?? null,
          source_quote: row.source_quote ?? null,
          why_distractors_fail: row.why_distractors_fail ?? null,
        })
      )
      .digest("hex")
    const riskScore = automaticFlags.reduce(
      (sum, flag) => sum + (RISK_WEIGHT[flag] ?? 20),
      row.family === "single_choice_contextual" ? 15 :
        row.family === "true_false" && row.correct_answer === "Falso" ? 12 :
          row.family === "fill_choice" ? 8 : 0
    )
    return {
      id: row.id,
      fact_id: row.fact_id ?? null,
      chapter: row.chapter ?? null,
      family: row.family ?? null,
      reference: row.reference ?? null,
      content_sha256: contentSha256,
      risk_score: riskScore,
      automatic_flags: automaticFlags,
      automatic_status:
        automaticFlags.length === 0 ? "passed" : "requires_attention",
      review_status: "pending_human",
      reviewer: null,
      reviewed_at: null,
      disposition: null,
      notes: null,
    }
  })
  return queue.sort(
    (left, right) =>
      right.risk_score - left.risk_score || left.id.localeCompare(right.id)
  )
}

export function buildPublicReviewIndex(queue, shards) {
  const filesByChapter = new Map(
    shards.map((shard) => [shard.chapter, shard.questions_file])
  )
  return queue.map((row) => {
    const questionsFile = filesByChapter.get(row.chapter)
    if (!questionsFile)
      throw new Error(`No hay shard para la auditoría de ${row.chapter}.`)
    return {
      id: row.id,
      fact_id: row.fact_id,
      chapter: row.chapter,
      family: row.family,
      reference: row.reference,
      content_sha256: row.content_sha256,
      risk_score: row.risk_score,
      automatic_flags: row.automatic_flags,
      automatic_status: row.automatic_status,
      questions_file: questionsFile,
    }
  })
}
