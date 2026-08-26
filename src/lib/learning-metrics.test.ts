import { describe, expect, it } from "vitest"

import { emptyFactMastery } from "@/domain/fact-mastery"
import type { QuestionExposure } from "@/domain/types"
import { buildLearningMetrics } from "@/lib/learning-metrics"

describe("learning evidence metrics", () => {
  it("keeps first attempt, contextual, delayed, next-day and blind evidence separate", () => {
    const mastery = {
      ...emptyFactMastery("DAN7-V19-F01"),
      firstAttemptAttempts: 4,
      firstAttemptCorrect: 3,
      contextualAttempts: 2,
      contextualCorrect: 1,
      sixHourAttempts: 2,
      sixHourCorrect: 2,
      nextDayAttempts: 1,
      nextDayCorrect: 1,
      attempts: 5,
      failures: 2,
    }
    const exposure = {
      evidence: {
        practice: { attempts: 2, correct: 1 },
        cold: { attempts: 1, correct: 1 },
        deferred: { attempts: 1, correct: 1 },
        blind: { attempts: 2, correct: 1 },
      },
    } as QuestionExposure

    expect(buildLearningMetrics([mastery], [exposure])).toEqual({
      firstAttempt: { attempts: 4, correct: 3, accuracy: 75 },
      contextual: { attempts: 2, correct: 1, accuracy: 50 },
      sixHour: { attempts: 2, correct: 2, accuracy: 100 },
      nextDay: { attempts: 1, correct: 1, accuracy: 100 },
      blind: { attempts: 2, correct: 1, accuracy: 50 },
      recurringErrors: 1,
    })
  })
})
