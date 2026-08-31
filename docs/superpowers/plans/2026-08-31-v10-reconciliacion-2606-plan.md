# V10 Reconciliation of 2,606 Historical FACTs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reconcile all 2,606 historical FACTs against V10 public training, prove target-specific public coverage for every represented detail, reincorporate every explicit askable omission, and emit deterministic JSON, CSV, and Markdown evidence without assuming a 389-item gap.

**Architecture:** A deterministic extractor reconstructs the historical universe from `Banco_Maestro_CB2026.json` through the verified 1,850/436/320 evidence routes. The canonical ledger at `content/competitive-v11/reconciliation/fact-ledger-v10.json` records one human-reviewable decision per FACT and may only accept `represented_exact`, `represented_rekeyed`, or `represented_merged` when a referenced public presentation actually tests the historical objective; otherwise the fact is reincorporated through a separately authored public shard. A final compiler validates the 2,606-row ledger, merges reincorporations without removing existing public rows, and emits machine-readable and human-readable reports whose totals are derived from the ledger.

**Tech Stack:** Python 3 standard library (`argparse`, `csv`, `dataclasses`, `hashlib`, `json`, `pathlib`, `unittest`), the existing V10 Python compiler and question contract, deterministic UTF-8 JSON/CSV/Markdown artifacts.

**Spec:** `docs/superpowers/specs/2026-08-30-v10-cobertura-total-y-reserva-generalizacion-design.md`

## Global Constraints

- Process exactly 2,606/2,606 historical FACT identities from `Banco_Maestro_CB2026.json`; never infer the review population from `2,606 - 2,217`.
- Preserve the observed extraction partition exactly: 1,850 generated-base FACTs, 436 historical singleton-FULL FACTs, and 320 historical composite-only-FULL FACTs.
- Treat Daniel 1–12 RVR1995 and Profetas y Reyes 39–44 local source packets as the only factual authorities.
- Never classify an explicit askable FACT as represented merely because it is implicit in a broader V10 fact.
- `represented_exact`, `represented_rekeyed`, and `represented_merged` require at least one extant public presentation that specifically demands the objective detail.
- Any explicit, verifiable, reasonably askable FACT without target-specific public evidence must be `reincorporated` and receive at least one new public question.
- Rarity, difficulty, and absence from historical contests are forbidden exclusion reasons.
- Keep every pre-existing public presentation ID and row; reincorporations are additive.
- Python may extract, validate, index, count, and render reports, but it must not generate question prose or adjudication prose.
- Every historical FACT receives exactly one terminal status, individualized evidence, and an individualized explanation.
- JSON, CSV, and Markdown outputs must be deterministic and must derive all category counts from the 2,606 decisions.

---

### Task 1: Reconstruct the canonical 2,606-FACT inventory

**Files:**
- Create: `scripts/lib/fact_reconciliation_v10.py`
- Create: `scripts/reconcile-facts-v10.py`
- Create: `scripts/test_fact_reconciliation_v10.py`
- Create: `content/competitive-v11/reconciliation/historical-facts.json`

**Interfaces:**
- Consumes: `Banco_Maestro_CB2026.json` with `metadata.inputs_congelados.FACT_total == 2606` and the 3,558 rows under `questions`.
- Produces: `extract_historical_facts(master: Mapping[str, Any]) -> list[dict[str, Any]]`, `inventory_sha256(rows: Sequence[Mapping[str, Any]]) -> str`, and a deterministic `historical-facts.json` object with `schema_version`, `master_sha256`, `counts`, `inventory_sha256`, and `facts`.
- Produces each fact row with the exact keys `historical_fact_id`, `material`, `chapter`, `source_ref`, `extraction_route`, `evidence_question_ids`, `candidate_prompt`, `candidate_answer`, `candidate_support`, and `candidate_source_quotes`.

- [ ] **Step 1: Write failing unit tests for the three extraction routes**

Add fixtures to `FactExtractionTests` in `scripts/test_fact_reconciliation_v10.py` that prove the precedence and uniqueness rules:

```python
def test_extracts_generated_base_before_historical_evidence(self) -> None:
    rows = extract_historical_facts(master_fixture())
    by_id = {row["historical_fact_id"]: row for row in rows}
    self.assertEqual(by_id["FACT-D01-V01-001"]["extraction_route"], "generated_base")

def test_distinguishes_singleton_and_composite_only_full_evidence(self) -> None:
    rows = extract_historical_facts(master_fixture())
    by_id = {row["historical_fact_id"]: row for row in rows}
    self.assertEqual(by_id["FACT-D01-V02-001"]["extraction_route"], "historical_singleton_full")
    self.assertEqual(by_id["FACT-D01-V03-001"]["extraction_route"], "historical_composite_only_full")

def test_rejects_a_fact_seen_only_as_partial_or_incidental(self) -> None:
    with self.assertRaisesRegex(ValueError, "no FULL evidence"):
        extract_historical_facts(master_with_partial_only_fact())
```

- [ ] **Step 2: Run the focused extraction tests and verify RED**

Run: `python -m unittest scripts.test_fact_reconciliation_v10.FactExtractionTests -v`

Expected: FAIL because `scripts.lib.fact_reconciliation_v10` and `extract_historical_facts` do not exist.

- [ ] **Step 3: Implement deterministic route classification**

In `scripts/lib/fact_reconciliation_v10.py`, implement the route order exactly as follows:

```python
EXTRACTION_ROUTES = (
    "generated_base",
    "historical_singleton_full",
    "historical_composite_only_full",
)

def extract_historical_facts(master: Mapping[str, Any]) -> list[dict[str, Any]]:
    questions = list(master["questions"])
    base = [
        row for row in questions
        if row.get("origen") == "GENERATED"
        and row.get("generation_level") != "TIER1_VARIANT"
    ]
    base_by_fact = _unique_full_fact_rows(base, require_single_full=True)
    historical = [row for row in questions if row.get("origen") == "HISTORICAL"]
    singleton = _historical_full_index(historical, full_count=1)
    all_historical_full = _historical_full_index(historical, full_count=None)
    fact_ids = sorted(set(base_by_fact) | set(all_historical_full))
    result = []
    for fact_id in fact_ids:
        if fact_id in base_by_fact:
            result.append(_fact_from_generated_base(fact_id, base_by_fact[fact_id]))
        elif fact_id in singleton:
            result.append(_fact_from_historical(fact_id, singleton[fact_id], "historical_singleton_full"))
        else:
            result.append(_fact_from_historical(fact_id, all_historical_full[fact_id], "historical_composite_only_full"))
    _assert_unique_fact_ids(result)
    return result
```

Normalize `material` to `DANIEL` or `PR`, normalize chapter to `DAN1`–`DAN12` or `PR39`–`PR44`, retain every supporting historical `QUESTION_ID`, and sort facts by `(material, numeric chapter, historical_fact_id)`.

- [ ] **Step 4: Add the real-master integration test for 2,606 = 1,850 + 436 + 320**

```python
def test_real_master_extracts_all_2606_facts_through_verified_routes(self) -> None:
    master = json.loads((ROOT / "Banco_Maestro_CB2026.json").read_text(encoding="utf-8"))
    rows = extract_historical_facts(master)
    self.assertEqual(len(rows), 2606)
    self.assertEqual(len({row["historical_fact_id"] for row in rows}), 2606)
    self.assertEqual(
        Counter(row["extraction_route"] for row in rows),
        Counter({
            "generated_base": 1850,
            "historical_singleton_full": 436,
            "historical_composite_only_full": 320,
        }),
    )
```

- [ ] **Step 5: Implement the extraction CLI and write the canonical artifact atomically**

`scripts/reconcile-facts-v10.py extract` must accept `--master`, `--output`, and `--check`. Define the CLI with required subcommands `extract`, `prepare`, `validate`, `report`, and `audit` so later tasks extend one stable tool. In write mode, serialize with `ensure_ascii=False`, `indent=2`, a trailing newline, and `Path.replace()` from a sibling `.tmp` file. In `--check` mode, compare the bytes that would be emitted and exit nonzero without changing the file when stale.

Run: `python scripts/reconcile-facts-v10.py extract --master Banco_Maestro_CB2026.json --output content/competitive-v11/reconciliation/historical-facts.json`

Expected: prints `facts=2606 generated_base=1850 historical_singleton_full=436 historical_composite_only_full=320`.

- [ ] **Step 6: Run focused and integration tests and verify GREEN**

Run: `python -m unittest scripts.test_fact_reconciliation_v10.FactExtractionTests scripts.test_fact_reconciliation_v10.RealMasterExtractionTests -v`

Expected: PASS, including byte-stable output on two consecutive runs.

- [ ] **Step 7: Commit the canonical extraction slice**

```bash
git add scripts/lib/fact_reconciliation_v10.py scripts/reconcile-facts-v10.py scripts/test_fact_reconciliation_v10.py content/competitive-v11/reconciliation/historical-facts.json
git commit -m "feat: reconstruct all 2606 historical facts"
```

### Task 2: Build a strict target-specific public-evidence index

**Files:**
- Modify: `scripts/lib/fact_reconciliation_v10.py`
- Modify: `scripts/test_fact_reconciliation_v10.py`

**Interfaces:**
- Consumes: public V10 question rows from `content/competitive-v11/questions/*.json` plus the publicized former blind rows.
- Produces: `build_public_evidence_index(rows: Sequence[Mapping[str, Any]]) -> PublicEvidenceIndex`, `find_public_candidates(fact: Mapping[str, Any], index: PublicEvidenceIndex) -> list[dict[str, Any]]`, and `validate_target_specific_evidence(fact, decision, index) -> list[str]`.
- `PublicEvidenceIndex` exposes immutable maps `by_id`, `by_fact_id`, `by_source_unit_id`, and `by_normalized_source_ref`.

- [ ] **Step 1: Write failing tests that distinguish explicit training from broad implicit coverage**

```python
def test_rejects_broad_question_that_does_not_demand_the_historical_detail(self) -> None:
    fact = historical_fact(candidate_answer="casi una hora", candidate_support="Daniel quedó atónito casi una hora")
    public = public_question(question="¿Cómo reaccionó Daniel?", correct_answer="Quedó atónito")
    decision = represented_decision(public_question_ids=[public["id"]], detail_under_test="casi una hora")
    errors = validate_target_specific_evidence(fact, decision, build_public_evidence_index([public]))
    self.assertIn("public_evidence_not_target_specific", errors)

def test_accepts_question_whose_answer_requires_the_exact_detail(self) -> None:
    fact = historical_fact(candidate_answer="casi una hora", candidate_support="Daniel quedó atónito casi una hora")
    public = public_question(question="¿Cuánto tiempo quedó atónito Daniel?", correct_answer="Casi una hora")
    decision = represented_decision(public_question_ids=[public["id"]], detail_under_test="casi una hora")
    self.assertEqual(validate_target_specific_evidence(fact, decision, build_public_evidence_index([public])), [])
```

- [ ] **Step 2: Run the evidence tests and verify RED**

Run: `python -m unittest scripts.test_fact_reconciliation_v10.PublicEvidenceTests -v`

Expected: FAIL because the evidence index and strict validator are absent.

- [ ] **Step 3: Implement candidate discovery without automatic semantic approval**

`find_public_candidates` may rank rows only when source compatibility is present. Rank by: identical normalized reference, identical source-unit evidence, canonical-answer support, and overlapping objective tokens. Return `candidate_score` and `candidate_reasons`, but never return an accepted status. A human decision must name the final public IDs.

```python
@dataclass(frozen=True)
class PublicEvidenceIndex:
    by_id: Mapping[str, Mapping[str, Any]]
    by_fact_id: Mapping[str, tuple[Mapping[str, Any], ...]]
    by_source_unit_id: Mapping[str, tuple[Mapping[str, Any], ...]]
    by_normalized_source_ref: Mapping[str, tuple[Mapping[str, Any], ...]]
```

- [ ] **Step 4: Implement the hard target-specific gate**

For every represented status, require all of the following: every cited presentation exists in the public index; at least one cited row is source-compatible; `detail_under_test` is nonempty; the detail is demanded by the combination of stem, blank span, options, and correct answer; and the decision contains an individualized `public_evidence_explanation`. A same-source row whose answer omits the objective detail must fail.

- [ ] **Step 5: Run the evidence tests and verify GREEN**

Run: `python -m unittest scripts.test_fact_reconciliation_v10.PublicEvidenceTests -v`

Expected: PASS for direct, fill-choice, and true/false target-specific fixtures; PASS for rejection of broad and merely implicit coverage.

- [ ] **Step 6: Commit the public-evidence contract**

```bash
git add scripts/lib/fact_reconciliation_v10.py scripts/test_fact_reconciliation_v10.py
git commit -m "feat: require target specific public fact evidence"
```

### Task 3: Define and validate all 2,606 individual adjudications

**Files:**
- Modify: `scripts/reconcile-facts-v10.py`
- Modify: `scripts/lib/fact_reconciliation_v10.py`
- Modify: `scripts/test_fact_reconciliation_v10.py`
- Create: `content/competitive-v11/reconciliation/composite-fact-definitions.json`
- Create: `content/competitive-v11/reconciliation/fact-ledger-v10.json`
- Create: `reports/competitive-v11/fact-reconciliation-review-packets/DAN1.json` through `reports/competitive-v11/fact-reconciliation-review-packets/PR44.json`

**Interfaces:**
- Consumes: `historical-facts.json`, current public questions, source packets, and 320 explicit composite definitions.
- Produces: `load_fact_ledger(path: Path) -> dict[str, dict[str, Any]]`, `validate_decision(fact, decision, public_index, source_units) -> list[str]`, and `validate_complete_ledger(facts, ledger, public_index, source_units, reincorporated_rows) -> list[str]`.
- Every decision has exact keys `historical_fact_id`, `status`, `historical_proposition`, `canonical_answer`, `source_ref`, `source_support`, `matched_v10_fact_ids`, `public_question_ids`, `detail_under_test`, `public_evidence_explanation`, `reason_code`, `individual_reason`, `evidence`, and `reincorporated_question_ids`.

- [ ] **Step 1: Write failing schema and state-machine tests**

```python
def test_every_historical_fact_has_exactly_one_decision(self) -> None:
    errors = validate_complete_ledger(self.facts, self.ledger, self.public_index, self.sources, [])
    self.assertIn("missing_decision:FACT-D01-V03-001", errors)

def test_represented_merged_requires_preserved_objective_and_public_test(self) -> None:
    decision = decision_fixture(status="represented_merged", public_question_ids=[], matched_v10_fact_ids=["DAN1-V001-F01"])
    self.assertIn("represented_without_public_evidence", validate_decision(self.fact, decision, self.public_index, self.sources))

def test_forbidden_exclusion_reason_is_rejected(self) -> None:
    decision = decision_fixture(status="excluded_not_factual", individual_reason="Nunca apareció históricamente")
    self.assertIn("forbidden_exclusion_rationale", validate_decision(self.fact, decision, self.public_index, self.sources))
```

- [ ] **Step 2: Run adjudication tests and verify RED**

Run: `python -m unittest scripts.test_fact_reconciliation_v10.DecisionContractTests -v`

Expected: FAIL because the decision state machine is absent.

- [ ] **Step 3: Implement terminal statuses and their evidence requirements**

```python
REPRESENTED_STATUSES = {
    "represented_exact",
    "represented_rekeyed",
    "represented_merged",
}
TERMINAL_STATUSES = REPRESENTED_STATUSES | {
    "reincorporated",
    "excluded_non_atomic",
    "excluded_reference_only",
    "excluded_ambiguous",
    "excluded_source_defect",
    "excluded_out_of_scope",
    "excluded_not_factual",
}
FORBIDDEN_EXCLUSION_TERMS = {
    "raro", "rareza", "difícil", "dificultad",
    "nunca apareció", "no ha salido", "sin historial",
}
```

Require `represented_exact` to preserve the same proposition and identity; `represented_rekeyed` to name one semantically equivalent V10 fact under another ID; and `represented_merged` to name the broader V10 fact plus a public presentation that independently tests this historical detail. Require every exclusion to cite source evidence and a fact-specific explanation. Require `reincorporated` to name one or more authored question IDs.

- [ ] **Step 4: Create and validate the 320 composite-only fact definitions**

`composite-fact-definitions.json` must contain exactly one row for each `historical_composite_only_full` identity. Each row contains `historical_fact_id`, `historical_proposition`, `canonical_answer`, `source_ref`, `source_support`, `source_question_ids`, and `reviewer`. The preparation CLI must reject copied composite prompts that do not isolate the individual FACT.

Run: `python scripts/reconcile-facts-v10.py prepare --historical-facts content/competitive-v11/reconciliation/historical-facts.json --composite-definitions content/competitive-v11/reconciliation/composite-fact-definitions.json --public-questions content/competitive-v11/questions --source-packets content/competitive-v11/source-packets --output reports/competitive-v11/fact-reconciliation-review-packets`

Expected: 18 chapter packets, 2,606 facts total, and exactly 320 accepted composite definitions.

- [ ] **Step 5: Adjudicate every chapter packet into the canonical 2,606-row ledger**

Initialize `fact-ledger-v10.json` with a top-level object containing `schema_version`, input hashes, and `facts`. For each FACT, read the exact source support, inspect every ranked public candidate, and record one terminal status directly in its ledger row. When a broader V10 fact contains the detail but no public question demands it, record `reincorporated`; do not use `represented_merged`. Store the reviewer’s explicit comparison in `public_evidence_explanation` and the factual basis in `evidence`. The chapter packets are disposable review aids; the ledger is the only adjudication source of truth.

Run after each chapter: `python scripts/reconcile-facts-v10.py validate --unit DAN1 --ledger content/competitive-v11/reconciliation/fact-ledger-v10.json --historical-facts content/competitive-v11/reconciliation/historical-facts.json --public-questions content/competitive-v11/questions --source-packets content/competitive-v11/source-packets`

Expected: `DAN1 decisions=<chapter count> missing=0 duplicate=0 invalid=0`. Repeat with the actual unit name through `PR44`.

- [ ] **Step 6: Run the complete-decision gate and verify GREEN**

Run: `python scripts/reconcile-facts-v10.py validate --all --historical-facts content/competitive-v11/reconciliation/historical-facts.json --ledger content/competitive-v11/reconciliation/fact-ledger-v10.json --public-questions content/competitive-v11/questions --source-packets content/competitive-v11/source-packets`

Expected: `decisions=2606 missing=0 duplicate=0 invalid=0`; status totals are printed from observed decisions and are not compared to 389.

- [ ] **Step 7: Commit the reviewed adjudication source of truth**

```bash
git add scripts/lib/fact_reconciliation_v10.py scripts/reconcile-facts-v10.py scripts/test_fact_reconciliation_v10.py content/competitive-v11/reconciliation/composite-fact-definitions.json content/competitive-v11/reconciliation/fact-ledger-v10.json reports/competitive-v11/fact-reconciliation-review-packets
git commit -m "content: adjudicate all 2606 historical facts"
```

### Task 4: Author and compile every required public reincorporation

**Files:**
- Create: `content/competitive-v11/reconciliation/reincorporated-questions/DAN1.json` through `content/competitive-v11/reconciliation/reincorporated-questions/PR44.json`
- Modify: `scripts/lib/fact_reconciliation_v10.py`
- Modify: `scripts/test_fact_reconciliation_v10.py`
- Modify: `scripts/compile-competitive-v11.py` in `compile_bank()` at the question-loading loop beginning near line 825
- Modify: `scripts/test_competitive_v11.py` in the `CompilerTests` test class

**Interfaces:**
- Consumes: decisions with `status == "reincorporated"`, V10 source units, and manually authored V10 question rows.
- Produces: `reincorporated_fact_id(historical_fact_id: str) -> str`, `load_reincorporated_questions(root: Path) -> list[dict[str, Any]]`, and `validate_reincorporations(facts, ledger, rows, source_units) -> list[str]`.
- `compile_bank()` appends validated reincorporation rows to the public corpus before `audit_corpus`; it never marks them blind and never removes or mutates loaded base rows.

- [ ] **Step 1: Write failing contract tests for one-to-one reincorporation coverage**

```python
def test_each_reincorporated_fact_has_a_public_question_that_tests_its_detail(self) -> None:
    errors = validate_reincorporations(self.facts, self.ledger, [], self.sources)
    self.assertIn("missing_reincorporated_question:FACT-D01-V03-001", errors)

def test_reincorporated_question_cannot_be_blind(self) -> None:
    row = reincorporated_question(blind_pool="A")
    self.assertIn("reincorporated_question_is_not_public", validate_reincorporations(self.facts, self.ledger, [row], self.sources))

def test_compiler_preserves_every_existing_public_id(self) -> None:
    manifest, emitted = compile_fixture_with_reincorporation()
    self.assertTrue(self.preexisting_ids.issubset({row["id"] for row in emitted}))
```

- [ ] **Step 2: Run reincorporation and compiler tests and verify RED**

Run: `python -m unittest scripts.test_fact_reconciliation_v10.ReincorporationTests scripts.test_competitive_v11.CompilerTests -v`

Expected: FAIL because reincorporated shards are not loaded or validated.

- [ ] **Step 3: Implement stable reincorporated identities and strict linking**

```python
def reincorporated_fact_id(historical_fact_id: str) -> str:
    if not re.fullmatch(r"FACT-[A-Z0-9-]+", historical_fact_id):
        raise ValueError(f"invalid historical FACT id: {historical_fact_id}")
    return f"V10R-{historical_fact_id}"
```

Every reincorporated question must include `historical_fact_id`, use the derived `fact_id`, reference one existing source unit, pass `validate_question`, use `blind_pool: null`, and be cited by its decision’s `reincorporated_question_ids`. Reject orphan questions and duplicate historical links.

- [ ] **Step 4: Author the additive public questions from source evidence**

For every observed `reincorporated` decision, write at least one question in its chapter shard. The stem must directly demand `detail_under_test`, the correct answer must be uniquely supported, and distractors must be plausible facts from the same material. Reuse the complete V10 row schema, set `role` to `central`, set `difficulty` to `hard` or `expert`, and record an AI semantic review plus an independent factual review before acceptance.

Run after authoring: `python scripts/reconcile-facts-v10.py validate --reincorporations --ledger content/competitive-v11/reconciliation/fact-ledger-v10.json --questions content/competitive-v11/reconciliation/reincorporated-questions --source-packets content/competitive-v11/source-packets`

Expected: `reincorporated_facts=<derived count> covered=<same derived count> invalid=0 orphan=0`.

- [ ] **Step 5: Modify `compile_bank()` to append the separate public shards**

Immediately after loading the 18 base `questions/<unit>.json` shards, load `reconciliation/reincorporated-questions/<unit>.json` when present, validate those rows with the same source map, append them to the public rows, and preserve a pre-append set of IDs. Before emission, assert that this set remains a subset of emitted public IDs.

- [ ] **Step 6: Run focused compiler tests and verify GREEN**

Run: `python -m unittest scripts.test_fact_reconciliation_v10.ReincorporationTests scripts.test_competitive_v11.CompilerTests -v`

Expected: PASS; a missing required reincorporation fails closed and no pre-existing public ID disappears.

- [ ] **Step 7: Commit the additive public training slice**

```bash
git add content/competitive-v11/reconciliation/reincorporated-questions scripts/lib/fact_reconciliation_v10.py scripts/test_fact_reconciliation_v10.py scripts/compile-competitive-v11.py scripts/test_competitive_v11.py
git commit -m "feat: add required historical fact training"
```

### Task 5: Emit the exhaustive JSON, CSV, Markdown, and special-case reports

**Files:**
- Modify: `scripts/reconcile-facts-v10.py`
- Modify: `scripts/lib/fact_reconciliation_v10.py`
- Modify: `scripts/test_fact_reconciliation_v10.py`
- Create: `reports/competitive-v11/fact-reconciliation.json`
- Create: `reports/competitive-v11/fact-reconciliation.csv`
- Create: `reports/competitive-v11/fact-reconciliation.md`
- Create: `reports/competitive-v11/fact-reconciliation-special-cases.json`
- Create: `reports/competitive-v11/fact-reconciliation-reincorporated.md`

**Interfaces:**
- Consumes: the canonical historical inventory, all decisions, public evidence index, and compiled reincorporated rows.
- Produces: `build_reconciliation_ledger(...) -> dict[str, Any]`, `render_reconciliation_csv(ledger) -> str`, `render_reconciliation_markdown(ledger) -> str`, and `render_reincorporated_markdown(ledger) -> str`.
- The JSON root contains `schema_version`, source hashes, `counts`, `by_material`, `by_chapter`, `by_status`, `facts`, and `special_cases`; `facts` contains exactly 2,606 ordered rows.

- [ ] **Step 1: Write failing tests for exhaustive, derived, deterministic reports**

```python
def test_ledger_has_2606_rows_and_status_totals_are_derived(self) -> None:
    ledger = build_real_ledger()
    self.assertEqual(len(ledger["facts"]), 2606)
    self.assertEqual(sum(ledger["by_status"].values()), 2606)
    self.assertEqual(ledger["counts"]["historical_facts"], 2606)
    self.assertNotIn("expected_excluded_count", ledger["counts"])

def test_special_cases_are_a_derived_subset(self) -> None:
    ledger = build_fixture_ledger()
    expected = {"represented_rekeyed", "represented_merged", "reincorporated", "excluded_ambiguous"}
    self.assertEqual({row["status"] for row in ledger["special_cases"]}, expected)

def test_report_renderers_are_byte_stable(self) -> None:
    ledger = build_fixture_ledger()
    self.assertEqual(render_reconciliation_csv(ledger), render_reconciliation_csv(ledger))
    self.assertEqual(render_reconciliation_markdown(ledger), render_reconciliation_markdown(ledger))
```

- [ ] **Step 2: Run report tests and verify RED**

Run: `python -m unittest scripts.test_fact_reconciliation_v10.ReportTests -v`

Expected: FAIL because ledger and renderers do not exist.

- [ ] **Step 3: Implement the exact 2,606-row ledger schema**

Each final row must contain: `historical_fact_id`, `material`, `chapter`, `source_ref`, `historical_proposition`, `canonical_answer`, `source_support`, `extraction_route`, `matched_v10_fact_ids`, `public_question_ids`, `status`, `reason_code`, `individual_reason`, `detail_under_test`, `public_evidence_explanation`, `evidence`, and `reincorporated_question_ids`. Sort by material, numeric chapter, then FACT ID. Refuse to render if any validator error remains.

- [ ] **Step 4: Implement CSV and Markdown views from the ledger only**

Write UTF-8 CSV with a fixed header matching the row schema; encode list fields as JSON arrays inside CSV cells. The Markdown report must contain overall counts, per-material and per-chapter tables, per-status totals, the derived special-case section, and a section listing every exclusion with its individualized reason. The reincorporation report must list every new question ID, its historical FACT, source, tested detail, and public stem.

- [ ] **Step 5: Generate all five reports atomically**

Run: `python scripts/reconcile-facts-v10.py report --historical-facts content/competitive-v11/reconciliation/historical-facts.json --ledger content/competitive-v11/reconciliation/fact-ledger-v10.json --public-questions content/competitive-v11/questions --reincorporated-questions content/competitive-v11/reconciliation/reincorporated-questions --source-packets content/competitive-v11/source-packets --output-dir reports/competitive-v11`

Expected: prints `ledger=2606 special_cases=<derived count> reincorporated=<derived count> invalid=0` and writes the five declared files.

- [ ] **Step 6: Run report tests and stale-artifact check and verify GREEN**

Run: `python -m unittest scripts.test_fact_reconciliation_v10.ReportTests -v`

Run: `python scripts/reconcile-facts-v10.py report --check --historical-facts content/competitive-v11/reconciliation/historical-facts.json --ledger content/competitive-v11/reconciliation/fact-ledger-v10.json --public-questions content/competitive-v11/questions --reincorporated-questions content/competitive-v11/reconciliation/reincorporated-questions --source-packets content/competitive-v11/source-packets --output-dir reports/competitive-v11`

Expected: both PASS; `--check` reports `stale=0` and modifies no files.

- [ ] **Step 7: Commit the exhaustive reconciliation reports**

```bash
git add scripts/lib/fact_reconciliation_v10.py scripts/reconcile-facts-v10.py scripts/test_fact_reconciliation_v10.py reports/competitive-v11/fact-reconciliation.json reports/competitive-v11/fact-reconciliation.csv reports/competitive-v11/fact-reconciliation.md reports/competitive-v11/fact-reconciliation-special-cases.json reports/competitive-v11/fact-reconciliation-reincorporated.md
git commit -m "docs: publish exhaustive 2606 fact reconciliation"
```

### Task 6: Add a fail-closed reconciliation gate to V10 compilation

**Files:**
- Modify: `scripts/compile-competitive-v11.py` in `compile_bank()` before staging public output
- Modify: `scripts/test_competitive_v11.py` in `CompilerTests`
- Modify: `scripts/test_fact_reconciliation_v10.py`
- Modify: `scripts/reconcile-facts-v10.py`

**Interfaces:**
- Consumes: every source artifact and report from Tasks 1–5.
- Produces: `audit_reconciliation(root: Path, public_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]` with `valid`, `historical_fact_count`, `decision_count`, `status_counts`, `reincorporated_count`, `errors`, and input hashes.
- `compile_bank()` raises `ValueError("reconciliation gate failed: ...")` before writing staging output when `valid` is false.

- [ ] **Step 1: Write failing tamper and stale-report integration tests**

```python
def test_gate_rejects_a_missing_decision_before_public_write(self) -> None:
    remove_one_decision(self.fixture_root)
    with self.assertRaisesRegex(ValueError, "missing_decision"):
        compile_bank(self.fixture_root, self.public_output)
    self.assertFalse(self.public_output.exists())

def test_gate_rejects_report_hash_drift(self) -> None:
    mutate_report_without_updating_inputs(self.fixture_root)
    result = audit_reconciliation(self.fixture_root, self.public_rows)
    self.assertIn("stale_reconciliation_report", result["errors"])

def test_gate_rejects_represented_fact_after_its_public_evidence_is_removed(self) -> None:
    remove_cited_public_question(self.fixture_root)
    result = audit_reconciliation(self.fixture_root, self.public_rows)
    self.assertTrue(any(error.startswith("missing_public_evidence") for error in result["errors"]))
```

- [ ] **Step 2: Run gate tests and verify RED**

Run: `python -m unittest scripts.test_fact_reconciliation_v10.ReconciliationGateTests scripts.test_competitive_v11.CompilerTests -v`

Expected: FAIL because compilation does not yet enforce reconciliation.

- [ ] **Step 3: Implement the read-only audit CLI and compiler gate**

The audit must re-extract the historical inventory in memory, compare its digest to the committed artifact, load all 2,606 decisions, rebuild target-specific evidence against the actual public rows being compiled, validate reincorporations, rebuild the report digests, and return all errors. It must never trust summary counts stored in a report.

`scripts/reconcile-facts-v10.py audit` accepts `--root` and `--json`; exit 0 only when every invariant passes. `compile_bank()` invokes the same library function before emitting files.

- [ ] **Step 4: Run focused gate tests and verify GREEN**

Run: `python -m unittest scripts.test_fact_reconciliation_v10.ReconciliationGateTests scripts.test_competitive_v11.CompilerTests -v`

Expected: PASS for valid fixtures and fail-closed behavior for missing, duplicated, stale, broad-evidence, and orphan-reincorporation cases.

- [ ] **Step 5: Run the real 2,606-fact audit**

Run: `python scripts/reconcile-facts-v10.py audit --root . --json`

Expected: JSON with `"valid": true`, `"historical_fact_count": 2606`, `"decision_count": 2606`, and `"errors": []`; status counts remain derived values.

- [ ] **Step 6: Compile a disposable public/private pair with the reconciliation gate active**

Run: `python scripts/compile-competitive-v11.py --source-root content/competitive-v11 --output .tmp-reconciliation-public --blind-output .tmp-reconciliation-private --require-blind-release`

Expected: exit 0; the public count is at least the pre-reconciliation public count plus the derived number of reincorporated questions, and the compiler reports no lost pre-existing IDs.

- [ ] **Step 7: Run the complete Python regression set for this subsystem**

Run: `python -m unittest scripts.test_fact_reconciliation_v10 scripts.test_competitive_v11 scripts.test_apply_blind_assignment_v11 scripts.test_audit_live_final_bank_integration -v`

Expected: PASS with zero failures and zero errors.

- [ ] **Step 8: Review the final reconciliation diff and commit the gate**

Run: `git diff --check`

Run: `git status --short`

Verify that no file under `public/` was manually edited, no base public question row was deleted, the committed ledger has 2,606 rows, and every generated report hash is current.

```bash
git add scripts/reconcile-facts-v10.py scripts/compile-competitive-v11.py scripts/test_competitive_v11.py scripts/test_fact_reconciliation_v10.py
git commit -m "test: gate V10 on exhaustive fact reconciliation"
```

## Final evidence required before the parent V10 program may deploy

- [ ] `historical-facts.json` contains 2,606 unique IDs and route counts 1,850/436/320.
- [ ] `fact-ledger-v10.json` contains exactly 2,606 unique terminal decisions.
- [ ] Every represented decision passes the target-specific public-evidence validator.
- [ ] Every reincorporated decision has at least one compiled public question and no blind assignment.
- [ ] Every exclusion has an allowed reason code, individualized prose, and source evidence.
- [ ] JSON, CSV, Markdown, special-case, and reincorporation reports are byte-current.
- [ ] All pre-existing public presentation IDs remain present after compilation.
- [ ] The reconciliation audit and focused regression suite pass with fresh evidence.
- [ ] Deployment remains outside this plan and must wait for the parent program’s blind privacy, 1,000-simulation, E2E, and production gates.
