import { readFileSync, writeFileSync } from "node:fs"
import { join } from "node:path"
import { naturalizePrompt } from "./lib/editorial.mjs"

const root = process.cwd()
const master = JSON.parse(readFileSync(join(root, "Banco_Maestro_CB2026.json"), "utf8")).questions
const canonicalCorrections = new Map([
  ["HIST-0163", { optionId: "A", text: "Beltsasar" }],
])

function stripPrefix(value) {
  return String(value ?? "").trim().replace(/^[A-D]\)\s*/i, "").replace(/\.{2,}$/g, ".")
}

function comparable(value) {
  return stripPrefix(value).normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[.。]+$/g, "").trim().toLocaleLowerCase("es")
}

function typeOf(value) {
  const type = String(value).replace(/\s+/g, " ").trim().toLocaleUpperCase("es")
  if (type.startsWith("VERDADERO")) return "true_false"
  if (type.startsWith("COMPLET") || type === "RESPUESTA CORTA") return "fill_blank"
  return "single_choice"
}

function difficultyOf(value) {
  return value === "EXPERT" ? 5 : value === "HARD" ? 4 : value === "MEDIUM" ? 3 : 3
}

function primaryFact(item) {
  return item.FULL_FACT_IDS?.[0] ?? item.PARTIAL_FACT_IDS?.[0] ?? item.INCIDENTAL_FACT_IDS?.[0] ?? (item.duplicate_group || item.QUESTION_ID)
}

function optionsAndAnswer(item, type) {
  if (type === "true_false") {
    const answer = comparable(item.respuesta_correcta)
    if (answer !== "verdadero" && answer !== "falso") return null
    return {
      options: [{ id: "TRUE", text: "Verdadero" }, { id: "FALSE", text: "Falso" }],
      correctAnswer: [answer === "verdadero" ? "TRUE" : "FALSE"],
    }
  }

  const options = ["A", "B", "C", "D"].map((id) => ({ id, text: stripPrefix(item[id]) })).filter((option) => option.text)
  if (type === "fill_blank" && options.length === 0) {
    const answer = stripPrefix(item.respuesta_correcta)
    if (!answer) return null
    return { options: [{ id: "ANSWER", text: answer }], correctAnswer: ["ANSWER"], answerMode: "canonical_text", correctAnswerText: answer }
  }
  const leadingId = String(item.respuesta_correcta).trim().match(/^([A-D])\)/i)?.[1]?.toUpperCase()
  const answer = comparable(item.respuesta_correcta)
  const optionId = leadingId && options.some((option) => option.id === leadingId)
    ? leadingId
    : options.find((option) => comparable(option.text) === answer)?.id
  if (!optionId || options.length < 2) return null
  return {
    options,
    correctAnswer: [optionId],
    ...(type === "fill_blank" ? { answerMode: "canonical_text", correctAnswerText: options.find((option) => option.id === optionId)?.text } : {}),
  }
}

function quality(item) {
  return (item.estado_QC === "PASS_10_10" ? 100 : 0) + (item.historical_status === "VERIFIED_CORRECT" || item.historical_status === "CORRECTED" ? 80 : 0) + (item.fact_support ? 20 : 0) + (item.origen === "GENERATED" ? 5 : 0)
}

function adapt(item, id) {
  const type = typeOf(item.tipo)
  const answer = optionsAndAnswer(item, type)
  if (!answer) return null
  const correction = canonicalCorrections.get(item.QUESTION_ID)
  if (correction) {
    answer.options = answer.options.map((option) => option.id === correction.optionId ? { ...option, text: correction.text } : option)
    if (answer.correctAnswerText !== undefined) answer.correctAnswerText = correction.text
  }
  const work = item.material === "DANIEL" ? "Daniel" : "Profetas y Reyes"
  const answerText = answer.correctAnswerText ?? answer.options.find((option) => option.id === answer.correctAnswer[0])?.text ?? stripPrefix(item.respuesta_correcta)
  const fact = primaryFact(item)
  return {
    id,
    type,
    difficulty: difficultyOf(item.dificultad),
    source: { work, version: item.material === "DANIEL" ? "RVR95" : "Material PDF", chapter: Number(item.capitulo), reference: item.fuente },
    tags: ["v3", String(item.habilidad || "detalle"), String(item.riesgo_objetivo || "MEDIUM").toLocaleLowerCase("es")],
    factKey: fact,
    factKeys: [...new Set([...(item.FULL_FACT_IDS ?? []), ...(item.PARTIAL_FACT_IDS ?? [])])],
    question: naturalizePrompt(item.pregunta),
    ...answer,
    explanation: item.fact_support
      ? `Dato verificado en ${item.fuente}: ${String(item.fact_support).replace(/[.。]+$/g, "")}.`
      : /pregunta hist[oó]rica|fase\s*[1234]|cobertura auditada/i.test(item.explicacion ?? "")
        ? `La respuesta se confirma directamente en ${item.fuente}.`
        : String(item.explicacion || `La respuesta se verifica en ${item.fuente}.`).trim(),
    trapReason: `No confundas este dato con otros del mismo capítulo; la precisión depende de ${item.fuente}.`,
    memoryCue: `Ancla ${item.fuente}: ${String(item.fact_support || answerText).replace(/[.。]+$/g, "")}.`,
    verified: true,
    metadata: { masterQuestionId: item.QUESTION_ID, qc: item.estado_QC, skill: item.habilidad },
  }
}

function choose(material, chapter, quota, prefix, usedPrompts) {
  const eligible = master
    .filter((item) => item.material === material && Number(item.capitulo) === chapter)
    .sort((left, right) => quality(right) - quality(left) || left.QUESTION_ID.localeCompare(right.QUESTION_ID))
  const families = new Map()
  const chapterPrompts = new Set()
  for (const item of eligible) {
    const prompt = comparable(item.pregunta)
    if (!prompt || usedPrompts.has(prompt) || chapterPrompts.has(prompt)) continue
    const adapted = adapt(item, "pending")
    if (!adapted) continue
    const key = primaryFact(item)
    const family = families.get(key) ?? []
    if (!family.some((candidate) => comparable(candidate.pregunta) === prompt)) family.push(item)
    families.set(key, family)
    chapterPrompts.add(prompt)
  }
  const groups = [...families.values()].sort((left, right) => Math.min(right.length, 2) - Math.min(left.length, 2) || quality(right[0]) - quality(left[0]))
  const selected = []
  for (const group of groups) {
    if (selected.length + 2 > quota || group.length < 2) continue
    selected.push(group[0], group[1])
    if (selected.length === quota) break
  }
  if (selected.length < quota) {
    for (const group of groups) {
      for (const item of group) {
        if (selected.includes(item)) continue
        selected.push(item)
        if (selected.length === quota) break
      }
      if (selected.length === quota) break
    }
  }
  if (selected.length !== quota) throw new Error(`${material} ${chapter}: se encontraron ${selected.length} de ${quota}`)
  return selected.map((item, index) => {
    usedPrompts.add(comparable(item.pregunta))
    return adapt(item, `${prefix}${String(chapter).padStart(2, "0")}-${String(index + 1).padStart(3, "0")}`)
  })
}

const usedPrompts = new Set()
const daniel = Array.from({ length: 12 }, (_, index) => choose("DANIEL", index + 1, 28, "V3-D", usedPrompts)).flat()
const prophets = Array.from({ length: 6 }, (_, index) => choose("PR", index + 39, 27, "V3-PR", usedPrompts)).flat()

const integrative = [
  {
    id: "V3-INT-001", type: "single_choice", difficulty: 4, integrative: true,
    source: { work: "Daniel", version: "RVR95 + Material PDF", chapter: 1, reference: "Daniel 1:8; Profetas y Reyes 39" },
    tags: ["v3", "integradora", "causa-efecto"], factKey: "INT-D01-PR39-PROPOSITO",
    question: "¿Qué decisión de Daniel enlaza el relato bíblico de Daniel 1 con la explicación de Profetas y Reyes 39?",
    options: [{ id: "A", text: "Pedir un cargo militar" }, { id: "B", text: "No contaminarse con la comida y el vino del rey" }, { id: "C", text: "Interpretar de inmediato el sueño del rey" }, { id: "D", text: "Regresar secretamente a Jerusalén" }],
    correctAnswer: ["B"], explanation: "Daniel 1:8 registra el propósito de no contaminarse, y Profetas y Reyes 39 desarrolla la fidelidad de los jóvenes en esa prueba.",
    trapReason: "Otros episodios pertenecen a capítulos posteriores de Daniel.", memoryCue: "Daniel 1 + PR39: propósito firme frente a la mesa del rey.", verified: true,
  },
  {
    id: "V3-INT-002", type: "single_choice", difficulty: 4, integrative: true,
    source: { work: "Daniel", version: "RVR95 + Material PDF", chapter: 5, reference: "Daniel 5:1; Profetas y Reyes 43" },
    tags: ["v3", "integradora", "comparacion"], factKey: "INT-D05-PR43-BANQUETE",
    question: "¿Qué detalle comparten Daniel 5 y Profetas y Reyes 43 al presentar la última noche de Babilonia?",
    options: [{ id: "A", text: "Darío convocó a ciento veinte sátrapas" }, { id: "B", text: "Belsasar ofreció un banquete a mil de sus príncipes" }, { id: "C", text: "Nabucodonosor levantó una estatua de oro" }, { id: "D", text: "Ciro ordenó reconstruir el templo durante el banquete" }],
    correctAnswer: ["B"], explanation: "Daniel 5:1 y el capítulo 43 describen el banquete de Belsasar para mil de sus príncipes.",
    trapReason: "Los demás datos pertenecen a otros momentos del material.", memoryCue: "Daniel 5 + PR43: Belsasar, banquete y mil príncipes.", verified: true,
  },
]

const common = { schemaVersion: "1.0" }
const danielDocument = {
  ...common,
  bank: { competition: "Conexion Biblica 2026", profileId: "prep-v3", sourceWork: "Daniel", sourceVersion: "RVR95", chapter: "1-12", description: "Banco V3 por familias para Daniel 1-12" },
  questions: [...daniel, ...integrative],
}
const prophetsDocument = {
  ...common,
  bank: { competition: "Conexion Biblica 2026", profileId: "prep-v3", sourceWork: "Profetas y Reyes", sourceVersion: "Material PDF", chapter: "39-44", description: "Banco V3 por familias para Profetas y Reyes 39-44" },
  questions: prophets,
}

writeFileSync(join(root, "public/banks/v3_daniel.json"), `${JSON.stringify(danielDocument, null, 2)}\n`)
writeFileSync(join(root, "public/banks/v3_profetas_reyes.json"), `${JSON.stringify(prophetsDocument, null, 2)}\n`)
console.log(`Generadas ${danielDocument.questions.length + prophetsDocument.questions.length} preguntas V3.`)
