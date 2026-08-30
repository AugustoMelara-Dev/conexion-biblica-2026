#!/usr/bin/env python3
"""Fija paquetes de fuente V11; no redacta preguntas."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.final_editorial import EDITORIALLY_EXCLUDED_SOURCE_UNITS
from scripts.lib.production_snapshot_v11 import fetch_url_bytes
from scripts.lib.source_packets_v11 import build_source_packets

EXPECTED_UNITS = [
    *(f"DAN{chapter}" for chapter in range(1, 13)),
    *(f"PR{chapter}" for chapter in range(39, 45)),
]


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inventory-url",
        default="https://conexion-biblica-2026.vercel.app/banks/final-2026/source_inventory.json",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=ROOT / "content" / "competitive-v11" / "baseline-production.json",
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        default=ROOT / "MaterialConexionBiblica (1).pdf",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "content" / "competitive-v11" / "source-packets",
    )
    args = parser.parse_args()

    try:
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        expected_source_hash = baseline["manifest"]["source_sha256"]
        actual_source_hash = hashlib.sha256(args.pdf.read_bytes()).hexdigest()
        if actual_source_hash != expected_source_hash:
            raise ValueError("El PDF local no coincide con la fuente de producción")

        inventory = json.loads(fetch_url_bytes(args.inventory_url).decode("utf-8"))
        packets, excluded = build_source_packets(
            inventory,
            EDITORIALLY_EXCLUDED_SOURCE_UNITS,
        )
        useful_count = sum(len(rows) for rows in packets.values())
        if list(packets) != EXPECTED_UNITS:
            raise ValueError(f"Unidades inesperadas: {list(packets)}")
        if inventory["source_units"] != 1031 or useful_count != 1024:
            raise ValueError(
                f"Cobertura inválida: source={inventory['source_units']}, useful={useful_count}"
            )
        if len(excluded) != 7:
            raise ValueError(f"Exclusiones inesperadas: {len(excluded)}")

        temporary = args.output.parent / f".{args.output.name}.tmp"
        if temporary.exists():
            shutil.rmtree(temporary)
        temporary.mkdir(parents=True)
        for unit_code in EXPECTED_UNITS:
            rows = packets[unit_code]
            write_json(
                temporary / f"{unit_code}.json",
                {
                    "schema_version": "11.0-source-packet",
                    "source_sha256": actual_source_hash,
                    "unit": unit_code,
                    "unit_count": len(rows),
                    "units": rows,
                },
            )
        write_json(
            temporary / "excluded-units.json",
            {
                "schema_version": "11.0-source-packet",
                "source_sha256": actual_source_hash,
                "units": excluded,
            },
        )
        if args.output.exists():
            shutil.rmtree(args.output)
        temporary.rename(args.output)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "source_units": inventory["source_units"],
                "useful_units": useful_count,
                "excluded_units": len(excluded),
                "packets": len(packets),
                "output": str(args.output),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
