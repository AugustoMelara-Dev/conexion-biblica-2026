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
