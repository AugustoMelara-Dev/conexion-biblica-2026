# V10 Integration, Verification, and Production Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the corrected V10 public and private artifacts, prove content quality, learning behavior, simulation invariants, and zero blind leakage, then release the exact verified commit to production with an executable rollback path.

**Architecture:** The public compiler emits only the trainable bank under `public/banks/final-2026`; the 250 blind presentations compile independently to the ephemeral, gitignored root `output/private/competitive-v11-blind`. A release gate consumes both artifacts plus the 2,606-row reconciliation ledger and produces tracked evidence without copying private stems, options, IDs, or fingerprints into reports. Local compilation, pair validation, content QC, 1,000-seed simulations, browser tests, build scanning, and a protected Vercel candidate must all pass before production promotion.

**Tech Stack:** Python 3.12 `unittest`, Node.js ESM, TypeScript 6, Vitest 3, React 19, Vite 8, Playwright 1.51, PowerShell, Vercel CLI.

**Spec:** `docs/superpowers/specs/2026-08-30-v10-cobertura-total-y-reserva-generalizacion-design.md`

## Global Constraints

- Preserve V10 architecture, difficulty, simulators, QC, and the 45/30/25 national-final mix.
- Never delete or replace an existing public presentation; after migration at least 2,468 public presentations and all 2,217 V10 competitive facts must remain trainable.
- The reconciliation ledger at `content/competitive-v11/reconciliation/fact-ledger-v10.json` must contain exactly 2,606 historical FACT decisions; status totals are derived from the ledger, never from the nominal delta 2,606 − 2,217.
- `represented_rekeyed` and `represented_merged` require a public presentation that specifically tests the complete historical proposition; otherwise the FACT is `reincorporated` with at least one new public question.
- The new private reserve contains exactly 250 presentation IDs and 250 unique `fact_id` values: A=100, B=100, emergency=50; no fact repeats across pools.
- A and B each preserve 45 selection, 30 fill-choice, and 25 true/false; emergency preserves 23 selection, 15 fill-choice, and 12 true/false.
- Every private presentation is HARD or EXPERT and keeps exact source, evidence excerpt, canonical answer, and fact traceability.
- Public/private equality is permitted for `fact_id`, canonical answer, source reference, and evidence excerpt; novelty checks apply to presentation ID, `variant_id`, normalized stem, syntax signature, options, distractors, distractor-pattern signature, and editorial presentation fingerprint.
- `content/competitive-v11/private-blind/**` and `output/private/competitive-v11-blind/**` must never enter `public/`, `dist/`, public manifests, source maps, service-worker caches, frontend statistics, public APIs, deployment payloads, or tracked release reports.
- Do not modify production until every local and protected-candidate gate is green. Do not disable Vercel deployment protection.
- The three prerequisite implementation plans—blind/compiler, FACT reconciliation, and privacy isolation—must be completed and committed before Task 1; this plan verifies their contracts and must not silently create substitute data when an input is missing.

## File and Interface Map

- `scripts/compile-competitive-v11.py`: owns deterministic public/private compilation and `validate_emitted_pair(public_root: Path, private_root: Path) -> str`.
- `scripts/audit-competitive-v11.py`: owns factual, structural, source, hash, and review-ledger validation for authored corpora.
- `scripts/audit-blind-privacy-v11.py`: owns repository/build/remote blind-leak scanning; it reports only counts, violation labels, and digests, never private strings.
- `scripts/simulate-private-blind-v11.py`: owns A/B/emergency invariant simulation over the compiled private artifact.
- `scripts/verify-v10-release.py`: new integration-only gate; orchestrates already implemented validators and writes sanitized release evidence.
- `scripts/test_verify_v10_release.py`: unit and negative-path coverage for the release gate.
- `content/competitive-v11/promoted-blind-v10.json`: prerequisite immutable registry for the 250 former blind presentations promoted to public training; its IDs and hashes join the compiler and promotion tests as the no-deletion evidence.
- `src/storage/final-bank-v8.real.test.ts`: public real-bank 1,000-seed national-final proof.
- `src/domain/fact-mastery.test.ts`, `src/domain/adaptive-session.test.ts`, `src/storage/endurance.test.ts`: mastery, spaced review, recurring-error, and multi-round uniqueness proof.
- `e2e/production-learning-endurance.spec.ts`, `e2e/training-modes.spec.ts`, `e2e/resilience.spec.ts`, `e2e/responsive-experience.spec.ts`, `e2e/editorial-audit.spec.ts`: real-interface verification across the six configured Playwright projects.
- `reports/competitive-v11/release-verification.json` and `.md`: sanitized, tracked release evidence.
- `output/release-v10/`: ephemeral candidate compilation, command logs, deployment URLs, and rollback metadata; remains ignored by Git.

---

### Task 1: Add a single fail-closed release gate

**Files:**
- Create: `scripts/verify-v10-release.py`
- Create: `scripts/test_verify_v10_release.py`
- Modify: `package.json`
- Generate: `reports/competitive-v11/release-verification.json`
- Generate: `reports/competitive-v11/release-verification.md`

**Interfaces:**
- Consumes: `content/competitive-v11/reconciliation/fact-ledger-v10.json`, `content/competitive-v11/promoted-blind-v10.json`, `reports/competitive-v11/fact-reconciliation.json`, a compiled public root, a compiled private root, and JSON results from the content, simulation, and privacy auditors.
- Produces: `verify_release(public_root: Path, private_root: Path, ledger_path: Path, report_root: Path, promotion_registry_path: Path) -> dict[str, object]`; exits nonzero unless every required gate is `PASS`.
- Sanitization contract: output may contain aggregate counts, SHA-256 digests, command names, exit codes, and violation codes; it must not contain private presentation IDs, `variant_id`, stems, options, distractors, or presentation fingerprints.

- [ ] **Step 1: Write failing unit tests for missing, failed, and passing gates**

Add fixtures that create minimal aggregate auditor results without private prose. The decisive assertions are:

```python
def test_release_gate_rejects_any_non_pass_gate(self):
    inputs = self.valid_inputs()
    inputs["privacy"] = {"ok": False, "scanned": 1, "findings": [{"kind": "normalized_stem"}]}
    with self.assertRaisesRegex(ValueError, "privacy"):
        verify_release(**inputs)

def test_release_gate_requires_exact_ledger_cardinality(self):
    inputs = self.valid_inputs()
    inputs["ledger_rows"] = inputs["ledger_rows"][:-1]
    with self.assertRaisesRegex(ValueError, "2606"):
        verify_release(**inputs)

def test_release_report_does_not_serialize_private_tokens(self):
    report = verify_release(**self.valid_inputs())
    serialized = json.dumps(report, ensure_ascii=False)
    for forbidden in ("BLIND-A-001", "stem secreto", "distractor secreto"):
        self.assertNotIn(forbidden, serialized)
    self.assertEqual(report["status"], "PASS")
```

- [ ] **Step 2: Run the new test and confirm RED**

Run: `python -m unittest scripts.test_verify_v10_release -v`

Expected: FAIL with `ModuleNotFoundError` or missing `verify_release`; no report is created.

- [ ] **Step 3: Implement the aggregate gate and CLI**

Implement these required CLI arguments exactly:

```text
--public-root PUBLIC_ROOT
--private-root PRIVATE_ROOT
--ledger LEDGER
--promotion-registry PROMOTION_REGISTRY
--content-report CONTENT_REPORT
--reconciliation-report RECONCILIATION_REPORT
--public-simulation-report PUBLIC_SIMULATION_REPORT
--private-simulation-report PRIVATE_SIMULATION_REPORT
--privacy-report PRIVACY_REPORT
--output-root OUTPUT_ROOT
```

The gate must verify: all input files exist; content, reconciliation, and private-simulation reports have `status: PASS`; the privacy report has `ok: true` and `findings: []`; the Vitest JSON public-simulation report has `numFailedTests: 0` and includes the named 1,000-seed test; ledger length is 2,606 with unique historical IDs and one allowed status per row; every `reincorporated` row names an emitted public presentation; all 250 IDs in the promotion registry remain public; the promotion/compiler regression tests prove all original 2,468 IDs remain; public fact coverage contains all 2,217 V10 fact IDs; private has exactly 250 unique facts split 100/100/50; and public/private presentation identities and signatures are disjoint. Write JSON atomically, then render Markdown only from the sanitized aggregate object.

- [ ] **Step 4: Add deterministic package commands**

Add these exact scripts to `package.json`:

```json
{
  "test:v10:python": "python -m unittest scripts.test_competitive_v11 scripts.test_apply_blind_assignment_v11 scripts.test_verify_v10_release scripts.test_audit_live_final_bank_integration",
  "test:v10:node": "node --test scripts/lib/competitive-audit.test.mjs scripts/audit-live-final-bank.check.mjs",
  "test:v10:ui": "vitest run",
  "test:v10:e2e": "playwright test"
}
```

- [ ] **Step 5: Run unit tests and confirm GREEN**

Run: `python -m unittest scripts.test_verify_v10_release -v`

Expected: all release-gate tests PASS; temporary reports contain no private tokens.

- [ ] **Step 6: Commit the release-gate implementation**

```powershell
git add scripts/verify-v10-release.py scripts/test_verify_v10_release.py package.json
git commit -m "test: add fail-closed V10 release gate"
```

Expected: one commit containing only the integration gate, its tests, and package commands.

### Task 2: Compile and validate the public/private artifact pair

**Files:**
- Consume: `content/competitive-v11/questions/*.json`
- Consume: `content/competitive-v11/reviews/*.json`
- Consume: `content/competitive-v11/private-blind/authored-batches/*.json`
- Consume: `content/competitive-v11/private-blind/reviews/*.json`
- Consume: `content/competitive-v11/private-blind/assignment-v2.json`
- Generate: `output/release-v10/public-final-2026/**`
- Generate: `output/private/competitive-v11-blind/**`
- Generate after candidate validation: `public/banks/final-2026/**`
- Test: `scripts/test_competitive_v11.py`

**Interfaces:**
- Consumes: corrected compiler contract from the blind/compiler plan.
- Produces: a public artifact containing training only, a separate private artifact containing 250 new presentations, and a shared deterministic pair/build digest without publishing private metadata.
- Preserves: all existing public question IDs plus the 250 formerly blind IDs and every accepted reincorporation.

- [ ] **Step 1: Add pair-integration assertions before compiling release data**

In `scripts/test_competitive_v11.py`, add a real-shaped fixture and assert:

```python
self.assertTrue(private_fact_ids <= public_fact_ids)
self.assertEqual(len(private_fact_ids), 250)
self.assertEqual(sum(pool_sizes.values()), 250)
self.assertFalse(public_presentation_ids & private_presentation_ids)
self.assertFalse(public_variant_ids & private_variant_ids)
for forbidden_key in ("blind_pools", "blind_delivery", "blind_fact_count", "blind_presentation_count"):
    self.assertNotIn(forbidden_key, public_manifest)
```

Implement the cross-pool fact assertion explicitly as `self.assertFalse(pool_fact_ids[left] & pool_fact_ids[right])` for `(A,B)`, `(A,emergency)`, and `(B,emergency)`. Also assert exact family distributions and HARD/EXPERT difficulty for all 250 private rows.

- [ ] **Step 2: Run the focused compiler tests and confirm the corrected contract**

Run: `python -m unittest scripts.test_competitive_v11 -v`

Expected: PASS only when the compiler permits shared facts, rejects shared presentation identities/signatures, rejects a repeated fact across pools, and omits all blind metadata from the public manifest.

- [ ] **Step 3: Compile to ephemeral candidate roots**

```powershell
New-Item -ItemType Directory -Force -Path output/release-v10 | Out-Null
python scripts/compile-competitive-v11.py --source-root content/competitive-v11 --output output/release-v10/public-final-2026 --blind-source-root content/competitive-v11/private-blind --blind-output output/private/competitive-v11-blind --require-blind-release
```

Expected: exit 0; public presentations are at least 2,468; V10 public fact coverage is 2,217/2,217; private output has exactly 250 presentations; no source file is modified.

- [ ] **Step 4: Validate the emitted pair independently**

Run:

```powershell
python scripts/compile-competitive-v11.py --validate-pair output/release-v10/public-final-2026 output/private/competitive-v11-blind
```

Expected: one JSON object with `"valid": true` and a 64-character `build_id`; exit 0.

- [ ] **Step 5: Prove deterministic compilation**

Compile the same source to a second public root while retaining a separately named private copy:

```powershell
python scripts/compile-competitive-v11.py --source-root content/competitive-v11 --output output/release-v10/public-final-2026-repeat --blind-source-root content/competitive-v11/private-blind --blind-output output/release-v10/private-blind-repeat --require-blind-release
$first = (Get-FileHash output/release-v10/public-final-2026/manifest.json -Algorithm SHA256).Hash
$second = (Get-FileHash output/release-v10/public-final-2026-repeat/manifest.json -Algorithm SHA256).Hash
if ($first -ne $second) { throw "Public manifest is not deterministic" }
$privateFirst = (Get-FileHash output/private/competitive-v11-blind/manifest.json -Algorithm SHA256).Hash
$privateSecond = (Get-FileHash output/release-v10/private-blind-repeat/manifest.json -Algorithm SHA256).Hash
if ($privateFirst -ne $privateSecond) { throw "Private manifest is not deterministic" }
```

Expected: both hash comparisons succeed.

- [ ] **Step 6: Atomically compile the verified public artifact into the application**

Run:

```powershell
python scripts/compile-competitive-v11.py --source-root content/competitive-v11 --output public/banks/final-2026 --blind-source-root content/competitive-v11/private-blind --blind-output output/private/competitive-v11-blind --require-blind-release
python scripts/compile-competitive-v11.py --validate-pair public/banks/final-2026 output/private/competitive-v11-blind
```

Expected: exit 0; the emitted `build_id` matches the candidate; `git diff -- public/banks/final-2026` contains additions/metadata changes but no deletion of a preexisting question ID.

- [ ] **Step 7: Commit the public artifact and integration assertions only**

```powershell
git add scripts/test_competitive_v11.py public/banks/final-2026
git diff --cached --check
git commit -m "build: integrate verified V10 public bank"
```

Expected: private roots remain untracked and absent from the commit.

### Task 3: Run factual, semantic, editorial, and adversarial QC

**Files:**
- Consume: `content/competitive-v11/questions/*.json`
- Consume: `content/competitive-v11/private-blind/authored-batches/*.json`
- Consume: `content/competitive-v11/private-blind/reviews/*.json`
- Consume: `content/competitive-v11/private-blind/editorial-comparisons.json`
- Consume: `content/competitive-v11/reconciliation/fact-ledger-v10.json`
- Regenerate: `reports/competitive-v11/fact-reconciliation.json`
- Regenerate: `reports/competitive-v11/fact-reconciliation.csv`
- Regenerate: `reports/competitive-v11/fact-reconciliation.md`
- Generate: `reports/competitive-v11/fact-reconciliation-summary.json`
- Test: `scripts/test_blind_generalization_v11.py`
- Test: `scripts/test_fact_reconciliation_v10.py`

**Interfaces:**
- Consumes: `audit_generalization_release(...) -> dict[str, Any]`, `audit_reconciliation(root: Path, public_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]`, canonical review hashes, and the fingerprint/syntax/distractor-pattern functions implemented by the prerequisite plans.
- Produces: current per-batch factual/semantic/adversarial evidence and reconciliation evidence tied to the same authored sources and compiled public bank. The release-wide generalization audit is intentionally deferred to Task 8, after simulation, privacy, and E2E evidence exists.

- [ ] **Step 1: Re-run the complete adversarial regression suite**

Run:

```powershell
python -m unittest scripts.test_promote_blind_training_v11 scripts.test_blind_generalization_v11 scripts.test_build_blind_generalization_manifest_v11 scripts.test_apply_private_blind_batches_v11 scripts.test_competitive_v11 scripts.test_fact_reconciliation_v10 scripts.test_authored_question -v
```

Expected: PASS, including fixtures for normalized-stem reuse, syntax reuse, recognizable distractor reuse, fingerprint collision, answer cues, unsupported distractors, stale review hashes, second defensible answers, and missing exact support. Shared `fact_id`, answer, reference, and source evidence remain accepted.

- [ ] **Step 2: Re-audit all seven private lots against public content and exact source support**

Run:

```powershell
$batches = @(
  'blind-new-01-A-DAN1-6.json',
  'blind-new-02-A-DAN7-12.json',
  'blind-new-03-A-PR39-44.json',
  'blind-new-04-B-DAN1-6.json',
  'blind-new-05-B-DAN7-12.json',
  'blind-new-06-B-PR39-44.json',
  'blind-new-07-emergency-all.json'
)
foreach ($batch in $batches) {
  python scripts/audit-competitive-v11.py --public-root content/competitive-v11/questions --private-source-root content/competitive-v11/private-blind --assignment content/competitive-v11/private-blind/assignment-v2.json --batch $batch
  if ($LASTEXITCODE -ne 0) { throw "Editorial audit failed: $batch" }
}
```

Expected: every batch exits 0; all 250 rows have current source/review hashes, one defensible answer, plausible distractors, no answer cue, and no exact or recognizable public presentation reuse.

- [ ] **Step 3: Regenerate and byte-check the 2,606-row reconciliation reports**

```powershell
python scripts/reconcile-facts-v10.py report --historical-facts content/competitive-v11/reconciliation/historical-facts.json --ledger content/competitive-v11/reconciliation/fact-ledger-v10.json --public-questions content/competitive-v11/questions --reincorporated-questions content/competitive-v11/reconciliation/reincorporated-questions --source-packets content/competitive-v11/source-packets --output-dir reports/competitive-v11
python scripts/reconcile-facts-v10.py report --check --historical-facts content/competitive-v11/reconciliation/historical-facts.json --ledger content/competitive-v11/reconciliation/fact-ledger-v10.json --public-questions content/competitive-v11/questions --reincorporated-questions content/competitive-v11/reconciliation/reincorporated-questions --source-packets content/competitive-v11/source-packets --output-dir reports/competitive-v11
$reconciliation = python scripts/reconcile-facts-v10.py audit --root . --json | ConvertFrom-Json
if (-not $reconciliation.valid) { throw "Reconciliation audit failed" }
$publicManifest = Get-Content -Raw public/banks/final-2026/manifest.json | ConvertFrom-Json
$summary = [ordered]@{
  status = 'PASS'
  build_id = $publicManifest.build_id
  historical_fact_count = $reconciliation.historical_fact_count
  decision_count = $reconciliation.decision_count
  status_counts = $reconciliation.status_counts
  reincorporated_count = $reconciliation.reincorporated_count
  errors = @($reconciliation.errors)
}
$summary | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 reports/competitive-v11/fact-reconciliation-summary.json
```

Expected: `"valid": true`, `historical_fact_count: 2606`, `decision_count: 2606`, `errors: []`; status counts are derived; every represented/reincorporated detail resolves to a specific public testing presentation; every exclusion has an individualized permitted reason.

- [ ] **Step 4: Verify the reconciliation summary is a sanitized PASS envelope**

```powershell
$summary = Get-Content -Raw reports/competitive-v11/fact-reconciliation-summary.json | ConvertFrom-Json
if ($summary.status -ne 'PASS' -or $summary.historical_fact_count -ne 2606 -or $summary.decision_count -ne 2606 -or @($summary.errors).Count -ne 0) {
  throw "Invalid reconciliation summary"
}
```

Expected: PASS; the summary contains derived totals, build ID, and zero errors without reproducing historical or private question prose.

- [ ] **Step 5: Commit regenerated QC evidence only when bytes changed**

```powershell
git add reports/competitive-v11/fact-reconciliation.json reports/competitive-v11/fact-reconciliation.csv reports/competitive-v11/fact-reconciliation.md reports/competitive-v11/fact-reconciliation-special-cases.json reports/competitive-v11/fact-reconciliation-reincorporated.md reports/competitive-v11/fact-reconciliation-summary.json
git diff --cached --check
git commit -m "docs: record V10 factual and adversarial QC"
```

Expected: regenerated reports either match the committed bytes or produce a reviewable evidence-only commit; no authored private file is staged.

### Task 4: Prove 1,000 public seeds and all private pool invariants

**Files:**
- Modify: `src/storage/final-bank-v8.real.test.ts`
- Create: `scripts/simulate-private-blind-v11.py`
- Create: `scripts/test_simulate_private_blind_v11.py`
- Generate: `reports/competitive-v11/national-simulations-1000.json`
- Generate: `output/release-v10/private-simulation-report.json`

**Interfaces:**
- Public: consumes `loadFinalQuestionPool()` and the production national-final selector; produces a deterministic aggregate for seeds 0–999.
- Private: `simulate_private_artifact(private_root: Path) -> dict[str, object]`; checks A/B/emergency without importing private data into TypeScript or the frontend.

- [ ] **Step 1: Extend the real-bank test to 1,000 deterministic national finals**

The test must execute the same selector used by the app and assert for every seed:

```ts
for (let seed = 0; seed < 1_000; seed += 1) {
  const round = selectMandatoryHundred(nationalFinal, seed)
  expect(round).toHaveLength(100)
  expect(new Set(round.map((row) => row.factId)).size).toBe(100)
  expect(round.filter((row) => row.type === "single_choice")).toHaveLength(45)
  expect(round.filter((row) => row.type === "fill_blank")).toHaveLength(30)
  expect(round.filter((row) => row.type === "true_false")).toHaveLength(25)
  expect(round.every((row) => !("blindPool" in row) && !("blindFinalPool" in row))).toBe(true)
}
```

Import `selectMandatoryHundred` from `src/domain/final-mission-selection.ts`, exactly as the current real-bank test does; do not create a test-only sampling algorithm.

When `V10_SIMULATION_REPORT` is set, the same test writes this sanitized aggregate after all assertions pass:

```ts
writeFileSync(process.env.V10_SIMULATION_REPORT, JSON.stringify({
  status: "PASS",
  build_id: manifest.build_id,
  seeds: 1000,
  round_size: 100,
  unique_fact_failures: 0,
  family_mix: { single_choice: 45, fill_blank: 30, true_false: 25 },
  difficulty: ["HARD", "EXPERT"],
  failures: [],
}, null, 2) + "\n")
```

- [ ] **Step 2: Run the real-bank test and confirm its actual result**

Run: `npm test -- --run src/storage/final-bank-v8.real.test.ts`

Expected: 1,000/1,000 seeds PASS with 100 unique facts and exact 45/30/25 composition. If it fails, preserve the seed and invariant in the assertion message before changing selection code.

- [ ] **Step 3: Write failing private simulator tests**

```python
def test_rejects_fact_reuse_between_pools(self):
    artifact = valid_artifact()
    artifact["B"][0]["fact_id"] = artifact["A"][0]["fact_id"]
    with self.assertRaisesRegex(ValueError, "cross-pool fact"):
        simulate_rows(artifact)

def test_accepts_exact_release_shape(self):
    result = simulate_rows(valid_artifact())
    self.assertEqual(result["status"], "PASS")
    self.assertEqual(result["pools"]["A"]["families"], {"selection": 45, "fill_choice": 30, "true_false": 25})
```

- [ ] **Step 4: Run private simulator tests and confirm RED**

Run: `python -m unittest scripts.test_simulate_private_blind_v11 -v`

Expected: FAIL because the simulator module/functions do not yet exist.

- [ ] **Step 5: Implement the private simulator without exposing rows**

The result schema must contain only:

```python
{
    "status": "PASS",
    "presentation_count": 250,
    "unique_fact_count": 250,
    "cross_pool_fact_collisions": 0,
    "pools": {
        "A": {"count": 100, "families": {"selection": 45, "fill_choice": 30, "true_false": 25}},
        "B": {"count": 100, "families": {"selection": 45, "fill_choice": 30, "true_false": 25}},
        "emergency": {"count": 50, "families": {"selection": 23, "fill_choice": 15, "true_false": 12}},
    },
}
```

Also assert one fact per pool row, HARD/EXPERT only, source/evidence traceability, unique presentation/variant IDs, and no duplicate editorial signatures.

- [ ] **Step 6: Run both simulation gates and save ephemeral aggregate reports**

```powershell
$env:V10_SIMULATION_REPORT='reports/competitive-v11/national-simulations-1000.json'
npm test -- --run src/storage/final-bank-v8.real.test.ts
Remove-Item Env:V10_SIMULATION_REPORT
python scripts/simulate-private-blind-v11.py --private-root output/private/competitive-v11-blind --output output/release-v10/private-simulation-report.json
python -m unittest scripts.test_simulate_private_blind_v11 -v
```

Expected: all commands exit 0; public report records 1,000 passing seeds; private report records 250 unique facts and exact pool/family counts without private IDs.

- [ ] **Step 7: Commit the simulation code and public test**

```powershell
git add src/storage/final-bank-v8.real.test.ts scripts/simulate-private-blind-v11.py scripts/test_simulate_private_blind_v11.py reports/competitive-v11/national-simulations-1000.json
git commit -m "test: prove V10 public and private simulation invariants"
```

### Task 5: Verify mastery, spaced repetition, and recurring-error behavior

**Files:**
- Modify: `src/domain/fact-mastery.test.ts`
- Modify: `src/domain/adaptive-session.test.ts`
- Modify: `src/storage/endurance.test.ts`
- Modify only upon a demonstrated regression: `src/domain/fact-mastery.ts`
- Modify only upon a demonstrated regression: `src/domain/adaptive-session.ts`
- Modify only upon a demonstrated regression: `src/storage/final-bank.ts`

**Interfaces:**
- Consumes: `applyFactEvidence(previous: FactMastery, event: FactEvidenceEvent) -> FactMastery` and `selectAdaptiveSession(...) -> Question[]`.
- Produces: deterministic proof that immediate feedback is not mastery, failures recur after spacing, due facts return, repeated variants do not substitute for semantic breadth, and sessions keep unique facts.

- [ ] **Step 1: Add a deterministic learning timeline test**

Use fixed Tegucigalpa timestamps and assert this sequence:

```ts
const t0 = Date.UTC(2026, 7, 31, 12)
let state = emptyFactMastery("DAN7-V025-F01")
state = applyFactEvidence(state, event({ occurredAt: t0, isCorrect: false, firstAttempt: true }))
expect(state.state).toBe("due")
state = applyFactEvidence(state, event({ occurredAt: t0 + 60_000, isCorrect: true, firstAttempt: false, afterFeedback: true }))
expect(state.state).toBe("repaired")
expect(state.state).not.toBe("mastered")
state = applyFactEvidence(state, event({ occurredAt: t0 + 6 * 3_600_000, isCorrect: true, firstAttempt: true, semanticSkill: "sequence" }))
expect(state.hasSixHourRetrieval).toBe(true)
state = applyFactEvidence(state, event({ occurredAt: t0 + 24 * 3_600_000, isCorrect: true, firstAttempt: true, semanticSkill: "cause" }))
expect(state.hasNextDayRetrieval).toBe(true)
```

- [ ] **Step 2: Add spaced-review and recurring-error selection tests**

Construct 120 public questions with unique facts, mark 20 due and 20 with failures, then assert `spaced-review` returns only due facts, `previous-errors` returns only failed facts, and every selected session contains unique fact IDs. Add a second variant for a failed fact and assert the scheduler can change presentation without duplicating the fact in one round.

- [ ] **Step 3: Run the narrow learning suite**

Run:

```powershell
npm test -- --run src/domain/fact-mastery.test.ts src/domain/adaptive-session.test.ts src/storage/endurance.test.ts
```

Expected: PASS. If a new assertion fails, record the exact test and observed state transition in `output/release-v10/learning-regression.txt`; do not weaken the assertion.

- [ ] **Step 4: Apply only a demonstrated runtime correction and rerun RED/GREEN**

For an observed defect, edit only the owning function: mastery transition in `applyFactEvidence`, due/error filtering in `selectAdaptiveSession`, or real-bank loading/selection in `src/storage/final-bank.ts`. Re-run the single failing test first, then the three-file command from Step 3.

Expected: the original failing test changes from FAIL to PASS and no existing learning test regresses.

- [ ] **Step 5: Commit learning evidence and any narrow correction**

```powershell
git add src/domain/fact-mastery.test.ts src/domain/adaptive-session.test.ts src/storage/endurance.test.ts src/domain/fact-mastery.ts src/domain/adaptive-session.ts src/storage/final-bank.ts
git diff --cached --check
git commit -m "test: verify V10 mastery and spaced repetition"
```

The command may name unchanged runtime files; Git does not stage them. Confirm the cached diff contains only files with actual changes.

### Task 6: Build the application and prove zero private leakage

**Files:**
- Consume: `.vercelignore`
- Consume: `scripts/audit-blind-privacy-v11.py`
- Test: `scripts/test_audit_blind_privacy_v11.py`
- Test: `src/service-worker.test.ts`
- Test: `src/deployment-cache.test.ts`
- Test: `e2e/private-reserve-boundary.spec.ts`
- Consume: `dist/**`
- Consume privately: `output/private/competitive-v11-blind/**`
- Generate: `output/release-v10/privacy-local.json`
- Generate: `reports/competitive-v11/private-build-leak-audit.json`

**Interfaces:**
- Consumes: the private artifact only as a comparison corpus.
- Uses: `load_private_signature_index(private_root: Path) -> LeakSignatureIndex`, `scan_directory(root: Path, index: LeakSignatureIndex, label: Literal["public", "dist"]) -> list[LeakFinding]`, and the CLI result `{ "ok": bool, "scanned": int, "findings": list }` from the privacy prerequisite plan.
- Deployment exclusion: `.vercelignore` must contain the broader canonical exclusions `content/`, `output/`, `reports/`, `docs/`, `scripts/`, `e2e/`, and `*.pdf`, which necessarily exclude all private source and release artifacts.

- [ ] **Step 1: Re-run the scanner's presentation-specific leak and factual false-positive tests**

Run: `python -m unittest scripts.test_audit_blind_privacy_v11 -v`

Expected: PASS; a legitimate shared `fact_id`, canonical answer such as “Miguel”, reference, or source quote is allowed, while private presentation IDs, `variant_id`, normalized stems, complete option/distractor sets, fingerprints, paths, public metadata, source maps, and service-worker entries are detected.

- [ ] **Step 2: Build from a clean tracked tree**

```powershell
npm run typecheck
npm run lint
npm run build
```

Expected: all commands exit 0; Vite writes `dist/`; no TypeScript or lint errors.

- [ ] **Step 3: Scan public paths and the built application**

```powershell
python scripts/audit-blind-privacy-v11.py --private-root output/private/competitive-v11-blind --public-root public --dist-root dist | Tee-Object -FilePath output/release-v10/privacy-local.json
```

Expected: `{ "ok": true, "findings": [] }`; no private IDs, stems, complete option/distractor sets, fingerprints, pool paths, or metadata occur in `public/`, `dist/`, source maps, service-worker content, frontend code, or public API files.

Wrap the raw scanner result with the common build ID required by the final generalization audit:

```powershell
$scan = Get-Content -Raw output/release-v10/privacy-local.json | ConvertFrom-Json
$publicManifest = Get-Content -Raw public/banks/final-2026/manifest.json | ConvertFrom-Json
$privateManifest = Get-Content -Raw output/private/competitive-v11-blind/manifest.json | ConvertFrom-Json
if ($publicManifest.build_id -ne $privateManifest.build_id) { throw "Artifact build IDs differ" }
$privacyEvidence = [ordered]@{
  status = if ($scan.ok -and @($scan.findings).Count -eq 0) { 'PASS' } else { 'FAIL' }
  build_id = $publicManifest.build_id
  scanned = $scan.scanned
  findings = @($scan.findings)
}
$privacyEvidence | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 reports/competitive-v11/private-build-leak-audit.json
```

Expected: `status: PASS`; the report contains no private signature text because findings are empty.

- [ ] **Step 4: Assert deployment exclusions and service-worker behavior**

```powershell
$ignore = (Get-Content .vercelignore) | Where-Object { $_.Trim() }
foreach ($required in @('content/','output/','reports/','docs/','scripts/','e2e/','*.pdf')) {
  if ($ignore -notcontains $required) { throw "Missing .vercelignore rule: $required" }
}
npm test -- --run src/service-worker.test.ts src/deployment-cache.test.ts
```

Expected: required exclusions exist; service worker caches the canonical public manifest only and never a private path.

- [ ] **Step 5: Run the browser network-boundary proof locally**

```powershell
npx playwright test e2e/private-reserve-boundary.spec.ts --project=desktop-chromium
```

Expected: PASS; the public app makes no private request and all ten forbidden remote probes return 404 without private content.

- [ ] **Step 6: Feed the canonical scanner report into the aggregate gate tests**

In `scripts/test_verify_v10_release.py`, retain the exact privacy adapter assertion:

```python
inputs = self.valid_inputs()
inputs["privacy"] = {"ok": False, "scanned": 9, "findings": [{"kind": "presentation_id"}]}
with self.assertRaisesRegex(ValueError, "privacy"):
    verify_release(**inputs)
```

Run: `python -m unittest scripts.test_verify_v10_release -v`

Expected: PASS; `ok: false` blocks release, while `ok: true` with an empty `findings` list is accepted.

- [ ] **Step 7: Commit only the release-gate integration assertion**

```powershell
git add scripts/test_verify_v10_release.py
git add reports/competitive-v11/private-build-leak-audit.json
git diff --cached --check
git commit -m "test: integrate blind privacy release evidence"
```

Expected: prerequisite privacy files remain unchanged; no private source or artifact is staged.

### Task 7: Run complete local suites and all six browser projects

**Files:**
- Modify: `e2e/production-learning-endurance.spec.ts`
- Modify: `e2e/training-modes.spec.ts`
- Modify: `e2e/resilience.spec.ts`
- Modify: `e2e/responsive-experience.spec.ts`
- Modify: `e2e/editorial-audit.spec.ts`
- Consume: `e2e/private-reserve-boundary.spec.ts`
- Consume: `playwright.config.ts`
- Generate ephemerally: `%TEMP%/conexion-biblica-playwright/**`
- Generate: `reports/competitive-v11/e2e-release.json`

**Interfaces:**
- Consumes: the real built public bank and public UI.
- Produces: observable browser proof for training, national-final mix, persistence, mastery/retry flows, navigation, error handling, responsive behavior, and private-mode absence on desktop/mobile Chromium, Firefox, and WebKit.

- [ ] **Step 1: Add browser assertions for the corrected release**

Assert through the real UI and public requests that:

```ts
await expect(page.getByText("Pregunta 1 de 100", { exact: true })).toBeVisible()
await expect(page.getByText(/simulación ciega/i)).toHaveCount(0)
const publicManifest = await page.request.get("/banks/final-2026/manifest.json")
expect(publicManifest.ok()).toBe(true)
expect(JSON.stringify(await publicManifest.json())).not.toMatch(/blind|emergency|private-blind/i)
for (const path of ["/banks/final-2026/blind/manifest.json", "/private-blind/assignment-v2.json"]) {
  expect((await page.request.get(path)).status()).toBe(404)
}
```

Use existing accessible labels and stable test hooks; do not expose a new private hook to make the assertions possible.

- [ ] **Step 2: Run all Python suites**

Run:

```powershell
python -m unittest discover -s scripts -p "test_*.py" -v
```

Expected: all discovered Python tests PASS; zero skips for release-critical compiler, reconciliation, novelty, privacy, private simulation, or live-audit tests.

- [ ] **Step 3: Run all Node audit suites**

Run:

```powershell
node --test scripts/audit-live-final-bank.check.mjs scripts/lib/competitive-audit.test.mjs scripts/lib/curated-question.test.mjs scripts/lib/curated-v4.integration.test.mjs scripts/lib/duplicate-policy.test.mjs scripts/lib/editorial.test.mjs scripts/lib/master-curation.test.mjs scripts/lib/ocr-path.test.mjs scripts/lib/pilot.test.mjs scripts/lib/semantic-audit.test.mjs
```

Expected: all Node tests PASS; live-bank fixture tests cover public/private contract changes without contacting production.

- [ ] **Step 4: Run the complete TypeScript/React suite and static checks**

```powershell
npm test
npm run typecheck
npm run lint
npm run build
```

Expected: Vitest, type checking, ESLint, and Vite build all exit 0.

- [ ] **Step 5: Run the six configured local Playwright projects explicitly**

```powershell
npx playwright test --project=desktop-chromium --project=mobile-chromium --project=desktop-firefox --project=mobile-firefox --project=desktop-webkit --project=mobile-webkit --reporter=json | Set-Content -Encoding utf8 output/release-v10/e2e-release-raw.json
if ($LASTEXITCODE -ne 0) { throw "Playwright release matrix failed" }
$rawE2e = Get-Content -Raw output/release-v10/e2e-release-raw.json | ConvertFrom-Json
$publicManifest = Get-Content -Raw public/banks/final-2026/manifest.json | ConvertFrom-Json
$e2eEvidence = [ordered]@{
  status = if ($rawE2e.stats.unexpected -eq 0) { 'PASS' } else { 'FAIL' }
  build_id = $publicManifest.build_id
  projects = @('desktop-chromium','mobile-chromium','desktop-firefox','mobile-firefox','desktop-webkit','mobile-webkit')
  expected = $rawE2e.stats.expected
  unexpected = $rawE2e.stats.unexpected
  flaky = $rawE2e.stats.flaky
  skipped = $rawE2e.stats.skipped
  duration_ms = $rawE2e.stats.duration
}
$e2eEvidence | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 reports/competitive-v11/e2e-release.json
```

Expected: every test passes in all six projects; failures retain trace and screenshot under `%TEMP%/conexion-biblica-playwright`.

- [ ] **Step 6: Re-run the local privacy scanner after E2E/build output exists**

Run:

```powershell
python scripts/audit-blind-privacy-v11.py --private-root output/private/competitive-v11-blind --public-root public --dist-root dist | Tee-Object -FilePath output/release-v10/privacy-after-e2e.json
```

Expected: PASS with zero violations.

- [ ] **Step 7: Commit E2E changes after the full matrix is green**

```powershell
git add e2e/production-learning-endurance.spec.ts e2e/training-modes.spec.ts e2e/resilience.spec.ts e2e/responsive-experience.spec.ts e2e/editorial-audit.spec.ts reports/competitive-v11/e2e-release.json
git diff --cached --check
git commit -m "test: certify V10 public training flows"
```

### Task 8: Freeze and review the exact release candidate

**Files:**
- Regenerate: `reports/competitive-v11/blind-generalization-audit.json`
- Regenerate: `reports/competitive-v11/blind-generalization-audit.md`
- Generate: `reports/competitive-v11/release-verification.json`
- Generate: `reports/competitive-v11/release-verification.md`
- Generate ephemerally: `output/release-v10/verified-commit.txt`
- Generate ephemerally: `output/release-v10/previous-production.txt`

**Interfaces:**
- Consumes: all green results from Tasks 2–7.
- Produces: an immutable Git commit SHA tied to sanitized evidence and a known previous production deployment for rollback.

- [ ] **Step 1: Run the release-wide factual, semantic, and adversarial audit after upstream evidence exists**

```powershell
python scripts/audit-competitive-v11.py --public-root content/competitive-v11/questions --private-source-root content/competitive-v11/private-blind --assignment content/competitive-v11/private-blind/assignment-v2.json --comparisons content/competitive-v11/private-blind/editorial-comparisons.json --report-json reports/competitive-v11/blind-generalization-audit.json --report-md reports/competitive-v11/blind-generalization-audit.md
```

Expected: 250/250 factual PASS, 250/250 semantic PASS, 250/250 adversarial PASS, zero pool collisions, exact family/difficulty contracts, 2,217/2,217 base facts trainable, no lost public IDs, and matching build IDs across reconciliation, 1,000 simulations, privacy, and E2E evidence.

- [ ] **Step 2: Run the aggregate release gate with every real report**

```powershell
python scripts/verify-v10-release.py --public-root public/banks/final-2026 --private-root output/private/competitive-v11-blind --ledger content/competitive-v11/reconciliation/fact-ledger-v10.json --promotion-registry content/competitive-v11/promoted-blind-v10.json --content-report reports/competitive-v11/blind-generalization-audit.json --reconciliation-report reports/competitive-v11/fact-reconciliation-summary.json --public-simulation-report reports/competitive-v11/national-simulations-1000.json --private-simulation-report output/release-v10/private-simulation-report.json --privacy-report output/release-v10/privacy-after-e2e.json --output-root reports/competitive-v11
```

Expected: `status: PASS`; ledger rows=2,606; public V10 coverage=2,217/2,217; public presentations≥2,468; private presentations/facts=250/250; every gate PASS; no private text in either report.

- [ ] **Step 3: Review repository scope and private-path absence**

```powershell
git status --short
git diff --check
git diff --stat 803efbc..HEAD
git ls-files content/competitive-v11/private-blind output/private output/release-v10 dist
```

Expected: only intended source/QC files are tracked; `output/private`, `output/release-v10`, and `dist` produce no `git ls-files` output; inspect every unexpected path before continuing.

- [ ] **Step 4: Commit final sanitized evidence**

```powershell
git add reports/competitive-v11/blind-generalization-audit.json reports/competitive-v11/blind-generalization-audit.md reports/competitive-v11/release-verification.json reports/competitive-v11/release-verification.md
git diff --cached --check
git commit -m "docs: certify V10 release candidate"
```

Expected: the evidence commit contains aggregate results only.

- [ ] **Step 5: Re-run the release-critical gate on the committed tree**

```powershell
python -m unittest discover -s scripts -p "test_*.py" -v
node --test scripts/audit-live-final-bank.check.mjs scripts/lib/competitive-audit.test.mjs scripts/lib/curated-question.test.mjs scripts/lib/curated-v4.integration.test.mjs scripts/lib/duplicate-policy.test.mjs scripts/lib/editorial.test.mjs scripts/lib/master-curation.test.mjs scripts/lib/ocr-path.test.mjs scripts/lib/pilot.test.mjs scripts/lib/semantic-audit.test.mjs
npm test
npm run typecheck
npm run lint
npm run build
npx playwright test --project=desktop-chromium --project=mobile-chromium --project=desktop-firefox --project=mobile-firefox --project=desktop-webkit --project=mobile-webkit
python scripts/audit-blind-privacy-v11.py --private-root output/private/competitive-v11-blind --public-root public --dist-root dist | Tee-Object -FilePath output/release-v10/privacy-final.json
git diff --check
```

Expected: every command exits 0 and privacy violations remain empty.

- [ ] **Step 6: Record the immutable verified commit**

```powershell
$verifiedCommit = git rev-parse HEAD
Set-Content -Path output/release-v10/verified-commit.txt -Value $verifiedCommit -Encoding ascii
if (git status --porcelain) { throw "Release tree is not clean" }
git show --no-patch --format="%H %s" $verifiedCommit
```

Expected: a clean tree and one exact 40-character commit SHA.

- [ ] **Step 7: Verify Vercel project identity and record current production**

Run from the repository directory containing `.vercel/project.json`:

```powershell
vercel whoami
$previous = vercel inspect https://conexion-biblica-2026.vercel.app --format=json --no-color | ConvertFrom-Json
if ($previous.readyState -ne 'READY') { throw "Current production is not READY" }
Set-Content -Path output/release-v10/previous-production.txt -Value ("https://" + $previous.url) -Encoding ascii
```

Expected: the authorized Vercel account and project are shown; inspection reports the current production deployment as Ready. Stop before any deployment if the project/team differs.

### Task 9: Deploy a protected candidate, promote, verify production, and retain rollback

**Files:**
- Consume: exact SHA in `output/release-v10/verified-commit.txt`
- Generate ephemerally: `output/release-v10/candidate-url.txt`
- Generate ephemerally: `output/release-v10/production-audit.json`
- Generate ephemerally: `output/release-v10/production-e2e.log`

**Interfaces:**
- Consumes: clean, fully verified commit and Vercel project link.
- Produces: a protected candidate verified before alias promotion, then evidence that production serves the exact public bank and no private artifact.
- Rollback: `vercel rollback <previous-deployment-url> --yes`, using the exact Ready deployment recorded in Task 8.

- [ ] **Step 1: Reconfirm the deployed checkout equals the verified SHA**

```powershell
$verifiedCommit = (Get-Content -Raw output/release-v10/verified-commit.txt).Trim()
if ((git rev-parse HEAD).Trim() -ne $verifiedCommit) { throw "HEAD changed after verification" }
if (git status --porcelain) { throw "Working tree changed after verification" }
```

Expected: no output and exit 0.

- [ ] **Step 2: Create a production-environment candidate without assigning the public domain**

```powershell
$candidateUrl = (vercel --prod --skip-domain --yes --no-color 2>&1 | Tee-Object -FilePath output/release-v10/vercel-candidate.log | Select-String -Pattern 'https://[^ ]+\.vercel\.app' | Select-Object -Last 1).Matches.Value
if (-not $candidateUrl) { throw "Vercel did not return a candidate URL" }
Set-Content -Path output/release-v10/candidate-url.txt -Value $candidateUrl -Encoding ascii
vercel inspect $candidateUrl --wait
```

Expected: candidate deployment reaches Ready; production alias is still unchanged.

- [ ] **Step 3: Verify protected candidate content and UI**

```powershell
$candidateUrl = (Get-Content -Raw output/release-v10/candidate-url.txt).Trim()
vercel curl / --deployment $candidateUrl
vercel curl /banks/final-2026/manifest.json --deployment $candidateUrl
$env:PLAYWRIGHT_BASE_URL=$candidateUrl
npx playwright test --project=desktop-chromium --project=mobile-chromium --project=desktop-firefox --project=mobile-firefox --project=desktop-webkit --project=mobile-webkit
Remove-Item Env:PLAYWRIGHT_BASE_URL
```

Expected: protected requests succeed; public manifest has no blind metadata; all six Playwright projects pass against the candidate.

- [ ] **Step 4: Run remote privacy scanning against the candidate**

```powershell
$candidateUrl = (Get-Content -Raw output/release-v10/candidate-url.txt).Trim()
python scripts/audit-blind-privacy-v11.py --private-root output/private/competitive-v11-blind --base-url $candidateUrl | Tee-Object -FilePath output/release-v10/privacy-candidate.json
```

Expected: PASS; private routes return 404 and no private presentation artifact/string appears in remote HTML, JS, CSS, manifests, source maps, service worker, or public bank resources.

- [ ] **Step 5: Promote the verified candidate to production**

```powershell
$candidateUrl = (Get-Content -Raw output/release-v10/candidate-url.txt).Trim()
vercel promote $candidateUrl --yes
vercel inspect https://conexion-biblica-2026.vercel.app --wait
```

Expected: the production alias points to the Ready candidate.

- [ ] **Step 6: Audit live production bank and private-route absence**

```powershell
$env:FINAL_BANK_BASE_URL='https://conexion-biblica-2026.vercel.app'
node scripts/audit-live-final-bank.mjs | Tee-Object -FilePath output/release-v10/production-audit.json
python scripts/audit-blind-privacy-v11.py --private-root output/private/competitive-v11-blind --base-url https://conexion-biblica-2026.vercel.app | Tee-Object -FilePath output/release-v10/privacy-production.json
Remove-Item Env:FINAL_BANK_BASE_URL
```

Expected: live public resources and hashes match the committed artifact; coverage is 2,217/2,217 plus accepted reincorporations; private audit status is intentionally `NOT_RUN` in the public live auditor; privacy scanner PASSes with private routes unavailable.

- [ ] **Step 7: Run all six browser projects against production**

```powershell
$env:PLAYWRIGHT_BASE_URL='https://conexion-biblica-2026.vercel.app'
npx playwright test --project=desktop-chromium --project=mobile-chromium --project=desktop-firefox --project=mobile-firefox --project=desktop-webkit --project=mobile-webkit 2>&1 | Tee-Object -FilePath output/release-v10/production-e2e.log
Remove-Item Env:PLAYWRIGHT_BASE_URL
```

Expected: all public training, national-final, persistence, error recovery, responsive navigation, and asset checks PASS in six projects; no blind mode or route is visible.

- [ ] **Step 8: Execute rollback immediately if any post-promotion gate fails**

Read the exact prior Ready deployment URL recorded before promotion, then run:

```powershell
$previousDeploymentUrl = (Get-Content -Raw output/release-v10/previous-production.txt).Trim()
if ($previousDeploymentUrl -notmatch '^https://[^/]+\.vercel\.app$') { throw "Invalid rollback deployment URL" }
vercel rollback $previousDeploymentUrl --yes
vercel inspect https://conexion-biblica-2026.vercel.app --wait
node scripts/audit-live-final-bank.mjs
```

Expected on rollback: the prior deployment is Ready on the production alias and the prior live-bank audit exits 0. Do not attempt an in-place content repair on production.

- [ ] **Step 9: Report final evidence without committing private or ephemeral output**

Report: verified Git SHA, candidate URL, production URL, Vercel Ready status, public presentation/fact counts, the 2,606 reconciliation status totals, private aggregate 100/100/50 and 45/30/25 results, exact Python/Node/Vitest/Playwright totals, privacy violations=0, and whether rollback was used. Classify the capability as `LOCALLY_VERIFIED` after local gates and `STAGING_VERIFIED` only after candidate checks; attach the fresh production evidence separately because the project classification vocabulary has no separate production state. Never publish or paste private IDs, stems, options, distractors, or fingerprints.

## Final Self-Review Checklist

- [ ] Every requirement in the approved spec maps to a task and executable gate above.
- [ ] A placeholder-vocabulary scan using the forbidden terms from `superpowers:writing-plans` returns no actionable matches.
- [ ] Function names and paths are consistent: `verify_release`, `simulate_private_artifact`, `load_private_signature_index`, `scan_directory`, `validate_emitted_pair`.
- [ ] No tracked report, command log, build, or deployment payload contains private presentation material.
- [ ] Production promotion occurs only after local compilation, pair validation, QC, 1,000 public seeds, private simulation, learning tests, full suites, six-project E2E, local privacy scan, and protected-candidate verification are green.
