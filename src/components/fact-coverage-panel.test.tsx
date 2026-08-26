import { render, screen } from "@testing-library/react"
import { expect, it } from "vitest"
import { FactCoveragePanel } from "@/components/fact-coverage-panel"
import type { QuestionExposure } from "@/domain/types"

function exposure(
  factId: string,
  variantId: string,
  correct: number,
  incorrect: number,
  averageResponseTimeMs: number
): QuestionExposure {
  return {
    exposureKey: `${factId}:${variantId}`,
    factId,
    variantId,
    questionKey: `massive-v5:${variantId}`,
    exposures: correct + incorrect,
    correct,
    incorrect,
    totalResponseTimeMs: (correct + incorrect) * averageResponseTimeMs,
    averageResponseTimeMs,
    lastSeenAt: 1,
    lastSelectedAnswer: null,
    lastErrorType: incorrect ? "context" : null,
  }
}

it("mide cobertura por hechos únicos y agrega variantes del mismo hecho", () => {
  render(
    <FactCoveragePanel
      totalFacts={2338}
      exposures={[
        exposure("DAN7-F01", "V1", 0, 1, 9200),
        exposure("DAN7-F01", "V2", 1, 1, 8800),
        exposure("PR44-F02", "V1", 2, 0, 3000),
      ]}
    />
  )

  expect(screen.getByText("2 / 2,338 hechos")).toBeInTheDocument()
  expect(screen.getByText("1 débil")).toBeInTheDocument()
  expect(screen.getByText("1 lento")).toBeInTheDocument()
})
