import fs from "node:fs"
import path from "node:path"
import { selectMissionQuestions } from "../src/domain/final-mission-selection"
import { adaptFinalQuestion, type FinalRawQuestion } from "../src/storage/final-bank"
import type { Question } from "../src/domain/types"

const ROOT = path.resolve(".")
const SHARDS_DIR = path.join(ROOT, "public", "banks", "final-2026", "questions")
const OUT_DIR = path.join(ROOT, "content", "competitive-v13", "waves", "wave2", "closeout")

const EXPECTED_UNITS = [
  ...Array.from({ length: 12 }, (_, i) => `DAN${i + 1}`),
  ...Array.from({ length: 6 }, (_, i) => `PR${i + 39}`),
]

async function runSimulation() {
  if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true })

  const rawQuestions: FinalRawQuestion[] = []
  for (const unit of EXPECTED_UNITS) {
    const filePath = path.join(SHARDS_DIR, `${unit}.json`)
    const fileContent = fs.readFileSync(filePath, "utf-8")
    const rows = JSON.parse(fileContent) as FinalRawQuestion[]
    rawQuestions.push(...rows)
  }

  console.log(`Loaded ${rawQuestions.length} raw questions.`)
  const adaptedQuestions: Question[] = rawQuestions.map(adaptFinalQuestion)
  console.log(`Adapted ${adaptedQuestions.length} questions.`)

  const signatures = new Set<string>()
  const sessionRecords = []
  let totalCoverageLeaks = 0
  let totalDuplicateFacts = 0
  let totalOptionShuffleMismatches = 0
  let totalProvisionalIncluded = 0

  for (let seed = 0; seed < 1000; seed += 1) {
    const selected = selectMissionQuestions({
      questions: adaptedQuestions,
      count: 100,
      seed,
      difficultyBands: ["HARD", "EXPERT"],
    })

    const facts = selected.map((q) => q.factId!)
    const uniqueFacts = new Set(facts)

    if (uniqueFacts.size !== selected.length) totalDuplicateFacts += 1

    for (const q of selected) {
      if (q.tier === "COVERAGE_ACCEPT") totalCoverageLeaks += 1
      if (q.metadata?.provisional === true) totalProvisionalIncluded += 1
      if (q.difficultyBand !== "HARD" && q.difficultyBand !== "EXPERT") totalCoverageLeaks += 1

      // Verify option shuffling preservation
      const rawMatch = rawQuestions.find((r) => r.id === q.id)
      if (rawMatch && rawMatch.correct_answer !== q.correctAnswerText) {
        totalOptionShuffleMismatches += 1
      }
    }

    const signature = facts.slice().sort().join("|")
    signatures.add(signature)

    if (seed < 10 || seed === 999) {
      sessionRecords.push({
        seed,
        selected_count: selected.length,
        unique_facts_count: uniqueFacts.size,
        difficulty_distribution: {
          HARD: selected.filter((q) => q.difficultyBand === "HARD").length,
          EXPERT: selected.filter((q) => q.difficultyBand === "EXPERT").length,
        },
        signature_prefix: signature.slice(0, 32),
      })
    }
  }

  console.log(`\n--- REAL SELECTOR SIMULATION REPORT (1,000 SEEDS) ---`)
  console.log(`Total seeds executed: 1,000`)
  console.log(`Total distinct fact signatures: ${signatures.size} (>= 900 required)`)
  console.log(`Coverage leaks in Hard/Expert: ${totalCoverageLeaks}`)
  console.log(`Duplicate facts in any session: ${totalDuplicateFacts}`)
  console.log(`Provisional questions included: ${totalProvisionalIncluded}`)
  console.log(`Option shuffle mismatches: ${totalOptionShuffleMismatches}`)

  const report = {
    contract: "CB2026_REAL_SELECTOR_SIMULATION_REPORT_V1",
    total_seeds: 1000,
    distinct_signatures: signatures.size,
    distinct_signatures_target_met: signatures.size >= 900,
    coverage_leaks_in_hard_expert: totalCoverageLeaks,
    duplicate_facts_in_sessions: totalDuplicateFacts,
    provisional_included: totalProvisionalIncluded,
    option_shuffle_mismatches: totalOptionShuffleMismatches,
    simulation_passed: (
      signatures.size >= 900 &&
      totalCoverageLeaks === 0 &&
      totalDuplicateFacts === 0 &&
      totalProvisionalIncluded === 0 &&
      totalOptionShuffleMismatches === 0
    ),
    sample_sessions: sessionRecords,
  }

  const outPath = path.join(OUT_DIR, "real-selector-simulation-report.json")
  fs.writeFileSync(outPath, JSON.stringify(report, null, 2), "utf-8")
  console.log(`Saved simulation report to ${outPath}`)
}

runSimulation().catch((err) => {
  console.error("Simulation failed:", err)
  process.exit(1)
})
