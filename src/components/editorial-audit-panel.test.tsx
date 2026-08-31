import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, expect, it, vi } from "vitest"

import { EditorialAuditPanel } from "@/components/editorial-audit-panel"

const entries = [
  {
    id: "q1",
    fact_id: "f1",
    chapter: "DAN7",
    family: "single_choice_contextual",
    reference: "Daniel 7:1",
    content_sha256: "hash-q1",
    risk_score: 20,
    automatic_flags: [],
    automatic_status: "passed",
    questions_file: "banks/final-2026/questions/DAN7.json",
  },
  {
    id: "q2",
    fact_id: "f2",
    chapter: "DAN8",
    family: "fill_choice",
    reference: "Daniel 8:1",
    content_sha256: "hash-q2",
    risk_score: 10,
    automatic_flags: [],
    automatic_status: "passed",
    questions_file: "banks/final-2026/questions/DAN8.json",
  },
]

const questions = {
  DAN7: [
    {
      id: "q1",
      question: "¿Qué corresponde a esta escena?",
      options: ["Babilonia", "Jerusalén"],
      correct_answer: "Babilonia",
      source_quote: "Texto fuente de Daniel 7.",
      why_distractors_fail: {
        Jerusalén: "Pertenece a otro contexto.",
      },
    },
  ],
  DAN8: [
    {
      id: "q2",
      question: "Completa la afirmación.",
      options: ["tardes", "reyes"],
      correct_answer: "tardes",
      source_quote: "Texto fuente de Daniel 8.",
      why_distractors_fail: { reyes: "No completa esta frase." },
    },
  ],
}

const schema10ReviewIndex = {
  schema_version: "10.0",
  total_reviewed: 1,
  human_signatures: 0,
  entries: [
    {
      question_id: "Q-DAN1-0001",
      content_sha256: "hash-real",
      decision: "passed",
      reviewer_type: "ai_semantic_audit",
      reviewer: "reviewer-pilot",
    },
  ],
}

const schema10Question = {
  id: "Q-DAN1-0001",
  family: "single_choice_direct",
  chapter: "DAN1",
  reference: "Daniel 1:1",
  question: "¿Qué lugar se indica en Daniel 1:1?",
  options: ["Babilonia", "Jerusalén"],
  correct_answer: "Babilonia",
  source_quote: "Vino Nabucodonosor, rey de Babilonia.",
  why_distractors_fail: {
    Jerusalén: "Es el lugar sitiado, no el reino del rey.",
  },
}

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
  localStorage.clear()
})

it("abre la auditoría con el review-index 10 publicado", async () => {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => ({
    ok: true,
    json: async () =>
      String(input).includes("review-index")
        ? schema10ReviewIndex
        : [schema10Question],
  }))
  vi.stubGlobal("fetch", fetchMock as unknown as typeof fetch)

  render(<EditorialAuditPanel />)

  expect(await screen.findByText(schema10Question.question)).toBeVisible()
  expect(screen.getByText("0 de 1 revisadas")).toBeVisible()
  expect(screen.getByLabelText("Familia").children).toHaveLength(1)
  expect(screen.getByText("single_choice_direct")).toBeVisible()
  expect(screen.getByText("DAN1", { selector: "span" })).toBeVisible()
  expect(screen.getByText(/Daniel 1:1 · Q-DAN1-0001/)).toBeVisible()
  expect(screen.getByText("Riesgo 0")).toBeVisible()
  expect(fetchMock).toHaveBeenNthCalledWith(
    2,
    "/banks/final-2026/questions/DAN1.json"
  )
})

it("muestra un error contractual si el índice está corrupto", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      json: async () => ({
        schema_version: "10.0",
        total_reviewed: 1,
        entries: [{ question_id: null, decision: "passed" }],
      }),
    })) as unknown as typeof fetch
  )

  render(<EditorialAuditPanel />)

  expect(await screen.findByRole("alert")).toHaveTextContent("entrada 1")
  expect(screen.getByText("Auditoría no disponible")).toBeVisible()
  expect(screen.queryByText("Cola completada")).not.toBeInTheDocument()
})

it("muestra un error y no renderiza una pregunta corrupta del shard", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => ({
      ok: true,
      json: async () =>
        String(input).includes("review-index")
          ? schema10ReviewIndex
          : [
              {
                ...schema10Question,
                options: null,
              },
            ],
    })) as unknown as typeof fetch
  )

  render(<EditorialAuditPanel />)

  expect(await screen.findByRole("alert")).toHaveTextContent("pregunta 1")
  expect(screen.queryByText(schema10Question.question)).not.toBeInTheDocument()
  expect(screen.queryByText("Cola completada")).not.toBeInTheDocument()
})

it("conserva el fallo global del índice tras importar decisiones válidas", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      json: async () => ({
        schema_version: "10.0",
        total_reviewed: 1,
        entries: [{ question_id: null, decision: "passed" }],
      }),
    })) as unknown as typeof fetch
  )
  const user = userEvent.setup()
  render(<EditorialAuditPanel />)
  await screen.findByText("Auditoría no disponible")

  await user.upload(
    screen.getByLabelText("Importar decisiones"),
    new File([JSON.stringify([decisionForQ1()])], "decisiones.json", {
      type: "application/json",
    })
  )

  expect(screen.getByText("Auditoría no disponible")).toBeVisible()
  expect(localStorage.getItem("conexion-biblica-human-review-v1")).toContain(
    '"id":"q1"'
  )
})

it("conserva el fallo global del shard junto al error de importación", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => ({
      ok: true,
      json: async () =>
        String(input).includes("review-index")
          ? schema10ReviewIndex
          : [{ ...schema10Question, options: null }],
    })) as unknown as typeof fetch
  )
  const user = userEvent.setup()
  render(<EditorialAuditPanel />)
  await screen.findByText("Auditoría no disponible")

  await user.upload(
    screen.getByLabelText("Importar decisiones"),
    new File(["no-json"], "decisiones.json", { type: "application/json" })
  )

  expect(screen.getByText("Auditoría no disponible")).toBeVisible()
  expect(screen.getByText("No se importaron las decisiones")).toBeVisible()
})

it("muestra el contexto de importación sin afirmar indisponibilidad", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => ({
      ok: true,
      json: async () =>
        String(input).includes("review-index")
          ? schema10ReviewIndex
          : [schema10Question],
    })) as unknown as typeof fetch
  )
  const user = userEvent.setup()
  render(<EditorialAuditPanel />)
  await screen.findByText(schema10Question.question)

  await user.upload(
    screen.getByLabelText("Importar decisiones"),
    new File(["no-json"], "decisiones.json", { type: "application/json" })
  )

  expect(screen.getByText("No se importaron las decisiones")).toBeVisible()
  expect(screen.queryByText("Auditoría no disponible")).not.toBeInTheDocument()
})

it("muestra el contexto de deshacer sin afirmar indisponibilidad", async () => {
  localStorage.setItem(
    "conexion-biblica-human-review-v1",
    JSON.stringify([decisionForQ1()])
  )
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => ({
      ok: true,
      json: async () =>
        String(input).includes("review-index")
          ? { bank_questions: 2, entries }
          : questions.DAN8,
    })) as unknown as typeof fetch
  )
  const user = userEvent.setup()
  render(<EditorialAuditPanel />)
  await screen.findByText("Completa la afirmación.")
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
    throw new DOMException("Quota exceeded", "QuotaExceededError")
  })

  await user.click(
    screen.getByRole("button", { name: "Deshacer última decisión" })
  )

  expect(screen.getByText("No se deshizo la decisión")).toBeVisible()
  expect(screen.queryByText("Auditoría no disponible")).not.toBeInTheDocument()
})

it("exige firma humana, persiste la aprobación y avanza por riesgo", async () => {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input)
    const payload = url.includes("review-index")
      ? { bank_questions: 2, entries }
      : url.includes("DAN7")
        ? questions.DAN7
        : questions.DAN8
    return { ok: true, json: async () => payload } as Response
  })
  vi.stubGlobal("fetch", fetchMock)
  const user = userEvent.setup()
  render(<EditorialAuditPanel />)

  expect(
    await screen.findByText("¿Qué corresponde a esta escena?")
  ).toBeVisible()
  expect(screen.getByText("0 de 2 revisadas")).toBeVisible()
  await user.click(screen.getByRole("button", { name: "Aprobar pregunta" }))
  expect(screen.getByRole("alert")).toHaveTextContent("nombre del revisor")
  expect(screen.getByText("No se guardó la decisión")).toBeVisible()
  expect(screen.queryByText("Auditoría no disponible")).not.toBeInTheDocument()

  await user.type(screen.getByLabelText("Nombre del revisor"), "María")
  await user.click(screen.getByRole("button", { name: "Aprobar pregunta" }))

  expect(await screen.findByText("Completa la afirmación.")).toBeVisible()
  expect(screen.getByText("1 de 2 revisadas")).toBeVisible()
  const stored = JSON.parse(
    localStorage.getItem("conexion-biblica-human-review-v1") ?? "[]"
  )
  expect(stored).toMatchObject([
    {
      id: "q1",
      reviewer: "María",
      disposition: "approved",
      content_sha256: "hash-q1",
    },
  ])
})

it("advierte y no acredita una decisión con huella obsoleta", async () => {
  localStorage.setItem(
    "conexion-biblica-human-review-v1",
    JSON.stringify([
      {
        id: "q1",
        reviewer: "María",
        reviewed_at: "2026-08-28T12:00:00.000Z",
        disposition: "approved",
        notes: "",
        content_sha256: "hash-anterior",
      },
    ])
  )
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => ({
      ok: true,
      json: async () =>
        String(input).includes("review-index")
          ? { bank_questions: 2, entries }
          : questions.DAN7,
    })) as unknown as typeof fetch
  )
  render(<EditorialAuditPanel />)

  await screen.findByText("¿Qué corresponde a esta escena?")
  await waitFor(() =>
    expect(screen.getByRole("alert")).toHaveTextContent(
      "1 decisión corresponde a contenido anterior"
    )
  )
  expect(screen.getByText("0 de 2 revisadas")).toBeVisible()
})

it("mantiene visible un rechazo como defecto abierto", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => ({
      ok: true,
      json: async () =>
        String(input).includes("review-index")
          ? { bank_questions: 2, entries }
          : String(input).includes("DAN7")
            ? questions.DAN7
            : questions.DAN8,
    })) as unknown as typeof fetch
  )
  const user = userEvent.setup()
  render(<EditorialAuditPanel />)
  await screen.findByText("¿Qué corresponde a esta escena?")

  await user.type(screen.getByLabelText("Nombre del revisor"), "María")
  await user.type(
    screen.getByLabelText("Nota editorial"),
    "El distractor no es plausible."
  )
  await user.click(screen.getByRole("button", { name: "Rechazar pregunta" }))

  expect(await screen.findByText("1 rechazo abierto")).toBeVisible()
  expect(screen.getByText("0 aprobadas o corregidas")).toBeVisible()
})

it("permite deshacer la última decisión sin dejar una firma fantasma", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => ({
      ok: true,
      json: async () =>
        String(input).includes("review-index")
          ? { bank_questions: 2, entries }
          : String(input).includes("DAN7")
            ? questions.DAN7
            : questions.DAN8,
    })) as unknown as typeof fetch
  )
  const user = userEvent.setup()
  render(<EditorialAuditPanel />)
  await screen.findByText("¿Qué corresponde a esta escena?")
  await user.type(screen.getByLabelText("Nombre del revisor"), "María")
  await user.click(screen.getByRole("button", { name: "Aprobar pregunta" }))
  await screen.findByText("Completa la afirmación.")

  await user.click(
    screen.getByRole("button", { name: "Deshacer última decisión" })
  )

  expect(
    await screen.findByText("¿Qué corresponde a esta escena?")
  ).toBeVisible()
  expect(screen.getByText("0 de 2 revisadas")).toBeVisible()
  expect(
    JSON.parse(localStorage.getItem("conexion-biblica-human-review-v1") ?? "[]")
  ).toEqual([])
})

it("no avanza ni acredita una firma cuando se agota el almacenamiento", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => ({
      ok: true,
      json: async () =>
        String(input).includes("review-index")
          ? { bank_questions: 2, entries }
          : questions.DAN7,
    })) as unknown as typeof fetch
  )
  const user = userEvent.setup()
  render(<EditorialAuditPanel />)
  await screen.findByText("¿Qué corresponde a esta escena?")
  await user.type(screen.getByLabelText("Nombre del revisor"), "María")
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
    throw new DOMException("Quota exceeded", "QuotaExceededError")
  })

  await user.click(screen.getByRole("button", { name: "Aprobar pregunta" }))

  expect(screen.getByRole("alert")).toHaveTextContent("Quota exceeded")
  expect(screen.getByText("¿Qué corresponde a esta escena?")).toBeVisible()
  expect(screen.getByText("0 de 2 revisadas")).toBeVisible()
})

it("importa decisiones exportadas y continúa desde la primera pendiente", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => ({
      ok: true,
      json: async () =>
        String(input).includes("review-index")
          ? { bank_questions: 2, entries }
          : String(input).includes("DAN7")
            ? questions.DAN7
            : questions.DAN8,
    })) as unknown as typeof fetch
  )
  const user = userEvent.setup()
  render(<EditorialAuditPanel />)
  await screen.findByText("¿Qué corresponde a esta escena?")

  await user.upload(
    screen.getByLabelText("Importar decisiones"),
    new File([JSON.stringify([decisionForQ1()])], "decisiones.json", {
      type: "application/json",
    })
  )

  expect(await screen.findByText("Completa la afirmación.")).toBeVisible()
  expect(screen.getByText("1 de 2 revisadas")).toBeVisible()
})

function decisionForQ1() {
  return {
    id: "q1",
    reviewer: "María",
    reviewed_at: "2026-08-28T12:00:00.000Z",
    disposition: "approved",
    notes: "",
    content_sha256: "hash-q1",
  }
}
