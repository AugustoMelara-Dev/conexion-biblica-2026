#!/usr/bin/env python3
"""Captura el banco activo de producción sin modificarlo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.production_snapshot_v11 import import_production_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default="https://conexion-biblica-2026.vercel.app",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=ROOT / "content" / "competitive-v11" / "baseline-production.json",
    )
    args = parser.parse_args()

    try:
        snapshot = import_production_snapshot(
            args.base_url,
            args.destination,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                **snapshot["counts"],
                "destination": str(args.destination),
                "resources": len(snapshot["resources"]),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
