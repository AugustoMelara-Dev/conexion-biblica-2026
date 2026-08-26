from collections import Counter
import json
from pathlib import Path

try:
    from scripts.lib.gold_quality import build_consolidation_bank
except ModuleNotFoundError:  # Ejecución directa: python scripts/audit-gold-bank.py
    from lib.gold_quality import build_consolidation_bank


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output/consolidacion_final"


def main() -> None:
    result = build_consolidation_bank(ROOT)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report = result["report"]
    (OUTPUT / "auditoria_calidad.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    reasons = report["rejections_by_reason"]
    chapters = report["gold_by_chapter"]
    templates = report["quarantine_by_template"]
    lines = [
        "# Rescate editorial V5 - Consolidación Final",
        "",
        f"- Registros originales preservados: {report['original_records_preserved']}",
        f"- Preguntas GOLD activas: {report['gold_questions']}",
        f"- Hechos GOLD: {report['gold_facts']}",
        f"- Variantes promedio por hecho: {report['average_variants_per_fact']}",
        f"- SILVER conservadas para edición: {report['final_status_counts'].get('silver', 0)}",
        f"- QUARANTINE fuera de producción: {report['final_status_counts'].get('quarantine', 0)}",
        "",
        "## GOLD por capítulo",
        "",
        *[f"- {chapter}: {count}" for chapter, count in chapters.items()],
        "",
        "## Cuarentena por razón",
        "",
        *[f"- {reason}: {count}" for reason, count in reasons.items()],
        "",
        "## Cuarentena por template",
        "",
        *[f"- {template}: {count}" for template, count in sorted(templates.items())],
        "",
        "`mc-sequence-v1` y los V/F falsos por sustitución libre están desactivados.",
        "",
        "## 20 ejemplos antes/después",
        "",
    ]
    for example in report["before_after_examples"]:
        lines.extend([
            f"### {example['id']}",
            "",
            f"- Antes: {example['before']}",
            f"- Después: {example['after']}",
            f"- Referencia: {example['reference_before']} -> {example['reference_after']}",
            "",
        ])
    (OUTPUT / "reporte_cuarentena.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result["manifest"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
