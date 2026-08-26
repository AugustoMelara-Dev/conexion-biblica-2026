#!/usr/bin/env python3
"""Construye los artefactos canónicos V7 desde el PDF y su caché OCR local."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.source_inventory import build_source_inventory


PDF_PATH = ROOT / "MaterialConexionBiblica (1).pdf"
OCR_PATH = ROOT / "scripts/source-cache/final-v7/ocr-pages.json"
OUTPUT_DIR = ROOT / "public/banks/final-2026"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    ocr = json.loads(OCR_PATH.read_text(encoding="utf-8"))
    source_hash = hashlib.sha256(PDF_PATH.read_bytes()).hexdigest()
    if ocr["source_sha256"] != source_hash:
        raise SystemExit("La caché OCR no corresponde al PDF local")
    inventory, issues = build_source_inventory(PDF_PATH, ocr["pages"])
    if issues["unresolved_count"]:
        raise SystemExit(
            f"La extracción conserva {issues['unresolved_count']} incidencias sin resolver"
        )
    write_json(OUTPUT_DIR / "source_inventory.json", inventory)
    write_json(OUTPUT_DIR / "source_extraction_issues.json", issues)
    print(
        json.dumps(
            {
                "daniel_verses": inventory["daniel_verses"],
                "pr_propositions": inventory["pr_propositions"],
                "source_units": inventory["source_units"],
                "unresolved": issues["unresolved_count"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
