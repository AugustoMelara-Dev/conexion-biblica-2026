# Competitive Bank Full Reauthoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the deployed 12,000-question bank with an entirely AI-authored, source-grounded competitive bank and prove that the real training application works correctly with it.

**Architecture:** Store concise authored records in 18 chapter-owned JSON files under `content/final-2026-authored/`. A new Python compiler validates and enriches those records but never writes question prose or distractors, then publishes the existing sharded interface under `public/banks/final-2026/`. TypeScript continues consuming shards through the current storage adapter, extended for the new subtype and audit metadata. Eight editorial owners author disjoint chapter groups; different reviewers cross-audit them before compilation and deployment.

**Tech Stack:** Python 3 standard library and `unittest`; TypeScript 6; React 19; Vite 8; Vitest 3; Playwright; IndexedDB; Vercel.

**Spec:** `docs/superpowers/specs/2026-08-28-banco-competitivo-reautoria-total-design.md`

## Global Constraints

- The only semantic authorities are Daniel 1–12 in RVR1995 and the supplied local PDF for *Profetas y Reyes* 39–44.
- Web material may guide competitive style but may not supply an answer or interpretation absent from the local sources.
- Question, explanation, and distractor prose must be authored by an AI editor; Python may validate, enrich metadata, compile, and report, but may not generate prose from templates.
- The accepted bank must contain exactly 12,000 source-grounded questions across all 18 units.
- A prompt must be understandable without a visible chapter, verse, page, or paragraph reference.
- Prompts that depend on «Según Daniel…», «Según PR…», «según el párrafo…» or equivalent source-location cues are prohibited.
- False statements may change exactly one local fact and may not transplant a true statement from a different passage.
- A round of 100 must contain exactly 45 selections, 30 completions, and 25 true/false questions without repeating `fact_id`.
- The blind pool must never appear in normal training.
- AI reviews must remain labeled as AI; human signatures remain pending until performed by a person.
- The deployed bank stays unchanged until all replacement artifacts and gates pass locally.
- Preserve unrelated untracked paths: `.playwright-cli/`, `MaterialConexionBiblica (1).pdf`, and `output/playwright/`.

---

### Task 1: Authored-question contract and repository layout

**Files:**
- Create: `content/final-2026-authored/README.md`
- Create: `content/final-2026-authored/questions/.gitkeep`
- Create: `scripts/lib/authored_question.py`
- Create: `scripts/test_authored_question.py`
- Modify: `scripts/lib/final_bank.py`
- Modify: `src/domain/final-bank.ts`
- Modify: `src/storage/final-bank.ts`
- Test: `src/domain/final-bank.test.ts`
- Test: `src/storage/final-bank.test.ts`

**Interfaces:**
- Produces: `validate_authored_question(row: Mapping[str, Any]) -> list[str]`.
- Produces: `load_authored_unit(path: Path) -> list[dict[str, Any]]`.
- Produces: schema version `10.0` with `subtype`, `evidence_excerpt`, and `ai_review` preserved by `adaptFinalQuestion`.
- Consumes: existing `Question`, `FinalQuestionFamily`, and public shard contracts.

- [ ] **Step 1: Write failing Python contract tests**

Add explicit fixtures to `scripts/test_authored_question.py` proving that a valid record passes and that these cases fail with the shown keys: `source_location_prompt`, `missing_evidence`, `answer_not_supported`, `invalid_option_count`, `duplicate_options`, `answer_index_mismatch`, `missing_subtype`, `missing_ai_review`, and `human_signature_claim`.

```python
def test_rejects_source_location_prompt(self):
    row = valid_authored_question()
    row["question"] = "Según Daniel 1:1, ¿quién sitió Jerusalén?"
    self.assertIn("Q-DAN1-0001:source_location_prompt", validate_authored_question(row))

def test_accepts_natural_grounded_prompt(self):
    row = valid_authored_question()
    self.assertEqual(validate_authored_question(row), [])
```

- [ ] **Step 2: Run the narrow Python test and verify red**

Run: `python -m unittest scripts.test_authored_question -v`  
Expected: FAIL because `scripts.lib.authored_question` does not exist.

- [ ] **Step 3: Implement the strict authored record validator**

Define the required keys exactly as:

```python
REQUIRED_KEYS = {
    "id", "source_unit_id", "fact_id", "family", "subtype", "question",
    "options", "correct_option", "correct_answer", "accepted_answers",
    "explanation", "why_distractors_fail", "source_ref", "source_quote",
    "evidence_excerpt", "difficulty", "importance", "relation_type",
    "option_category", "blind_pool", "ai_review",
}
PROHIBITED_PROMPT_PATTERNS = (
    r"^\s*según\s+(?:daniel|pr|profetas\s+y\s+reyes)",
    r"según\s+(?:el\s+)?(?:párrafo|capítulo|versículo|página)",
)
```

`ai_review` must equal `{"status": "passed", "reviewer_type": "ai_semantic_audit", "reviewer": <non-empty string>}` and must not contain a human signature. Require four unique options except two for `true_false`, require `options[correct_option] == correct_answer`, require the normalized correct answer to occur in `source_quote` or `evidence_excerpt`, and reject empty prose fields.

- [ ] **Step 4: Document the canonical JSON shape and ownership rule**

In `content/final-2026-authored/README.md`, include one full non-template example, the complete allowed subtype set, the prohibited prompt rules, the one-fact-change rule for false statements, and the ownership matrix used in Task 4.

- [ ] **Step 5: Extend Python and TypeScript public contracts**

Set `SCHEMA_VERSION` and `FINAL_BANK_SCHEMA_VERSION` to `10.0`. Add these raw fields:

```ts
subtype:
  | "factual_recall" | "speaker_addressee" | "cause_consequence"
  | "narrative_order" | "identification" | "relationship"
  | "text_recall" | "comparison" | "symbol_interpretation"
  | "prophetic_detail" | "principle" | "cross_source_integration"
evidence_excerpt: string
ai_review: {
  status: "passed"
  reviewer_type: "ai_semantic_audit"
  reviewer: string
}
```

Map `subtype` directly to `Question.semanticSkill` and preserve `evidenceExcerpt`, `aiReviewer`, and `aiReviewerType` in `Question.metadata`.

- [ ] **Step 6: Run focused contracts and make them green**

Run: `python -m unittest scripts.test_authored_question scripts.test_final_bank -v`  
Expected: PASS.  
Run: `npm test -- --run src/domain/final-bank.test.ts src/storage/final-bank.test.ts`  
Expected: PASS.

- [ ] **Step 7: Commit the contract**

```bash
git add content/final-2026-authored scripts/lib/authored_question.py scripts/test_authored_question.py scripts/lib/final_bank.py src/domain/final-bank.ts src/storage/final-bank.ts src/domain/final-bank.test.ts src/storage/final-bank.test.ts
git commit -m "feat: define authored competitive question contract"
```

### Task 2: Non-generative compiler and hard quality gates

**Files:**
- Create: `scripts/compile-authored-bank.py`
- Create: `scripts/lib/authored_bank_audit.py`
- Create: `scripts/test_authored_bank_audit.py`
- Modify: `scripts/audit-final-bank-deep.py`
- Modify: `package.json`
- Generate only after all gates pass: `public/banks/final-2026/*.json`
- Generate only after all gates pass: `public/banks/final-2026/questions/*.json`

**Interfaces:**
- Consumes: `load_authored_unit(path)` and all 18 canonical JSON files.
- Produces: `compile_bank(source_dir: Path, output_dir: Path) -> dict[str, Any]`.
- Produces: `audit_authored_bank(rows: Sequence[Mapping[str, Any]]) -> dict[str, list[str]]`.
- Produces: public manifest schema `10.0` compatible with `readFinalManifest`.

- [ ] **Step 1: Write failing audit tests**

Cover exact duplicates, normalized duplicates, repeated `fact_id` family collisions, source-location prompts, answer leaks, nonparallel distractors, two-defensible-option flags, cross-passage false mutations, trivial completion blanks, incorrect total, missing unit, missing family capacity, and an AI review whose hash no longer matches the content.

```python
def test_rejects_cross_passage_false_statement(self):
    rows = [false_question(mutation={"changed_fields": ["source_ref"], "local": False})]
    audit = audit_authored_bank(rows)
    self.assertEqual(audit["cross_passage_false_mutations"], [rows[0]["id"]])
```

- [ ] **Step 2: Run the audit tests and verify red**

Run: `python -m unittest scripts.test_authored_bank_audit -v`  
Expected: FAIL because `authored_bank_audit` does not exist.

- [ ] **Step 3: Implement pure audit functions**

Implement normalization with Unicode NFKD, lowercase, punctuation removal, and whitespace collapse. Produce named violation arrays rather than a single boolean. Require exactly these 18 units:

```python
EXPECTED_UNITS = (
    "DAN1", "DAN2", "DAN3", "DAN4", "DAN5", "DAN6",
    "DAN7", "DAN8", "DAN9", "DAN10", "DAN11", "DAN12",
    "PR39", "PR40", "PR41", "PR42", "PR43", "PR44",
)
```

The compiler must stop with a JSON error report when any violation array is nonempty. It must never import `generate_gold_questions`, `final_editorial`, or any prose-rendering module.

Expose `--source`, `--output`, `--bank`, and repeatable `--authored-unit` CLI arguments. `--authored-unit DAN1` validates only that canonical unit without publishing; `--bank <directory>` audits an already compiled bank without modifying it.

- [ ] **Step 4: Implement deterministic public enrichment**

The compiler may add only deterministic identifiers and fixed metadata: `bank_id`, `bank_name`, `schema_version`, `variant_id`, `template_id: "ai-authored-v1"`, validation status, and content hashes. Copy all prose unchanged from authored files. Write to a temporary output directory, validate it, then replace public artifacts only after success.

- [ ] **Step 5: Update the deep audit to reject legacy mechanisms**

Delete assumptions requiring four mechanical families per fact. Add checks requiring `template_id == "ai-authored-v1"`, no forbidden source-location prompt, `trap_type != "true_in_other_context"`, no `replacement_source_ref`, valid subtype, valid AI review, and matching content hash.

- [ ] **Step 6: Add repository commands and run green**

Add:

```json
"compile:authored": "python scripts/compile-authored-bank.py",
"test:authored": "python -m unittest scripts.test_authored_question scripts.test_authored_bank_audit",
"audit:authored": "python scripts/audit-final-bank-deep.py"
```

Run: `npm run test:authored`  
Expected: PASS.  
Do not run `compile:authored` against the production output until all 18 authored files exist.

- [ ] **Step 7: Commit the compiler and gates**

```bash
git add scripts/compile-authored-bank.py scripts/lib/authored_bank_audit.py scripts/test_authored_bank_audit.py scripts/audit-final-bank-deep.py package.json
git commit -m "feat: compile and audit AI-authored bank"
```

### Task 3: Pilot authoring and reviewer calibration on DAN1

**Files:**
- Create: `content/final-2026-authored/questions/DAN1.json`
- Create: `reports/authored-bank-review/DAN1.json`
- Test: `scripts/test_authored_question.py`

**Interfaces:**
- Consumes: the DAN1 source units from `public/banks/final-2026/source_inventory.json` and the authored contract.
- Produces: exactly 351 accepted DAN1 records using the canonical schema.
- Produces: a review ledger containing `question_id`, `content_sha256`, `decision`, `reviewer_type`, `reviewer`, and `notes`.

- [ ] **Step 1: Add a failing chapter acceptance test**

Add `test_dan1_pilot_has_351_distinct_competitive_questions` that loads `DAN1.json`, validates every row, requires 351 unique IDs and prompts, requires all seven applicable subtypes (`factual_recall`, `speaker_addressee`, `cause_consequence`, `narrative_order`, `identification`, `relationship`, `text_recall`), and finds zero forbidden prompt patterns.

- [ ] **Step 2: Run the DAN1 acceptance test and verify red**

Run: `python -m unittest scripts.test_authored_question.AuthoredUnitAcceptanceTests.test_dan1_pilot_has_351_distinct_competitive_questions -v`  
Expected: FAIL because `DAN1.json` does not exist.

- [ ] **Step 3: Author DAN1 in reviewable batches**

Write records from the exact DAN1 source text. Keep the global visible-family capacity by including selection, completion, and true/false records, but do not force four variants per fact. Every false statement must include:

```json
"false_mutation": {
  "changed_fields": ["person"],
  "local": true,
  "original": "Daniel",
  "replacement": "Misael"
}
```

True statements set `false_mutation` to `null`. Blind records use stable fact-level allocation; ordinary records use `blind_pool: null`.

- [ ] **Step 4: Perform independent semantic review**

The reviewer checks the source without relying on the author's decision, records one ledger entry per question, rejects ambiguity and weak distractors, and sets `ai_review.status` to `passed` only after corrections. The reviewer must not claim human review.

- [ ] **Step 5: Run the pilot gates**

Run: `python -m unittest scripts.test_authored_question -v`  
Expected: PASS with 351/351 DAN1 rows valid.  
Run: `python scripts/audit-final-bank-deep.py --authored-unit DAN1`  
Expected: zero errors.

- [ ] **Step 6: Review the DAN1 diff and commit**

```bash
git add content/final-2026-authored/questions/DAN1.json reports/authored-bank-review/DAN1.json scripts/test_authored_question.py
git commit -m "content: author and review competitive DAN1 bank"
```

### Task 4: Parallel chapter authoring for the remaining 17 units

**Files:**
- Create: `content/final-2026-authored/questions/DAN2.json` through `DAN12.json`
- Create: `content/final-2026-authored/questions/PR39.json` through `PR44.json`
- Create: matching `reports/authored-bank-review/<UNIT>.json` files

**Interfaces:**
- Consumes: canonical schema, source inventory, local PDF, and DAN1 pilot conventions.
- Produces: the exact per-unit accepted counts listed below; total with DAN1 equals 12,000.

Ownership and immutable quotas:

| Owner | Files | Required accepted questions |
|---|---|---:|
| Editor A | `DAN2.json`, `DAN3.json` | 482 + 366 |
| Editor B | `DAN4.json`, `DAN5.json`, `DAN6.json` | 433 + 366 + 364 |
| Editor C | `DAN7.json`, `DAN8.json` | 833 + 871 |
| Editor D | `DAN9.json`, `DAN10.json` | 879 + 543 |
| Editor E | `DAN11.json`, `DAN12.json` | 1,196 + 376 |
| Editor F | `PR39.json`, `PR40.json` | 868 + 799 |
| Editor G | `PR41.json`, `PR42.json` | 751 + 732 |
| Editor H | `PR43.json`, `PR44.json` | 1,001 + 789 |

- [ ] **Step 1: Add failing unit-count and coverage tests**

Parameterize the 17 files and counts above. Require unique IDs, prompts, valid source references, valid evidence, all prose fields nonempty, and at least three applicable semantic subtypes in every unit.

- [ ] **Step 2: Run the full authored acceptance test and verify red**

Run: `python -m unittest scripts.test_authored_question.AuthoredUnitAcceptanceTests -v`  
Expected: FAIL listing each missing unit.

- [ ] **Step 3: Dispatch eight non-overlapping editorial owners**

Each owner edits only the files in their row, states that they are not alone in the repository, preserves other edits, authors from the exact source, and runs the validator against their own units. No owner may modify compiler, runtime, tests, or another owner's files.

- [ ] **Step 4: Require a clean local gate from every owner**

For each unit run:

```powershell
python scripts/audit-final-bank-deep.py --authored-unit DAN2
```

Replace `DAN2` with the unit being checked. Expected: zero errors and the exact quota.

- [ ] **Step 5: Run the aggregate 12,000-row acceptance gate**

Run: `python -m unittest scripts.test_authored_question scripts.test_authored_bank_audit -v`  
Expected: PASS, 18 unit files, exactly 12,000 accepted rows, zero prohibited patterns and zero duplicate prompts.

- [ ] **Step 6: Commit each ownership block separately**

Use one content-only commit per owner, for example:

```bash
git add content/final-2026-authored/questions/DAN2.json content/final-2026-authored/questions/DAN3.json reports/authored-bank-review/DAN2.json reports/authored-bank-review/DAN3.json
git commit -m "content: author competitive DAN2-DAN3 bank"
```

Repeat with the exact files owned by Editors B–H.

### Task 5: Blind cross-review and adversarial correction

**Files:**
- Modify: all `content/final-2026-authored/questions/*.json` only when correcting a recorded defect
- Modify: all `reports/authored-bank-review/*.json`
- Create: `reports/authored-bank-review/cross-review-summary.json`

**Interfaces:**
- Consumes: all 12,000 authored rows and first-pass ledgers.
- Produces: a second content hash and independent `cross_review` decision for every row.
- Produces: zero active blocking findings.

- [ ] **Step 1: Add a failing review-completeness test**

Require every authored question to have a ledger entry whose `content_sha256` matches current content and whose independent reviewer differs from the author.

```python
self.assertNotEqual(entry["author"], entry["cross_reviewer"])
self.assertEqual(entry["cross_review"], "passed")
self.assertEqual(entry["content_sha256"], content_hash(question))
```

- [ ] **Step 2: Run the completeness test and verify red**

Run: `python -m unittest scripts.test_authored_bank_audit.CrossReviewTests -v`  
Expected: FAIL because second-review fields are absent.

- [ ] **Step 3: Rotate reviewers without preserving ownership**

Use this exact rotation: A reviews B, B reviews C, C reviews D, D reviews E, E reviews F, F reviews G, G reviews H, and H reviews A plus DAN1. Reviewers verify source support, answer uniqueness, distractor plausibility, false-statement locality, natural Spanish, and competitive value.

- [ ] **Step 4: Correct and re-review every rejection**

A correction invalidates the previous hash. The original owner corrects it; the cross-reviewer rechecks it and writes the new hash. Do not mark a rejected unchanged row as passed.

- [ ] **Step 5: Run all semantic and adversarial gates**

Run: `npm run test:authored`  
Expected: PASS.  
Run: `npm run audit:authored`  
Expected: zero errors.  
Run: `node scripts/audit-exhaustive-review.mjs --source authored`  
Expected: 12,000 matching review decisions and zero active blockers.

- [ ] **Step 6: Commit the cross-review evidence**

```bash
git add content/final-2026-authored/questions reports/authored-bank-review
git commit -m "content: cross-review all competitive questions"
```

### Task 6: Compile the replacement and validate session composition

**Files:**
- Generate: `public/banks/final-2026/manifest.json`
- Generate: `public/banks/final-2026/questions/*.json`
- Generate: `public/banks/final-2026/editorial_audit.json`
- Generate: `public/banks/final-2026/review-index.json`
- Modify: `src/domain/final-mission-selection.test.ts`
- Modify: `src/storage/final-bank-v8.real.test.ts`
- Modify: `src/storage/endurance.test.ts`

**Interfaces:**
- Consumes: all cross-reviewed canonical records.
- Produces: public schema V10 shards consumed by `loadFinalQuestionPool`.
- Preserves: `selectMandatoryRound(questions, count, seed, excludedFacts, priorityByFact)`.

- [ ] **Step 1: Add failing real-bank distribution tests**

For at least 1,000 deterministic seeds, select 100 questions and assert:

```ts
expect(round).toHaveLength(100)
expect(new Set(round.map((q) => q.factId)).size).toBe(100)
expect(round.filter((q) => q.type === "fill_blank")).toHaveLength(30)
expect(round.filter((q) => q.type === "true_false")).toHaveLength(25)
expect(round.filter((q) => q.type === "single_choice")).toHaveLength(45)
expect(round.some((q) => q.blindFinalPool)).toBe(false)
```

- [ ] **Step 2: Run the real-bank tests and verify red against absent V10 output**

Run: `npm test -- --run src/storage/final-bank-v8.real.test.ts src/domain/final-mission-selection.test.ts`  
Expected: FAIL on schema mismatch or missing V10 artifacts.

- [ ] **Step 3: Compile into a temporary directory and audit**

Run: `python scripts/compile-authored-bank.py --output .tmp/final-2026-v10`  
Expected: 12,000 questions, 18 shards, zero gate failures.  
Run: `python scripts/audit-final-bank-deep.py --bank .tmp/final-2026-v10`  
Expected: zero errors.

- [ ] **Step 4: Publish the locally verified artifacts**

Run: `npm run compile:authored`  
Expected: atomic replacement of `public/banks/final-2026` after validation, with manifest schema `10.0`.

- [ ] **Step 5: Run endurance and distribution tests**

Run: `npm test -- --run src/storage/final-bank-v8.real.test.ts src/storage/endurance.test.ts src/domain/final-mission-selection.test.ts src/domain/session-selection.test.ts`  
Expected: PASS for all seeds, exact mix, no repeated facts, no blind questions.

- [ ] **Step 6: Commit the compiled bank and tests**

```bash
git add public/banks/final-2026 src/domain/final-mission-selection.test.ts src/storage/final-bank-v8.real.test.ts src/storage/endurance.test.ts
git commit -m "feat: publish competitive authored bank v10"
```

### Task 7: Verify spaced learning behavior across consecutive rounds

**Files:**
- Modify only if a failing behavior requires it: `src/storage/final-bank.ts`
- Modify only if a failing behavior requires it: `src/domain/session-selection.ts`
- Modify only if a failing behavior requires it: `src/domain/fact-mastery.ts`
- Test: `src/storage/endurance.test.ts`
- Test: `src/domain/fact-mastery.test.ts`
- Test: `e2e/production-learning-endurance.spec.ts`

**Interfaces:**
- Consumes: V10 questions and existing exposure/mastery state.
- Produces: observable proof that positions and variants change, errors return after separation, immediate correction does not grant mastery, slow facts gain priority, and blind facts remain excluded.

- [ ] **Step 1: Write failing multi-round tests**

Create a deterministic five-round scenario that records one wrong answer, one immediate correction, one slow correct answer, and ordinary correct answers. Assert the wrong fact is absent from the immediate next slot, returns in a later round with another variant, is not mastered after correction, the slow fact outranks unseen neutral repeats, and option order differs across exposures.

- [ ] **Step 2: Run the narrow learning tests and verify their actual state**

Run: `npm test -- --run src/storage/endurance.test.ts src/domain/fact-mastery.test.ts`  
Expected: tests either fail with a specific behavioral defect or pass and document that no runtime change is needed.

- [ ] **Step 3: Fix only demonstrated behavioral defects**

Keep the existing interfaces. Do not refactor unrelated scheduling code. If the test exposes immediate repeat, add a recent-fact exclusion window; if correction grants mastery, require a later separated correct exposure; if option order is stable, shuffle options after adaptation while remapping the correct option ID.

- [ ] **Step 4: Add browser-visible endurance assertions**

In `production-learning-endurance.spec.ts`, answer multiple rounds and inspect displayed question IDs through the existing test hooks. Assert the same five properties and ensure the user can complete every round without an unhandled promise rejection.

- [ ] **Step 5: Run focused and full learning suites**

Run: `npm test -- --run src/storage/endurance.test.ts src/domain/fact-mastery.test.ts src/domain/session-selection.test.ts src/domain/adaptive-session.test.ts`  
Expected: PASS.  
Run: `npx playwright test e2e/production-learning-endurance.spec.ts`  
Expected: PASS.

- [ ] **Step 6: Commit learning verification and any minimal fix**

```bash
git add src/storage/final-bank.ts src/domain/session-selection.ts src/domain/fact-mastery.ts src/storage/endurance.test.ts src/domain/fact-mastery.test.ts e2e/production-learning-endurance.spec.ts
git commit -m "test: prove competitive spaced learning behavior"
```

### Task 8: Repair and exhaustively verify application interactions

**Files:**
- Modify if required by failing tests: `src/App.tsx`
- Modify if required by failing tests: `src/app/app-state.tsx`
- Modify if required by failing tests: `src/components/quiz-page.tsx`
- Modify if required by failing tests: `src/components/bank-manager-page.tsx`
- Modify if required by failing tests: `src/components/session-builder-page.tsx`
- Modify if required by failing tests: `src/components/massive-training-hub.tsx`
- Modify if required by failing tests: `src/components/answer-learning-feedback.tsx`
- Test: matching `*.test.tsx` files
- Test: `e2e/resilience.spec.ts`
- Test: `e2e/training-modes.spec.ts`
- Test: `e2e/responsive-experience.spec.ts`

**Interfaces:**
- Consumes: current app navigation and `startRound`/`recordAnswer` promises.
- Produces: visible busy, success, retry, and error behavior for every asynchronous action.

- [ ] **Step 1: Add focused failing interaction tests for known weak paths**

Test rejection from `recordAnswer`, backup export, bank removal, fullscreen APIs, and round startup. Require no unhandled promise rejection, a visible Spanish error, a retry path, and disabled duplicate triggers. Require the “Entendido” feedback button to close or advance the feedback state observably.

- [ ] **Step 2: Run component tests and verify red**

Run: `npm test -- --run src/components/quiz-page.test.tsx src/components/bank-manager-page.test.tsx src/components/session-builder-page.test.tsx src/components/massive-training-hub.test.tsx src/components/answer-learning-feedback.test.tsx`  
Expected: FAIL only on the newly demonstrated interaction gaps.

- [ ] **Step 3: Implement scoped async error handling**

Use `try/catch/finally` around awaited actions, disable all equivalent triggers while an operation is pending, and show the existing alert/error component with a retry action. Handle rejected fullscreen promises without breaking quiz state. Wire “Entendido” to the actual feedback transition.

- [ ] **Step 4: Exercise every principal button in E2E**

Cover dashboard navigation, quick round, manual configuration, all training modes, answer submission, next question, finish round, restart, review, history, statistics, bank manager, backup, fullscreen, theme, and mobile navigation. For each, assert a state change or visible result instead of only checking clickability.

- [ ] **Step 5: Run the complete local UI matrix**

Run: `npm test`  
Expected: all Vitest suites pass.  
Run: `npm run typecheck`  
Expected: PASS.  
Run: `npm run lint`  
Expected: PASS.  
Run: `npm run build`  
Expected: PASS.  
Run: `npx playwright test --project=chromium --project=firefox --project=webkit`  
Expected: PASS on configured desktop and mobile projects.

- [ ] **Step 6: Commit interaction fixes and evidence**

```bash
git add src e2e
git commit -m "fix: make all training interactions observable and resilient"
```

### Task 9: Final audit, production deployment, and live verification

**Files:**
- Create: `reports/final-authored-bank-audit.json`
- Create: `reports/final-authored-bank-audit.md`
- Modify: `reports/final-ai-editorial-review.md`
- Modify if content hashes changed: `public/banks/final-2026/review-index.json`

**Interfaces:**
- Consumes: committed V10 bank and verified application.
- Produces: reproducible local and live evidence for content, rounds, learning, assets, and interactions.

- [ ] **Step 1: Run the complete local release gate from a clean process**

Run:

```powershell
npm run test:authored
npm run audit:authored
npm run audit:competitive
npm run audit:exhaustive
npm test
npm run typecheck
npm run lint
npm run build
npx playwright test
git diff --check
```

Expected: every command exits 0; authored count is 12,000; forbidden prompt count, cross-passage false count, active audit findings, and human signatures are all 0.

- [ ] **Step 2: Generate the final evidence reports**

Record exact hashes, counts by unit/family/subtype/difficulty, duplicate metrics, audit decisions, round simulations, learning simulations, test totals, and the explicit statement `human_signatures: 0`. The Markdown report must link each JSON evidence file.

- [ ] **Step 3: Review the complete diff before external action**

Run: `git status --short` and `git diff --stat HEAD~1..HEAD`.  
Inspect that no untracked user files are staged and no legacy bank path outside `public/banks/final-2026` changed accidentally.

- [ ] **Step 4: Commit reports and push the verified main branch**

```bash
git add reports/final-authored-bank-audit.json reports/final-authored-bank-audit.md reports/final-ai-editorial-review.md public/banks/final-2026/review-index.json
git commit -m "docs: record final authored bank verification"
git push origin main
```

- [ ] **Step 5: Deploy the verified commit**

Run: `npm run deploy`  
Expected: Vercel reports a successful production deployment for the exact verified commit.

- [ ] **Step 6: Audit production content and behavior**

Run: `npm run audit:production`  
Expected: schema `10.0`, 18 matching shard hashes, 12,000 questions, zero missing assets.  
Run the Playwright production projects against `https://conexion-biblica-2026.vercel.app/`. Expected: all principal interactions, round composition, response persistence, retry behavior, and mobile navigation pass.

- [ ] **Step 7: Publish the final verification commit if live evidence changed tracked reports**

```bash
git add reports/final-authored-bank-audit.json reports/final-authored-bank-audit.md
git commit -m "docs: record production verification"
git push origin main
```

- [ ] **Step 8: Final handoff**

Report the deployed commit, URL, exact test totals, bank counts, forbidden-pattern counts, production verification result, and remaining honest limitation: semantic review was performed by AI and `human_signatures` remains 0.
