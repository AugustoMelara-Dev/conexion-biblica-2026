import type { Page } from "@playwright/test"

const answersByPage = new WeakMap<
  Page,
  Promise<Record<string, string>>
>()

function canonicalQuestionText(prompt: string) {
  const canonical = prompt.replace(
    /^(Atendiendo al contexto exacto, |Sin trasladar datos de otra escena, |Para distinguir este pasaje de los cercanos, )/,
    "",
  )
  return canonical.charAt(0).toUpperCase() + canonical.slice(1)
}

async function loadCanonicalAnswers(page: Page) {
  let pending = answersByPage.get(page)
  if (!pending) {
    pending = page.evaluate(async () => {
      const manifest = await fetch("/banks/final-2026/manifest.json").then(
        (response) => response.json(),
      )
      const entries = await Promise.all(
        (
          manifest.shards as Array<{ questions_file: string }>
        ).map(async (shard) => {
          const rows = await fetch(`/${shard.questions_file}`).then(
            (response) => response.json(),
          )
          return (rows as Array<{ question: string; correct_answer: string }>).map(
            (row) => [row.question, row.correct_answer] as const,
          )
        }),
      )
      return Object.fromEntries(entries.flat())
    })
    answersByPage.set(page, pending)
  }
  return pending
}

export async function canonicalAnswerForPrompt(page: Page, prompt: string) {
  const answers = await loadCanonicalAnswers(page)
  return answers[canonicalQuestionText(prompt)] ?? null
}
