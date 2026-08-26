#!/usr/bin/env python3
"""Genera el sistema editorial masivo desde MaterialConexionBiblica (1).pdf."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import fitz

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts.lib.massive_bank import BANK_TARGETS, MassiveQuestion, validate_massive_bank
from scripts.lib.massive_generator import (
    FILL_STEMS,
    MC_STEMS,
    TF_STEMS,
    extract_daniel_units,
    extract_pr_units,
    generate_questions_for_specs,
    normalized_text,
)


def json_bytes(value: Any, *, pretty: bool = False) -> bytes:
    text = json.dumps(
        value,
        ensure_ascii=False,
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    ) + "\n"
    return text.encode("utf-8")


def write_json(path: Path, value: Any, *, pretty: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(value, pretty=pretty))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "id", "fact_id", "variant_id", "template_id", "bank", "chapter",
        "verse_or_page", "source_span", "type", "difficulty", "topic",
        "context_anchor", "question", "options", "correct_option", "correct_answer",
        "accepted_answers", "answer_mode", "explanation", "why_distractors_fail",
        "source_quote", "trap_type", "blind_final_pool", "validation_status",
        "incorrect_detail", "correction",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            value = {field: row.get(field) for field in fields}
            for field in ("options", "accepted_answers", "why_distractors_fail"):
                value[field] = json.dumps(value[field], ensure_ascii=False)
            writer.writerow(value)


def counts(questions: list[MassiveQuestion]) -> dict[str, Any]:
    mc = [question for question in questions if question.type == "multiple_choice"]
    four = [question for question in questions if len(question.options) == 4]
    facts = Counter(question.fact_id for question in questions)
    return {
        "total": len(questions),
        "by_chapter": dict(sorted(Counter(question.chapter for question in questions).items())),
        "by_type": dict(Counter(question.type for question in questions)),
        "by_difficulty": dict(Counter(question.difficulty for question in questions)),
        "correct_option_abcd": dict(Counter("ABCD"[question.correct_option or 0] for question in four)),
        "true_false_answers": dict(Counter(question.correct_answer for question in questions if question.type == "true_false")),
        "contextual_traps": sum(question.trap_type == "true_elsewhere" for question in mc),
        "contextual_trap_ratio": round(sum(question.trap_type == "true_elsewhere" for question in mc) / len(mc), 4),
        "blind_questions": sum(question.blind_final_pool for question in questions),
        "blind_ratio": round(sum(question.blind_final_pool for question in questions) / len(questions), 4),
        "atomic_facts": len(facts),
        "average_variants_per_fact": round(len(questions) / len(facts), 3),
        "variant_range": [min(facts.values()), max(facts.values())],
    }


def source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shard_bank(
    public_root: Path,
    questions: list[MassiveQuestion],
    facts: list,
) -> list[dict[str, Any]]:
    fact_by_chapter: dict[str, list] = defaultdict(list)
    for fact in facts:
        fact_by_chapter[fact.chapter].append(fact)
    question_by_chapter: dict[str, list[MassiveQuestion]] = defaultdict(list)
    for question in questions:
        question_by_chapter[question.chapter].append(question)
    shards: list[dict[str, Any]] = []
    for chapter in sorted(question_by_chapter, key=lambda value: (value.startswith("PR"), int("".join(c for c in value if c.isdigit())))):
        question_file = public_root / "questions" / f"{chapter}.json"
        fact_file = public_root / "facts" / f"{chapter}.json"
        question_records = [question.as_record() for question in question_by_chapter[chapter]]
        fact_records = [fact.as_record() for fact in fact_by_chapter[chapter]]
        write_json(question_file, question_records)
        write_json(fact_file, fact_records)
        shards.append(
            {
                "chapter": chapter,
                "bank": question_records[0]["bank"],
                "question_count": len(question_records),
                "fact_count": len(fact_records),
                "questions_file": question_file.relative_to(public_root.parent.parent).as_posix(),
                "facts_file": fact_file.relative_to(public_root.parent.parent).as_posix(),
                "questions_sha256": source_hash(question_file),
                "facts_sha256": source_hash(fact_file),
                "bytes": question_file.stat().st_size + fact_file.stat().st_size,
            }
        )
    return shards


def validate_readback(
    public_root: Path,
    manifest: dict[str, Any],
    expected_questions: list[MassiveQuestion],
) -> list[str]:
    errors: list[str] = []
    readback: list[dict[str, Any]] = []
    for shard in manifest["shards"]:
        path = public_root.parent.parent / shard["questions_file"]
        if not path.exists():
            errors.append(f"missing shard: {path}")
            continue
        rows = json.loads(path.read_text(encoding="utf-8"))
        if len(rows) != shard["question_count"]:
            errors.append(f"{shard['chapter']}: readback count")
        if source_hash(path) != shard["questions_sha256"]:
            errors.append(f"{shard['chapter']}: checksum")
        readback.extend(rows)
    if len(readback) != len(expected_questions):
        errors.append(f"readback total: {len(readback)}/{len(expected_questions)}")
    if len({row["id"] for row in readback}) != len(readback):
        errors.append("duplicate ids after readback")
    if len({row["variant_id"] for row in readback}) != len(readback):
        errors.append("duplicate variant ids after readback")
    if any(row["validation_status"] != "verified" for row in readback):
        errors.append("unverified record after readback")
    if any(not row["source_quote"] or not row["correct_answer"] for row in readback):
        errors.append("missing quote or answer after readback")
    if {row["id"] for row in readback} != {question.id for question in expected_questions}:
        errors.append("readback id mismatch")
    return errors


def build_audit(
    pdf_name: str,
    sha256: str,
    daniel: list[MassiveQuestion],
    pr: list[MassiveQuestion],
    dan_meta: dict[str, Any],
    pr_meta: dict[str, Any],
    total_templates: int,
    unique_distractors: int,
) -> str:
    dan_stats = counts(daniel)
    pr_stats = counts(pr)
    total = len(daniel) + len(pr)
    return f"""# Auditoría de bancos masivos

Fuente única: `{pdf_name}` (SHA-256 `{sha256}`). No se consultó internet ni otra traducción para generar contenido.

## Resultado

- Preguntas estáticas verificadas: {total:,}.
- Daniel 1–12: {len(daniel):,}.
- Profetas y Reyes 39–44: {len(pr):,}.
- Hechos atómicos seleccionados: {dan_stats['atomic_facts'] + pr_stats['atomic_facts']:,}.
- Variantes por hecho: Daniel {dan_stats['variant_range']} (promedio {dan_stats['average_variants_per_fact']}); PR {pr_stats['variant_range']} (promedio {pr_stats['average_variants_per_fact']}).
- Plantillas: {total_templates} ({len(set(q.template_id for q in daniel + pr))} estáticas y {total_templates - len(set(q.template_id for q in daniel + pr))} de reescritura controlada en tiempo de ejecución).
- Distractores dinámicos únicos: {unique_distractors:,} ({dan_meta['dynamic_distractors'] + pr_meta['dynamic_distractors']:,} entradas antes de deduplicar entre bancos).
- Candidatos o spans descartados: {dan_meta['rejected'] + pr_meta['rejected']:,}.
- Duplicados textuales o `variant_id` conservados: 0.
- Preguntas sin cita, respuesta o validación: 0.

## Daniel 1–12

- Por capítulo: `{json.dumps(dan_stats['by_chapter'], ensure_ascii=False)}`.
- Por tipo: `{json.dumps(dan_stats['by_type'], ensure_ascii=False)}`.
- Por dificultad: `{json.dumps(dan_stats['by_difficulty'], ensure_ascii=False)}`.
- V/F: `{json.dumps(dan_stats['true_false_answers'], ensure_ascii=False)}`.
- Posiciones A/B/C/D: `{json.dumps(dan_stats['correct_option_abcd'], ensure_ascii=False)}`.
- Trampas contextuales de selección múltiple: {dan_stats['contextual_traps']} ({dan_stats['contextual_trap_ratio']:.0%}).
- Reserva ciega: {dan_stats['blind_questions']} ({dan_stats['blind_ratio']:.1%}).

## Profetas y Reyes 39–44

- Por capítulo: `{json.dumps(pr_stats['by_chapter'], ensure_ascii=False)}`.
- Por tipo: `{json.dumps(pr_stats['by_type'], ensure_ascii=False)}`.
- Por dificultad: `{json.dumps(pr_stats['by_difficulty'], ensure_ascii=False)}`.
- V/F: `{json.dumps(pr_stats['true_false_answers'], ensure_ascii=False)}`.
- Posiciones A/B/C/D: `{json.dumps(pr_stats['correct_option_abcd'], ensure_ascii=False)}`.
- Trampas contextuales de selección múltiple: {pr_stats['contextual_traps']} ({pr_stats['contextual_trap_ratio']:.0%}).
- Reserva ciega: {pr_stats['blind_questions']} ({pr_stats['blind_ratio']:.1%}).

## Pruebas editoriales automáticas

Cada registro pasó comprobación de esquema, fuente y cita no vacías, una sola respuesta marcada, opciones distintas, respuesta presente una sola vez, cuota por capítulo/tipo/dificultad, reserva ciega, identidad única y ausencia de duplicado textual normalizado. Las falsas registran el detalle alterado y la corrección; completar conserva contexto; la selección contextual explica por qué cada distractor pertenece a otra unidad de la fuente.

## Cobertura reforzada

- Daniel 7, 8, 9 y 11 reciben las cuotas más altas; Daniel 11 es el capítulo de mayor tamaño.
- Daniel 1–6 conserva cobertura de todos sus versículos y escenas.
- PR43 mantiene menos de 35 % de su cuota en páginas 47–49 por selección estratificada de unidades; páginas 52–54 permanecen incluidas.
- PR44 mantiene menos de 45 % de su cuota en páginas 55–57; páginas 58–59 permanecen incluidas.

## Límite editorial

El banco se detiene en 14,000 preguntas estáticas porque las siguientes variantes disponibles repetirían la misma capacidad con cambios superficiales de enunciado. La expansión adicional queda en el motor dinámico de distractores y barajado, sin declarar nuevas preguntas estáticas como hechos distintos.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", default="MaterialConexionBiblica (1).pdf")
    parser.add_argument("--output", default="output/bancos_masivos_pdf")
    parser.add_argument("--public", default="public/banks/massive-v5")
    args = parser.parse_args()
    pdf_path = Path(args.pdf).resolve()
    output_root = Path(args.output).resolve()
    public_root = Path(args.public).resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)
    document = fitz.open(pdf_path)
    if len(document) != 60:
        raise ValueError(f"Se esperaban 60 páginas; se encontraron {len(document)}")
    sha256 = source_hash(pdf_path)

    daniel_questions, daniel_facts, dan_meta = generate_questions_for_specs(
        extract_daniel_units(document),
        bank="DANIEL1-12",
        chapter_targets=BANK_TARGETS["DANIEL1-12"]["chapters"],
    )
    pr_questions, pr_facts, pr_meta = generate_questions_for_specs(
        extract_pr_units(document),
        bank="PR39-44",
        chapter_targets=BANK_TARGETS["PR39-44"]["chapters"],
    )
    errors = validate_massive_bank(
        daniel_questions,
        expected_total=BANK_TARGETS["DANIEL1-12"]["total"],
        expected_chapters=BANK_TARGETS["DANIEL1-12"]["chapters"],
    ) + validate_massive_bank(
        pr_questions,
        expected_total=BANK_TARGETS["PR39-44"]["total"],
        expected_chapters=BANK_TARGETS["PR39-44"]["chapters"],
    )
    if errors:
        raise ValueError("Validación editorial fallida:\n- " + "\n- ".join(errors[:100]))

    public_root.mkdir(parents=True, exist_ok=True)
    all_questions = daniel_questions + pr_questions
    all_facts = daniel_facts + pr_facts
    shards = shard_bank(public_root, all_questions, all_facts)
    templates = {
        "fill_blank": [{"id": f"fill-context-v{i + 1}", "stem": stem} for i, stem in enumerate(FILL_STEMS)],
        "multiple_choice": [{"id": f"mc-contextual-v{i + 1}", "stem": stem} for i, stem in enumerate(MC_STEMS)],
        "sequence_choice": [{"id": "mc-sequence-v1", "stem": "Orden de tres detalles consecutivos"}],
        "true_false": [{"id": f"tf-single-detail-v{i + 1}", "stem": stem} for i, stem in enumerate(TF_STEMS)],
    }
    distractors: dict[str, list[dict[str, str]]] = defaultdict(list)
    seen_distractors: set[tuple[str, str]] = set()
    for fact in all_facts:
        key = (fact.category, normalized_text(fact.answer))
        if key in seen_distractors:
            continue
        seen_distractors.add(key)
        distractors[fact.category].append(
            {
                "text": fact.answer,
                "fact_id": fact.fact_id,
                "chapter": fact.chapter,
                "source": fact.verse_or_page,
            }
        )
    write_json(public_root / "templates.json", templates, pretty=True)
    write_json(public_root / "distractors.json", distractors)

    manifest = {
        "schema_version": "5.0",
        "profile_id": "massive-v5",
        "generated_at": "2026-08-26",
        "source": {"file": pdf_path.name, "sha256": sha256, "pages": len(document)},
        "totals": {
            "questions": len(all_questions),
            "facts": len(all_facts),
            "templates": sum(len(values) for values in templates.values()),
            "distractors": sum(len(values) for values in distractors.values()),
        },
        "banks": {
            "DANIEL1-12": counts(daniel_questions),
            "PR39-44": counts(pr_questions),
        },
        "templates_file": "banks/massive-v5/templates.json",
        "distractors_file": "banks/massive-v5/distractors.json",
        "shards": shards,
    }
    write_json(public_root / "manifest.json", manifest, pretty=True)

    output_root.mkdir(parents=True, exist_ok=True)
    daniel_records = [question.as_record() for question in daniel_questions]
    pr_records = [question.as_record() for question in pr_questions]
    write_jsonl(output_root / "daniel1_12_8000.jsonl", daniel_records)
    write_jsonl(output_root / "pr39_44_6000.jsonl", pr_records)
    write_csv(output_root / "daniel1_12_8000.csv", daniel_records)
    write_csv(output_root / "pr39_44_6000.csv", pr_records)
    write_jsonl(output_root / "hechos_atomicos.jsonl", [fact.as_record() for fact in all_facts])
    write_json(output_root / "plantillas.json", templates, pretty=True)
    write_json(output_root / "distractores.json", distractors)
    stats = {
        "source": manifest["source"],
        "final": manifest["totals"],
        "DANIEL1-12": {**counts(daniel_questions), **dan_meta},
        "PR39-44": {**counts(pr_questions), **pr_meta},
        "validation": {
            "errors": 0,
            "duplicate_ids": 0,
            "duplicate_variant_ids": 0,
            "duplicate_question_texts": 0,
            "missing_quotes": 0,
            "missing_answers": 0,
            "unverified": 0,
        },
    }
    write_json(output_root / "estadisticas_bancos_masivos.json", stats, pretty=True)
    (output_root / "auditoria_bancos_masivos.md").write_text(
        build_audit(
            pdf_path.name,
            sha256,
            daniel_questions,
            pr_questions,
            dan_meta,
            pr_meta,
            manifest["totals"]["templates"],
            manifest["totals"]["distractors"],
        ),
        encoding="utf-8",
    )
    (output_root / "errores_o_dudas_de_fuente.md").write_text(
        "# Errores o dudas de fuente\n\n"
        "- Daniel 5:18: la página PDF 13 muestra visualmente `8` entre los versículos 17 y 19; se restituyó `18` por continuidad inequívoca.\n"
        "- Daniel 7:13: el numeral no queda asociado al inicio de la página 17 en la extracción; se restituyó por continuidad entre 7:12 y 7:14, verificada visualmente.\n"
        "- No se modernizó la terminología de Profetas y Reyes ni se añadieron identificaciones históricas a Daniel 11.\n",
        encoding="utf-8",
    )
    readback_errors = validate_readback(public_root, manifest, all_questions)
    if readback_errors:
        raise ValueError("Validación de archivos escritos fallida:\n- " + "\n- ".join(readback_errors))
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
