# V10 Reserve Generalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publicar las 250 presentaciones blind V10 actuales sin eliminar contenido y construir una reserva privada nueva de 250 presentaciones HARD/EXPERT que mida generalización sobre los mismos 250 hechos entrenables.

**Architecture:** La promoción será una migración idempotente que elimina `blind_pool` de las 250 presentaciones existentes y conserva un registro inmutable de sus IDs y hechos. La reserva nueva se autorará como variantes en siete lotes bajo `content/competitive-v11/private-blind`, se compilará hacia el artefacto efímero `output/private/competitive-v11-blind` y se comparará contra todo el entrenamiento público mediante IDs, stems, sintaxis, opciones, distractores y fingerprints editoriales que excluyen identidad factual y evidencia. El compilador tratará los hechos blind como un subconjunto obligatorio de los hechos públicos, mantendrá A/B/emergencia disjuntos por `fact_id` y emitirá el banco público sin metadata ni contenido privado.

**Tech Stack:** Python 3.12 (`unittest`, `dataclasses`, `hashlib`, `json`, `pathlib`), JSON UTF-8, Node.js para auditoría de artefactos, Git y PowerShell.

**Spec:** `docs/superpowers/specs/2026-08-30-v10-cobertura-total-y-reserva-generalizacion-design.md`

## Global Constraints

- Conservar V10, su arquitectura, dificultad, simuladores, QC y despliegue.
- No eliminar ni reemplazar ninguna presentación pública existente.
- Después de la promoción, las 2,468 presentaciones V10 existentes serán públicas y los 2,217 hechos V10 serán entrenables; las reincorporaciones FACT posteriores solo pueden aumentar esos conteos.
- Crear exactamente 250 presentaciones privadas nuevas sobre los mismos 250 `fact_id` promovidos: A=100, B=100 y `emergency`=50.
- A, B y `emergency` serán disjuntos por `fact_id`; cada pool tendrá una presentación por hecho.
- A y B conservarán 45 selección, 30 completar y 25 verdadero/falso; `emergency` conservará 23/15/12.
- Cada presentación privada tendrá dificultad `hard` o `expert` y riesgo editorial explícito `high` o `critical`.
- `fact_id`, respuesta canónica, fuente y fragmento probatorio pueden coincidir entre público y privado; no forman parte del fingerprint editorial.
- IDs, `variant_id`, stems normalizados, estructura sintáctica, opciones, distractores, patrones de distractores y fingerprints editoriales deben permanecer disjuntos.
- Los distractores privados serán plausibles, de la misma categoría semántica y provenientes de hechos cercanos del mismo material, sin segunda respuesta defendible ni pistas de longitud, gramática o detalle.
- La fuente privada vivirá en `content/competitive-v11/private-blind`, quedará excluida del deploy y solo emitirá el artefacto efímero `output/private/competitive-v11-blind`; nunca se escribirá bajo `public/` ni será requisito para ejecutar la aplicación pública.
- Las 250 presentaciones privadas nuevas tendrán `role: variant`; el compilador privado no las contará como preguntas centrales.
- No desplegar hasta que promoción, compilación, QC factual/semántico/adversarial, 1,000 simulaciones, privacidad y E2E estén en verde.
- Este plan no modifica la reconciliación histórica de 2,606 FACT ni la auditoría de frontend/despliegue; consume sus artefactos como puertas de integración.

## File Map and Ownership

- `scripts/promote-blind-to-training-v11.py`: migración idempotente de las 250 presentaciones actuales al entrenamiento.
- `scripts/test_promote_blind_training_v11.py`: contrato de no eliminación, cobertura y repetibilidad de la promoción.
- `content/competitive-v11/promoted-blind-v10.json`: registro versionado de los 250 IDs, hechos y pools originales promovidos.
- `scripts/lib/competitive_v11.py`: normalización editorial, firmas, fingerprints y validación público/privado dentro del contrato canónico V11.
- `scripts/test_blind_generalization_v11.py`: pruebas unitarias de ineditud, pistas y disyunción por pool.
- `content/competitive-v11/private-blind/assignment-v2.json`: selección editorial de 250 hechos con pool, familia, dificultad, riesgo, material, capítulo y lote.
- `scripts/build-blind-generalization-manifest-v11.py`: construcción determinista del manifiesto a partir del registro promovido y decisiones editoriales.
- `scripts/test_build_blind_generalization_manifest_v11.py`: invariantes de 250 hechos y estratificación.
- `scripts/apply-private-blind-batches-v11.py`: compilación transaccional de lotes privados a preguntas y reviews canónicos.
- `scripts/test_apply_private_blind_batches_v11.py`: contrato del pipeline editorial privado.
- `content/competitive-v11/private-blind/authored-batches/blind-new-01-A-DAN1-6.json`: 24 presentaciones A de Daniel 1–6; 11/7/6.
- `content/competitive-v11/private-blind/authored-batches/blind-new-02-A-DAN7-12.json`: 26 presentaciones A de Daniel 7–12; 12/8/6.
- `content/competitive-v11/private-blind/authored-batches/blind-new-03-A-PR39-44.json`: 50 presentaciones A de PR39–44; 22/15/13.
- `content/competitive-v11/private-blind/authored-batches/blind-new-04-B-DAN1-6.json`: 23 presentaciones B de Daniel 1–6; 10/7/6.
- `content/competitive-v11/private-blind/authored-batches/blind-new-05-B-DAN7-12.json`: 27 presentaciones B de Daniel 7–12; 12/8/7.
- `content/competitive-v11/private-blind/authored-batches/blind-new-06-B-PR39-44.json`: 50 presentaciones B de PR39–44; 23/15/12.
- `content/competitive-v11/private-blind/authored-batches/blind-new-07-emergency-all.json`: 50 presentaciones `emergency`; 23/15/12.
- `content/competitive-v11/private-blind/reviews/{DAN1..DAN12,PR39..PR44}.json`: reviews canónicos por unidad.
- `content/competitive-v11/private-blind/editorial-comparisons.json`: 250 decisiones adversariales contra las presentaciones públicas del mismo hecho.
- `output/private/competitive-v11-blind`: salida privada efímera por unidad y pool; nunca se añade a Git.
- `scripts/compile-competitive-v11.py`: compilación desde raíces pública y privada separadas.
- `scripts/test_competitive_v11.py`: pruebas de conteos, cobertura, separación y artefactos.
- `scripts/audit-competitive-v11.py`: auditoría integrada factual, semántica y adversarial.
- `reports/competitive-v11/blind-generalization-audit.json`: evidencia detallada por variante.
- `reports/competitive-v11/blind-generalization-audit.md`: resumen legible y puerta de liberación.

---

### Task 1: Promote the 250 Existing Blind Presentations into Public Training

**Files:**
- Create: `scripts/promote-blind-to-training-v11.py`
- Create: `scripts/test_promote_blind_training_v11.py`
- Create: `content/competitive-v11/promoted-blind-v10.json`
- Modify: `content/competitive-v11/questions/{DAN1..DAN12,PR39..PR44}.json`
- Modify: `content/competitive-v11/reviews/{DAN1..DAN12,PR39..PR44}.json`
- Modify: only the authored batch JSON files that contain an ID listed in `content/competitive-v11/blind-assignment-v11.json`

**Interfaces:**
- Consumes: `blind-assignment-v11.json` schema 1.0 and `content_hash(row: Mapping[str, Any]) -> str` from `scripts.lib.competitive_v11`.
- Produces: `promote(content_root: Path, assignment_path: Path, registry_path: Path) -> dict[str, Any]` and registry schema `competitive-v11-promoted-blind-v1`.
- Registry row: `{question_id, fact_id, original_pool, source_unit_id, family, material, chapter, promoted_content_sha256}`.

- [ ] **Step 1: Write failing tests for additive and idempotent promotion**

```python
def test_promotes_exact_assignment_without_deleting_or_rewriting_prose(self):
    before = fixture.all_questions()
    report = promote(fixture.content_root, fixture.assignment, fixture.registry)
    after = fixture.all_questions()
    self.assertEqual(set(map(itemgetter("id"), after)), set(map(itemgetter("id"), before)))
    self.assertEqual(len(after), len(before))
    self.assertEqual(report["promoted_presentations"], 3)
    self.assertTrue(all(row["blind_pool"] is None for row in after))
    self.assertEqual(
        [{k: row[k] for k in row if k not in {"blind_pool", "ai_review"}} for row in after],
        [{k: row[k] for k in row if k not in {"blind_pool", "ai_review"}} for row in before],
    )

def test_second_promotion_is_a_byte_identical_noop(self):
    promote(fixture.content_root, fixture.assignment, fixture.registry)
    first = fixture.snapshot_bytes()
    promote(fixture.content_root, fixture.assignment, fixture.registry)
    self.assertEqual(fixture.snapshot_bytes(), first)

def test_checked_in_promotion_exposes_all_v10_facts(self):
    rows = load_questions(Path("content/competitive-v11/questions"))
    registry = read_json(Path("content/competitive-v11/promoted-blind-v10.json"))
    self.assertEqual(len(registry["presentations"]), 250)
    self.assertEqual(len({row["fact_id"] for row in registry["presentations"]}), 250)
    self.assertEqual(len(rows), 2468)
    self.assertEqual(len({row["fact_id"] for row in rows}), 2217)
    self.assertTrue(all(row["blind_pool"] is None for row in rows))
```

- [ ] **Step 2: Run the promotion tests and verify RED**

Run: `python -m unittest scripts.test_promote_blind_training_v11 -v`

Expected: FAIL because `scripts.promote_blind_to_training_v11` and the promoted registry do not exist.

- [ ] **Step 3: Implement an atomic promotion that only clears ownership metadata**

```python
def promote(content_root: Path, assignment_path: Path, registry_path: Path) -> dict[str, Any]:
    assignment = read_json(assignment_path)
    expected = {
        question_id: pool
        for pool, ids in assignment["pools"].items()
        for question_id in ids
    }
    questions = load_index(content_root / "questions", "id")
    reviews = load_index(content_root / "reviews", "question_id")
    if len(expected) != 250 or len({questions[qid]["fact_id"] for qid in expected}) != 250:
        raise ValueError("promotion requires exactly 250 unique presentations and facts")
    registry_rows = []
    for question_id, original_pool in sorted(expected.items()):
        row = questions[question_id]
        if row.get("blind_pool") not in {original_pool, None}:
            raise ValueError(f"unexpected blind_pool for {question_id}")
        row["blind_pool"] = None
        row["ai_review"] = {
            **row["ai_review"],
            "status": "passed",
            "reviewer_type": "ai_semantic_audit",
            "reviewer": "gpt-5.6-sol-v10-blind-promotion",
        }
        reviews[question_id]["content_sha256"] = content_hash(row)
        registry_rows.append(registry_row(row, original_pool))
    write_all_atomically(content_root, questions, reviews, expected)
    write_json_atomic(registry_path, {
        "contract": "competitive-v11-promoted-blind-v1",
        "presentation_count": 250,
        "fact_count": 250,
        "presentations": registry_rows,
    })
    return {"promoted_presentations": 250, "promoted_facts": 250}
```

The authored-origin update must remove only the `blind_pool` field for the same 250 IDs. It must refuse to write if any other authored field differs from the tracked `HEAD` version, following the safety pattern already used by `collect_authored_rows()` in `scripts/apply_blind_assignment_v11.py`.

- [ ] **Step 4: Run fixture tests and verify GREEN**

Run: `python -m unittest scripts.test_promote_blind_training_v11 -v`

Expected: PASS, including the byte-identical second run.

- [ ] **Step 5: Execute the checked-in migration and validate the exact base result**

Run: `python scripts/promote-blind-to-training-v11.py --content-root content/competitive-v11 --assignment content/competitive-v11/blind-assignment-v11.json --registry content/competitive-v11/promoted-blind-v10.json`

Expected stdout:

```json
{"promoted_facts": 250, "promoted_presentations": 250, "public_facts": 2217, "public_presentations": 2468}
```

Run: `python -m unittest scripts.test_promote_blind_training_v11 -v`

Expected: PASS.

- [ ] **Step 6: Review the migration diff for prohibited deletions or prose changes**

Run: `git diff --numstat -- content/competitive-v11/questions content/competitive-v11/authored-batches content/competitive-v11/reviews content/competitive-v11/promoted-blind-v10.json`

Run: `git diff --word-diff=porcelain -- content/competitive-v11/questions content/competitive-v11/authored-batches`

Expected: only `blind_pool` removal, review hash/reviewer updates, and the new registry; all 2,468 question IDs remain present.

- [ ] **Step 7: Commit the promotion independently**

```bash
git add scripts/promote-blind-to-training-v11.py scripts/test_promote_blind_training_v11.py content/competitive-v11/promoted-blind-v10.json content/competitive-v11/questions content/competitive-v11/reviews content/competitive-v11/authored-batches
git commit -m "feat: promote V10 blind questions into training"
```

### Task 2: Define Editorial Independence and Leakage-Safe Fingerprints

**Files:**
- Create: `scripts/test_blind_generalization_v11.py`
- Modify: `scripts/lib/competitive_v11.py`

**Interfaces:**
- Produces: `normalize_editorial_text(text: object) -> str`.
- Produces: `distractors(row: Mapping[str, Any]) -> tuple[str, ...]`.
- Produces: `option_shape_signature(row: Mapping[str, Any]) -> tuple[str, ...]`.
- Produces: `presentation_fingerprint(row: Mapping[str, Any]) -> str`.
- Produces: `validate_generalization_pair(public_rows, private_rows, assignment) -> dict[str, list[str]]`.
- Requires private fields: `variant_id`, `syntax_pattern`, `distractor_pattern`, `risk_tier`, `risk_tags`, `nearest_public_ids`.

- [ ] **Step 1: Write failing tests that distinguish factual overlap from editorial overlap**

```python
def test_fingerprint_excludes_shared_fact_answer_and_source(self):
    left = blind_row(question="¿Quién acudió para ayudar a Daniel?", fact_id="F-1")
    right = {**left, "fact_id": "F-9", "correct_answer": "Miguel", "source_ref": "Daniel 10:13", "source_quote": "Miguel vino para ayudarme"}
    self.assertEqual(presentation_fingerprint(left), presentation_fingerprint(right))

def test_fingerprint_changes_for_new_stem_syntax_and_distractors(self):
    public = public_row(question="¿Quién acudió para ayudar?", options=["Miguel", "Gabriel", "Ciro", "Darío"])
    private = private_row(question="¿Qué príncipe intervino cuando persistía la resistencia?", options=["Gabriel", "Miguel", "Jefe de Persia", "Jefe de Grecia"])
    self.assertNotEqual(presentation_fingerprint(public), presentation_fingerprint(private))

def test_pair_requires_shared_fact_but_disjoint_presentations(self):
    report = validate_generalization_pair([public_row(fact_id="F-1")], [private_row(fact_id="F-1")], assignment_for("F-1"))
    self.assertEqual(report, {})

def test_pair_rejects_cross_pool_fact_reuse_and_recognizable_distractor_reuse(self):
    rows = [private_row(fact_id="F-1", blind_pool="A"), private_row(fact_id="F-1", blind_pool="B")]
    report = validate_generalization_pair([public_row(fact_id="F-1")], rows, assignment_for("F-1"))
    self.assertEqual(report["cross_pool_fact_collisions"], ["F-1"])
    self.assertTrue(report["recognizable_distractor_reuse"])

def test_private_blind_requires_variant_role(self):
    row = private_row(role="central")
    self.assertIn("blind_role_must_be_variant", validate_question(row, source_units()))
```

- [ ] **Step 2: Run the fingerprint tests and verify RED**

Run: `python -m unittest scripts.test_blind_generalization_v11 -v`

Expected: FAIL because the module and functions do not exist.

- [ ] **Step 3: Implement the canonical fingerprint without factual identity fields**

```python
def presentation_fingerprint(row: Mapping[str, Any]) -> str:
    payload = {
        "stem": normalize_editorial_text(row.get("question")),
        "syntax_pattern": normalize_editorial_text(row.get("syntax_pattern")),
        "distractors": sorted(distractors(row)),
        "distractor_pattern": normalize_editorial_text(row.get("distractor_pattern")),
        "option_shape": option_shape_signature(row),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
```

`distractors()` must exclude `options[correct_option]`. `option_shape_signature()` records token-count buckets and grammatical category in displayed order but never answer text. The fingerprint must not read `fact_id`, `correct_answer`, `accepted_answers`, `source_ref`, `source_quote`, `evidence_excerpt` or `answer_support_term`.

- [ ] **Step 4: Implement the full public/private validator**

```python
def validate_generalization_pair(public_rows, private_rows, assignment):
    issues = defaultdict(list)
    public_facts = {str(row["fact_id"]) for row in public_rows}
    public_ids = {str(row["id"]) for row in public_rows}
    public_variants = {str(row.get("variant_id") or row["id"]) for row in public_rows}
    private_facts_by_pool = defaultdict(set)
    for row in private_rows:
        fact_id = str(row["fact_id"])
        if fact_id not in public_facts:
            issues["blind_fact_without_public_training"].append(fact_id)
        if row["id"] in public_ids or row["variant_id"] in public_variants:
            issues["presentation_identity_collision"].append(row["id"])
        private_facts_by_pool[row["blind_pool"]].add(fact_id)
        compare_with_public_presentations(row, public_rows, issues)
        validate_length_grammar_and_detail_balance(row, issues)
    for left, right in combinations(("A", "B", "emergency"), 2):
        issues["cross_pool_fact_collisions"].extend(sorted(private_facts_by_pool[left] & private_facts_by_pool[right]))
    validate_assignment_exactness(private_rows, assignment, issues)
    return {key: sorted(set(values)) for key, values in issues.items() if values}
```

Exact collision gates compare normalized stem, `syntax_pattern`, ordered normalized options, normalized distractor set, `distractor_pattern` and fingerprint. Recognizable reuse additionally fails when two or more of the three private distractors equal public distractors for the same fact or when `syntax_pattern` and `distractor_pattern` both match a public presentation.

- [ ] **Step 5: Require HARD/EXPERT and explicit risk only for private reserve rows**

Add to `validate_question()`:

```python
if row.get("blind_pool") is not None:
    if row.get("role") != "variant":
        errors.append("blind_role_must_be_variant")
    if row.get("difficulty") not in {"hard", "expert"}:
        errors.append("blind_difficulty_below_hard")
    if row.get("risk_tier") not in {"high", "critical"}:
        errors.append("blind_missing_risk_tier")
    if not isinstance(row.get("risk_tags"), list) or not row["risk_tags"]:
        errors.append("blind_missing_risk_tags")
    for field in ("variant_id", "syntax_pattern", "distractor_pattern", "nearest_public_ids"):
        if not row.get(field):
            errors.append(f"blind_missing_{field}")
```

Do not add these fields to the required schema for public rows.

Remove the obsolete `blind_variant_not_allowed` branch. Public questions keep the existing `central`/`variant` behavior; only rows with a non-null private pool are required to be variants.

- [ ] **Step 6: Run focused contract tests and verify GREEN**

Run: `python -m unittest scripts.test_blind_generalization_v11 scripts.test_competitive_v11.CompetitiveV11ContractTests -v`

Expected: PASS.

- [ ] **Step 7: Commit the editorial contract**

```bash
git add scripts/lib/competitive_v11.py scripts/test_blind_generalization_v11.py scripts/test_competitive_v11.py
git commit -m "feat: enforce blind editorial independence"
```

### Task 3: Build and Lock the 250-Fact Private Assignment

**Files:**
- Create: `scripts/build-blind-generalization-manifest-v11.py`
- Create: `scripts/test_build_blind_generalization_manifest_v11.py`
- Create: `content/competitive-v11/private-blind/assignment-v2.json`

**Interfaces:**
- Consumes: `content/competitive-v11/promoted-blind-v10.json`.
- Produces: `build_manifest(registry: Mapping[str, Any], decisions: Sequence[Mapping[str, Any]]) -> dict[str, Any]`.
- Manifest row: `{fact_id, public_question_id, pool, family, difficulty, risk_tier, risk_tags, material, chapter, source_unit_id, authoring_batch}`.

- [ ] **Step 1: Write failing tests for exact selection and stratification**

```python
def test_manifest_uses_every_promoted_fact_exactly_once(self):
    manifest = read_json(MANIFEST)
    rows = manifest["assignments"]
    promoted = read_json(PROMOTED)["presentations"]
    self.assertEqual(len(rows), 250)
    self.assertEqual({row["fact_id"] for row in rows}, {row["fact_id"] for row in promoted})
    self.assertEqual(len({row["fact_id"] for row in rows}), 250)

def test_pool_sizes_and_family_mixes_are_exact(self):
    expected = {
        "A": (100, {"selection": 45, "fill_choice": 30, "true_false": 25}),
        "B": (100, {"selection": 45, "fill_choice": 30, "true_false": 25}),
        "emergency": (50, {"selection": 23, "fill_choice": 15, "true_false": 12}),
    }
    assert_pool_contract(read_json(MANIFEST)["assignments"], expected)

def test_every_assignment_has_explicit_competitive_risk(self):
    for row in read_json(MANIFEST)["assignments"]:
        self.assertIn(row["difficulty"], {"hard", "expert"})
        self.assertIn(row["risk_tier"], {"high", "critical"})
        self.assertTrue(row["risk_tags"])
```

- [ ] **Step 2: Run manifest tests and verify RED**

Run: `python -m unittest scripts.test_build_blind_generalization_manifest_v11 -v`

Expected: FAIL because the builder and manifest do not exist.

- [ ] **Step 3: Implement deterministic validation and assignment emission**

```python
def build_manifest(registry, decisions):
    promoted = {row["fact_id"]: row for row in registry["presentations"]}
    by_fact = {row["fact_id"]: row for row in decisions}
    if set(by_fact) != set(promoted) or len(decisions) != 250:
        raise ValueError("decisions must cover the 250 promoted facts exactly once")
    assignments = []
    for fact_id in sorted(promoted):
        decision = validate_decision(by_fact[fact_id], promoted[fact_id])
        assignments.append({**decision, "public_question_id": promoted[fact_id]["question_id"]})
    assert_release_distribution(assignments)
    return {
        "contract": "competitive-v11-blind-generalization-assignment-v1",
        "fact_count": 250,
        "assignments": assignments,
    }
```

The 250 editorial decisions preserve each fact's original A/B/`emergency` partition from the promotion registry so the selected fact sets remain stable, but they assign a new family, difficulty and risk explicitly. Risk tags are selected from `prophetic_precision`, `speaker_addressee`, `chronology`, `quantity`, `causal_chain`, `lexical_precision`, `near_scene_confusion`, `symbol_interpretation`, `pr_narrative_detail` and `cross_source_confusion`.

- [ ] **Step 4: Encode exact seven-batch counts in validation**

```python
BATCH_REQUIREMENTS = {
    "blind-new-01-A-DAN1-6.json": (24, {"selection": 11, "fill_choice": 7, "true_false": 6}),
    "blind-new-02-A-DAN7-12.json": (26, {"selection": 12, "fill_choice": 8, "true_false": 6}),
    "blind-new-03-A-PR39-44.json": (50, {"selection": 22, "fill_choice": 15, "true_false": 13}),
    "blind-new-04-B-DAN1-6.json": (23, {"selection": 10, "fill_choice": 7, "true_false": 6}),
    "blind-new-05-B-DAN7-12.json": (27, {"selection": 12, "fill_choice": 8, "true_false": 7}),
    "blind-new-06-B-PR39-44.json": (50, {"selection": 23, "fill_choice": 15, "true_false": 12}),
    "blind-new-07-emergency-all.json": (50, {"selection": 23, "fill_choice": 15, "true_false": 12}),
}
```

The sum is A=100 at 45/30/25, B=100 at 45/30/25, and `emergency`=50 at 23/15/12.

- [ ] **Step 5: Generate and validate the checked-in manifest**

Run: `python scripts/build-blind-generalization-manifest-v11.py --promoted content/competitive-v11/promoted-blind-v10.json --output content/competitive-v11/private-blind/assignment-v2.json`

Run: `python -m unittest scripts.test_build_blind_generalization_manifest_v11 -v`

Expected: PASS with 250 unique facts, exact pool/family/batch totals, 18 source units represented according to the promoted registry, and every assignment carrying risk metadata.

- [ ] **Step 6: Commit the locked assignment**

```bash
git add scripts/build-blind-generalization-manifest-v11.py scripts/test_build_blind_generalization_manifest_v11.py content/competitive-v11/private-blind/assignment-v2.json
git commit -m "feat: lock generalization reserve assignment"
```

### Task 4: Add a Transactional Compiler for Private Editorial Batches

**Files:**
- Create: `scripts/apply-private-blind-batches-v11.py`
- Create: `scripts/test_apply_private_blind_batches_v11.py`
- Modify: `scripts/lib/author_batch_v11.py`
- Create: `content/competitive-v11/private-blind/reviews/{DAN1..DAN12,PR39..PR44}.json`

**Interfaces:**
- Consumes: public source packets, private assignment manifest and seven authored batches.
- Produces: `compile_private_batches(content_root: Path, private_root: Path, manifest_path: Path) -> dict[str, Any]`.
- Changes: `compile_authored_batch(authored_inputs, source_units, *, private_blind: bool = False) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]`.
- Preserves: `variant_id`, `syntax_pattern`, `distractor_pattern`, `risk_tier`, `risk_tags`, `nearest_public_ids`.

- [ ] **Step 1: Write failing transactional and provenance tests**

```python
def test_private_compiler_accepts_only_manifested_rows(self):
    report = compile_private_batches(fixture.content_root, fixture.private_root, fixture.manifest)
    self.assertEqual(report, {"compiled": 3, "facts": 3, "pools": {"A": 1, "B": 1, "emergency": 1}})

def test_private_compiler_rejects_wrong_fact_pool_family_or_batch(self):
    for field, value in (("fact_id", "F-OTHER"), ("blind_pool", "B"), ("family", "true_false")):
        fixture.mutate_authored(field, value)
        with self.assertRaisesRegex(ValueError, "assignment mismatch"):
            compile_private_batches(fixture.content_root, fixture.private_root, fixture.manifest)

def test_failed_batch_leaves_private_outputs_byte_identical(self):
    before = fixture.output_bytes()
    fixture.add_invalid_row()
    with self.assertRaises(ValueError):
        compile_private_batches(fixture.content_root, fixture.private_root, fixture.manifest)
    self.assertEqual(fixture.output_bytes(), before)
```

- [ ] **Step 2: Run private pipeline tests and verify RED**

Run: `python -m unittest scripts.test_apply_private_blind_batches_v11 -v`

Expected: FAIL because the private batch compiler does not exist.

- [ ] **Step 3: Extend authored compilation without weakening public validation**

```python
PRIVATE_EDITORIAL_FIELDS = (
    "variant_id", "syntax_pattern", "distractor_pattern", "risk_tier",
    "risk_tags", "nearest_public_ids",
)

def compile_authored_batch(authored_inputs, source_units, *, private_blind=False):
    questions, reviews = [], []
    for authored in authored_inputs:
        source = source_units[str(authored["source_unit_id"])]
        question = build_current_question_mapping(authored, source)
        question["role"] = "variant" if private_blind else "central"
        question["variant_justification"] = (
            authored["review"]["rationale"] if private_blind else None
        )
        if private_blind:
            for field in PRIVATE_EDITORIAL_FIELDS:
                question[field] = authored[field]
        validate_and_append(question, authored["review"], source_units, questions, reviews)
    return questions, reviews
```

`build_current_question_mapping()` and `validate_and_append()` above denote extraction of the existing inline mapping and validation blocks into two functions defined in this same task:

```python
def build_current_question_mapping(authored: Mapping[str, Any], source: Mapping[str, Any]) -> dict[str, Any]:
    options = list(authored["options"])
    correct_option = int(authored["correct_option"])
    family = str(authored["family"])
    return {
        "id": authored["id"],
        "source_unit_id": str(authored["source_unit_id"]),
        "fact_id": authored["fact_id"],
        "role": "central",
        "family": family,
        "subtype": authored["subtype"],
        "question": authored["question"],
        "options": options,
        "correct_option": correct_option,
        "correct_answer": str(options[correct_option]),
        "accepted_answers": list(authored.get("accepted_answers", [options[correct_option]])),
        "explanation": authored["explanation"],
        "why_distractors_fail": dict(authored["why_distractors_fail"]),
        "source_ref": source["source_ref"],
        "source_quote": source["source_quote"],
        "evidence_excerpt": source["source_quote"],
        "difficulty": authored["difficulty"],
        "importance": authored["importance"],
        "relation_type": authored["relation_type"],
        "option_category": authored["option_category"],
        "false_mutation": authored.get("false_mutation"),
        "blank_span": str(options[correct_option]) if family == "fill_choice" else None,
        "significance": authored.get("significance") if family == "fill_choice" else None,
        "variant_justification": None,
        "blind_pool": authored.get("blind_pool"),
        "ai_review": {
            "status": "passed",
            "reviewer_type": "ai_semantic_audit",
            "reviewer": authored["review"]["reviewer"],
        },
    }
```

Define the extracted append helper exactly as follows so public review semantics remain unchanged:

```python
def validate_and_append(question, review, source_units, questions, reviews):
    errors = validate_question(question, source_units)
    if errors:
        raise ValueError(f"{question['id']}: {', '.join(errors)}")
    questions.append(question)
    reviews.append({
        "question_id": question["id"],
        "content_sha256": content_hash(question),
        "decision": "ai_authored_and_semantically_reviewed",
        "reviewer_type": "ai_semantic_audit",
        "reviewer": review["reviewer"],
        "reasons": [review["rationale"]],
        "second_defensible_option": False,
    })
```

Default `private_blind=False` guarantees byte-compatible public behavior. Reviews record `content_sha256`, `selected_option`, `second_defensible_option`, factual support and the adversarial reviewer identity.

- [ ] **Step 4: Implement assignment-exact compilation with atomic directory replacement**

```python
def compile_private_batches(content_root, private_root, manifest_path):
    manifest = read_json(manifest_path)
    assignments = {row["fact_id"]: row for row in manifest["assignments"]}
    authored = load_authored_rows(private_root / "authored-batches")
    if len(authored) != 250 or {row["fact_id"] for row in authored} != set(assignments):
        raise ValueError("private authored rows must match all 250 assignments")
    questions, reviews = [], []
    for authored_row in authored:
        assert_assignment_match(authored_row, assignments[authored_row["fact_id"]])
        question, review = compile_one_private(authored_row, load_source_units(content_root))
        questions.append(question)
        reviews.append(review)
    validate_private_outputs(questions, reviews)
    write_private_reviews_atomically(private_root / "reviews", reviews)
    return summarize_private_outputs(questions)
```

The compiled `questions` list is returned to the release compiler in memory or reconstructed deterministically from the seven authored batches. It is not persisted beneath `content/competitive-v11/private-blind`; only source authoring, assignment, reviews and editorial comparisons are tracked. Emitted question shards exist only under `output/private/competitive-v11-blind`.

- [ ] **Step 5: Run focused public and private compiler regression tests**

Run: `python -m unittest scripts.test_apply_private_blind_batches_v11 scripts.test_authored_question scripts.test_competitive_v11.AuthoredBatchTests -v`

Expected: PASS; public authored compilation remains unchanged.

- [ ] **Step 6: Commit the private editorial pipeline**

```bash
git add scripts/apply-private-blind-batches-v11.py scripts/test_apply_private_blind_batches_v11.py scripts/lib/author_batch_v11.py
git commit -m "feat: compile private blind authoring batches"
```

### Task 5: Author the 250 New Adversarial Presentations in Seven Reviewable Lots

**Files:**
- Create: all seven files under `content/competitive-v11/private-blind/authored-batches/` listed in the File Map.
- Generate: all 18 private review shards under `content/competitive-v11/private-blind/reviews/`; question shards exist only in the ephemeral compiler output.

**Interfaces:**
- Consumes: each exact assignment from `content/competitive-v11/private-blind/assignment-v2.json` and source evidence from `content/competitive-v11/source-packets/`.
- Each row contains the full authored question contract plus `blind_pool`, `variant_id`, `syntax_pattern`, `distractor_pattern`, `risk_tier`, `risk_tags`, `nearest_public_ids` and a semantic review rationale.

- [ ] **Step 1: Author and validate lot 01 — A, Daniel 1–6**

Create 24 rows in `blind-new-01-A-DAN1-6.json`: 11 selection, 7 `fill_choice`, 6 `true_false`. For every assigned fact, inspect every public presentation with that `fact_id`, use a different interrogative or assertion structure, and source distractors from neighboring Daniel 1–6 facts of the same semantic category.

Example of the required complete shape:

```json
{
  "id": "BLIND-V10-A-DAN1-001",
  "variant_id": "BV-A-DAN1-001",
  "source_unit_id": "DAN1-V001",
  "fact_id": "DAN1-V001-F04",
  "role": "variant",
  "blind_pool": "A",
  "family": "single_choice_contextual",
  "subtype": "cause_consequence",
  "question": "Al reconstruir el avance inicial contra Jerusalén, ¿qué acción completó la llegada del rey babilónico?",
  "options": ["Estableció el sitio", "Ordenó la retirada", "Reparó las murallas", "Coronó al gobernante"],
  "correct_option": 0,
  "accepted_answers": ["Estableció el sitio", "La sitió"],
  "explanation": "La llegada de Nabucodonosor culminó en el sitio de Jerusalén.",
  "why_distractors_fail": {
    "Ordenó la retirada": "La fuente describe el avance y sitio, no una retirada.",
    "Reparó las murallas": "La acción pertenece a otra categoría narrativa.",
    "Coronó al gobernante": "No se narra una coronación en este episodio."
  },
  "difficulty": "hard",
  "importance": "high",
  "relation_type": "event_action",
  "option_category": "action",
  "syntax_pattern": "contextual_reconstruction_then_action",
  "distractor_pattern": "nearby_actions_same_semantic_category",
  "risk_tier": "high",
  "risk_tags": ["chronology", "near_scene_confusion"],
  "nearest_public_ids": ["Q-DAN1-0001"],
  "review": {
    "reviewer": "gpt-5.6-sol-v10-blind-generalization",
    "rationale": "La formulación cambia el foco sintáctico y los tres distractores respecto de la presentación pública, manteniendo una única acción respaldada."
  }
}
```

Run: `python scripts/apply-private-blind-batches-v11.py --allow-partial-batch blind-new-01-A-DAN1-6.json`

Run: `python scripts/audit-competitive-v11.py --public-root content/competitive-v11/questions --private-source-root content/competitive-v11/private-blind --assignment content/competitive-v11/private-blind/assignment-v2.json --batch blind-new-01-A-DAN1-6.json`

Expected: 24/24 pass factual, semantic, uniqueness, balance and editorial-independence gates.

Commit:

```bash
git add content/competitive-v11/private-blind/authored-batches/blind-new-01-A-DAN1-6.json
git commit -m "content: author blind A Daniel 1 to 6"
```

- [ ] **Step 2: Author and validate lot 02 — A, Daniel 7–12**

Create 26 rows in `blind-new-02-A-DAN7-12.json`: 12/8/6. Give `critical` risk to dense prophetic distinctions involving time, symbols, rulers, speakers or sequence; reject a distractor if it can be defended from the same vision.

Run: `python scripts/apply-private-blind-batches-v11.py --allow-partial-batch blind-new-02-A-DAN7-12.json`

Run: `python scripts/audit-competitive-v11.py --public-root content/competitive-v11/questions --private-source-root content/competitive-v11/private-blind --assignment content/competitive-v11/private-blind/assignment-v2.json --batch blind-new-02-A-DAN7-12.json`

Expected: 26/26 PASS and no reused fact inside A.

Commit: `git add content/competitive-v11/private-blind/authored-batches/blind-new-02-A-DAN7-12.json && git commit -m "content: author blind A Daniel 7 to 12"`

- [ ] **Step 3: Author and validate lot 03 — A, PR39–44**

Create 50 rows in `blind-new-03-A-PR39-44.json`: 22/15/13. Keep paragraph/page references out of stems; use actions, motives, consequences, comparisons and narrative order. A false V/F item changes exactly one local field and records `false_mutation`.

Run the private batch compiler and batch audit with `blind-new-03-A-PR39-44.json`.

Expected: A closes at exactly 100 unique facts and 45/30/25.

Commit: `git add content/competitive-v11/private-blind/authored-batches/blind-new-03-A-PR39-44.json && git commit -m "content: complete blind pool A"`

- [ ] **Step 4: Author and validate lot 04 — B, Daniel 1–6**

Create 23 rows in `blind-new-04-B-DAN1-6.json`: 10/7/6. Compare each row against all public presentations of its fact and against pool A; `fact_id` overlap with A is a hard failure.

Run the private batch compiler and batch audit with `blind-new-04-B-DAN1-6.json`.

Expected: 23/23 PASS and A∩B facts is empty.

Commit: `git add content/competitive-v11/private-blind/authored-batches/blind-new-04-B-DAN1-6.json && git commit -m "content: author blind B Daniel 1 to 6"`

- [ ] **Step 5: Author and validate lot 05 — B, Daniel 7–12**

Create 27 rows in `blind-new-05-B-DAN7-12.json`: 12/8/7. For symbol/interpretation questions, all four choices must be entities of the same prophetic level; for speaker/addressee questions, all choices must be plausible participants in the same scene.

Run the private batch compiler and batch audit with `blind-new-05-B-DAN7-12.json`.

Expected: 27/27 PASS and no pool contamination.

Commit: `git add content/competitive-v11/private-blind/authored-batches/blind-new-05-B-DAN7-12.json && git commit -m "content: author blind B Daniel 7 to 12"`

- [ ] **Step 6: Author and validate lot 06 — B, PR39–44**

Create 50 rows in `blind-new-06-B-PR39-44.json`: 23/15/12. Use nearby PR39–44 facts for distractors, but never transplant a true statement from another paragraph as the sole reason an assertion is false.

Run the private batch compiler and batch audit with `blind-new-06-B-PR39-44.json`.

Expected: B closes at exactly 100 unique facts and 45/30/25.

Commit: `git add content/competitive-v11/private-blind/authored-batches/blind-new-06-B-PR39-44.json && git commit -m "content: complete blind pool B"`

- [ ] **Step 7: Author and validate lot 07 — emergency, all material**

Create 50 rows in `blind-new-07-emergency-all.json`: 23/15/12. Preserve its assigned Daniel/PR and chapter distribution; compare against public, A and B. Every `fact_id` must be absent from A and B.

Run: `python scripts/apply-private-blind-batches-v11.py --content-root content/competitive-v11 --private-root content/competitive-v11/private-blind --manifest content/competitive-v11/private-blind/assignment-v2.json`

Run: `python scripts/audit-competitive-v11.py --public-root content/competitive-v11/questions --private-source-root content/competitive-v11/private-blind --assignment content/competitive-v11/private-blind/assignment-v2.json`

Expected stdout summary:

```json
{"facts":250,"presentations":250,"pools":{"A":100,"B":100,"emergency":50},"issues":0}
```

Commit:

```bash
git add content/competitive-v11/private-blind/authored-batches/blind-new-07-emergency-all.json content/competitive-v11/private-blind/reviews
git commit -m "content: complete private generalization reserve"
```

### Task 6: Compile Public and Private Corpora from Separate Roots

**Files:**
- Modify: `scripts/compile-competitive-v11.py`
- Modify: `scripts/test_competitive_v11.py`
- Modify: `scripts/lib/competitive_v11.py`

**Interfaces:**
- Change: `compile_bank(source_root: Path, output: Path, *, blind_source_root: Path | None = None, blind_output: Path | None = None, blind_requirements: dict | None = None) -> dict[str, Any]`.
- Change: `validate_artifact_pair(public_manifest, private_manifest, public_root=None, private_root=None) -> str` validates shared fact coverage rather than ownership disjunction.
- Public manifest contains public counts/shards only; private pool metadata lives only in the private manifest.

- [ ] **Step 1: Replace obsolete ownership tests with failing shared-coverage tests**

```python
def test_compiler_requires_every_blind_fact_to_be_publicly_trainable(self):
    public_rows = [self.distinct_question(suffix="TRAIN", fact_id="F-TRAIN", blind_pool=None)]
    private_rows = [self.distinct_question(suffix="A", fact_id="F-ORPHAN", blind_pool="A")]
    with self.assertRaisesRegex(ValueError, "blind fact without public training"):
        compile_separate_fixture(public_rows, private_rows)

def test_compiler_accepts_shared_fact_with_distinct_presentations(self):
    public_rows = [self.distinct_question(suffix="TRAIN", fact_id="F-SHARED", blind_pool=None)]
    private_rows = [self.adversarial_question(suffix="A", fact_id="F-SHARED", blind_pool="A")]
    public_manifest, private_manifest = compile_separate_fixture(public_rows, private_rows)
    self.assertEqual(public_manifest["training_fact_count"], 1)
    self.assertEqual(private_manifest["total_fact_count"], 1)

def test_public_manifest_and_shards_contain_no_private_metadata(self):
    public_manifest, _ = compile_separate_fixture(public_rows, private_rows)
    serialized = json.dumps(public_manifest)
    for token in ("blind_pools", "blind_fact_count", "blind_presentation_count", "A", "emergency"):
        self.assertNotIn(token, serialized)
```

- [ ] **Step 2: Run the compiler contract tests and verify RED**

Run: `python -m unittest scripts.test_competitive_v11.BlindPoolContractTests -v`

Expected: FAIL because the compiler still extracts private rows from the public source root and rejects shared facts.

- [ ] **Step 3: Load and validate public/private sources independently**

```python
public_rows = load_validated_rows(source_root)
if any(row.get("blind_pool") is not None for row in public_rows):
    raise ValueError("public source contains blind ownership")
private_rows = load_validated_rows(blind_source_root) if blind_source_root else []
if any(row.get("blind_pool") is None for row in private_rows):
    raise ValueError("private source contains training presentation")
issues = validate_generalization_pair(public_rows, private_rows, blind_requirements)
if issues:
    raise ValueError(json.dumps(issues, ensure_ascii=False, sort_keys=True))
```

- [ ] **Step 4: Correct count semantics for shared fact identities**

```python
public_fact_ids = {row["fact_id"] for row in public_rows}
private_fact_ids = {row["fact_id"] for row in private_rows}
if not private_fact_ids <= public_fact_ids:
    raise ValueError("blind fact without public training")
public_manifest["training_fact_count"] = len(public_fact_ids)
public_manifest["training_presentation_count"] = len(public_rows)
public_manifest["total_fact_count"] = len(public_fact_ids)
public_manifest["total_presentation_count"] = len(public_rows)
private_manifest["total_fact_count"] = len(private_fact_ids)
private_manifest["total_presentation_count"] = len(private_rows)
```

Do not sum public and private fact counts because all 250 private facts are deliberately public. The combined editorial presentation count is computed only in the private release report, not exposed in the public manifest.

- [ ] **Step 5: Preserve atomic pair compilation without public dependency on private delivery**

When `blind_source_root` is provided, compile both artifacts to sibling staging directories, validate the pair and replace both atomically. When omitted, compile public training alone. Never place private shard descriptors, pool names, private IDs, hashes, options or paths in the public manifest.

- [ ] **Step 6: Run compiler, pair-integrity and regression tests**

Run: `python -m unittest scripts.test_competitive_v11 scripts.test_apply_private_blind_batches_v11 scripts.test_blind_generalization_v11 -v`

Expected: PASS, including tampering, stale shard cleanup, path safety, atomic rollback and public-only compilation.

- [ ] **Step 7: Compile the checked-in release candidate locally**

Run:

```powershell
python scripts/compile-competitive-v11.py --source-root content/competitive-v11 --output .tmp/v10-public-rc --blind-source-root content/competitive-v11/private-blind --blind-output output/private/competitive-v11-blind --require-blind-release
```

Expected:

- public: at least 2,468 presentations and at least 2,217 facts, with all 250 promoted question IDs;
- private: exactly 250 presentations/facts, A=100, B=100, `emergency`=50;
- public IDs ∩ private IDs = ∅;
- private fact IDs ⊆ public fact IDs;
- A facts, B facts and `emergency` facts are pairwise disjoint.

- [ ] **Step 8: Commit the separate-root compiler**

```bash
git add scripts/compile-competitive-v11.py scripts/test_competitive_v11.py scripts/lib/competitive_v11.py
git commit -m "feat: compile shared-fact private reserve separately"
```

### Task 7: Integrate Adversarial Review and Release Gates

**Files:**
- Modify: `scripts/audit-competitive-v11.py`
- Create: `content/competitive-v11/private-blind/editorial-comparisons.json`
- Create: `reports/competitive-v11/blind-generalization-audit.json`
- Create: `reports/competitive-v11/blind-generalization-audit.md`
- Modify: `scripts/test_competitive_v11.py`

**Interfaces:**
- Consumes: public/private canonical questions, reviews, assignment manifest, FACT coverage report, 1,000-simulation report, privacy report and E2E report.
- Produces: `audit_generalization_release(...) -> dict[str, Any]` with `status: PASS | FAIL` and zero unresolved issues.
- Each editorial comparison row: `{private_id, variant_id, fact_id, nearest_public_ids, stem_overlap, syntax_overlap, option_overlap, distractor_overlap, fingerprint_overlap, answer_cue_balance, second_defensible_option, factual_support, decision, rationale, reviewer}`.

- [ ] **Step 1: Write failing release-gate tests**

```python
def test_release_gate_requires_250_individual_editorial_comparisons(self):
    with self.assertRaisesRegex(ValueError, "editorial comparisons: 249/250"):
        audit_generalization_release(fixture.with_comparisons(249))

def test_release_gate_fails_on_semantic_rephrase_even_when_hashes_differ(self):
    fixture.private[0]["question"] = "¿Quién fue el que acudió para ayudar a Daniel?"
    result = audit_generalization_release(fixture)
    self.assertIn(fixture.private[0]["id"], result["semantic_rephrase_collisions"])

def test_release_gate_accepts_shared_answer_and_evidence(self):
    result = audit_generalization_release(fixture.with_shared_answer_source_and_fact())
    self.assertEqual(result["status"], "PASS")
```

- [ ] **Step 2: Run the release-gate tests and verify RED**

Run: `python -m unittest scripts.test_competitive_v11.BlindPoolContractTests scripts.test_blind_generalization_v11 -v`

Expected: FAIL because the exhaustive editorial comparison gate is absent.

- [ ] **Step 3: Review every private presentation against all public presentations of its fact**

For each of the 250 private rows, inspect the source unit, answer support, all public stems/options/distractors for that `fact_id`, and the other private pools. Record a comparison only after confirming:

```json
{
  "stem_overlap": 0.31,
  "syntax_overlap": false,
  "option_overlap": 0.25,
  "distractor_overlap": 0.0,
  "fingerprint_overlap": false,
  "answer_cue_balance": "passed",
  "second_defensible_option": false,
  "factual_support": "passed",
  "decision": "passed",
  "reviewer": "gpt-5.6-sol-v10-blind-adversarial-review"
}
```

`option_overlap` may include the unavoidable canonical answer; `distractor_overlap` must remain below recognizable reuse and the rationale must name the changed reasoning path.

- [ ] **Step 4: Implement machine validation of the 250 review records**

```python
def validate_comparisons(private_rows, comparisons):
    by_id = {row["private_id"]: row for row in comparisons}
    if set(by_id) != {row["id"] for row in private_rows}:
        raise ValueError(f"editorial comparisons: {len(by_id)}/{len(private_rows)}")
    failures = []
    for row in private_rows:
        review = by_id[row["id"]]
        if (
            review["decision"] != "passed"
            or review["syntax_overlap"]
            or review["fingerprint_overlap"]
            or review["answer_cue_balance"] != "passed"
            or review["second_defensible_option"]
            or review["factual_support"] != "passed"
        ):
            failures.append(row["id"])
    return failures
```

- [ ] **Step 5: Require external program gates without fabricating their evidence**

The final audit reads these exact upstream reports and fails closed if absent, stale, non-PASS or built from a different public/private build ID:

- `content/competitive-v11/reconciliation/fact-ledger-v10.json` — ledger canónico con 2,606/2,606 decisiones históricas;
- `reports/competitive-v11/fact-reconciliation-summary.json` — resumen PASS y cobertura pública de todos los FACT aceptados;
- `reports/competitive-v11/national-simulations-1000.json` — 1,000 valid national simulations;
- `reports/competitive-v11/private-build-leak-audit.json` — no private IDs, stems, options, fingerprints, paths or pool metadata in public output;
- `reports/competitive-v11/e2e-release.json` — public study and simulator flows PASS.

The private authoring task reports `BLOCKED_EXTERNAL` for a missing upstream artifact; it does not write a synthetic PASS.

- [ ] **Step 6: Run the complete local content and compiler audit**

Run:

```powershell
python scripts/audit-competitive-v11.py --public-root content/competitive-v11/questions --private-source-root content/competitive-v11/private-blind --assignment content/competitive-v11/private-blind/assignment-v2.json --comparisons content/competitive-v11/private-blind/editorial-comparisons.json --report-json reports/competitive-v11/blind-generalization-audit.json --report-md reports/competitive-v11/blind-generalization-audit.md
```

Expected: 250/250 factual PASS, 250/250 semantic PASS, 250/250 adversarial PASS, no pool fact collision, exact 45/30/25 and 23/15/12, all HARD/EXPERT, all risks explicit, 2,217/2,217 base V10 facts trainable, no lost public IDs.

- [ ] **Step 7: Run the focused Python closure suite**

Run:

```powershell
python -m unittest scripts.test_promote_blind_training_v11 scripts.test_blind_generalization_v11 scripts.test_build_blind_generalization_manifest_v11 scripts.test_apply_private_blind_batches_v11 scripts.test_competitive_v11 scripts.test_authored_question scripts.test_audit_live_final_bank_integration -v
```

Expected: PASS.

- [ ] **Step 8: Inspect the final diff and counts before accepting integration**

Run: `git diff --check`

Run: `git status --short`

Run: `git diff --stat 80c3019..HEAD`

Acceptance evidence:

- the original 2,468 V10 IDs remain present;
- exactly 250 new private IDs and 250 new `variant_id` values exist;
- exactly 250 private facts, all in public training and pairwise disjoint by pool;
- no public question prose was replaced;
- the public corpus was not reduced;
- all generated reviews and hashes match canonical rows.

- [ ] **Step 9: Commit the reviewed release evidence**

```bash
git add scripts/audit-competitive-v11.py scripts/test_competitive_v11.py content/competitive-v11/private-blind/editorial-comparisons.json reports/competitive-v11/blind-generalization-audit.json reports/competitive-v11/blind-generalization-audit.md
git commit -m "test: certify V10 generalization reserve"
```

## Final Integration Order

1. Merge promotion and verify the public lower bound of 2,468 presentations/2,217 facts.
2. Merge fingerprint/validation contracts.
3. Merge the locked 250-fact manifest.
4. Merge the private batch compiler.
5. Merge seven authored lots one at a time; rerun batch audit after each.
6. Merge separate-root compilation and regenerate both local artifacts.
7. Merge the exhaustive editorial review.
8. Consume reconciliation, simulation, privacy and E2E reports only when their build IDs match.
9. Run the complete release command set and inspect the full diff.
10. Authorize deployment only from a commit where every gate reports PASS; private source and artifacts remain outside public deployment inputs.
