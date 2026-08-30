"""Captura verificable del banco competitivo que está en producción."""

from __future__ import annotations

import json
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Any
from urllib.request import Request, urlopen


def fetch_url_bytes(url: str) -> bytes:
    request = Request(url, headers={"Cache-Control": "no-cache", "User-Agent": "conexion-biblica-v11-snapshot/1.0"})
    with urlopen(request, timeout=30) as response:
        return response.read()


def import_production_snapshot(
    base_url: str,
    destination: Path,
    *,
    fetch_bytes: Callable[[str], bytes] | None = None,
    fetched_at: str | None = None,
) -> dict[str, Any]:
    fetch_bytes = fetch_bytes or fetch_url_bytes
    fetched_at = fetched_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    root = base_url.rstrip("/")
    manifest_url = f"{root}/banks/final-2026/manifest.json"
    manifest_bytes = fetch_bytes(manifest_url)
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    resources = [
        {
            "kind": "manifest",
            "chapter": None,
            "path": "banks/final-2026/manifest.json",
            "url": manifest_url,
            "bytes": len(manifest_bytes),
            "sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        }
    ]
    for shard in manifest["shards"]:
        resource_path = shard["questions_file"].lstrip("/")
        shard_url = f"{root}/{resource_path}"
        try:
            shard_bytes = fetch_bytes(shard_url)
        except Exception as exc:
            raise ValueError(
                f"No se pudo capturar el shard {shard['chapter']}"
            ) from exc
        resources.append(
            {
                "kind": "question_shard",
                "chapter": shard["chapter"],
                "path": resource_path,
                "url": shard_url,
                "bytes": len(shard_bytes),
                "sha256": hashlib.sha256(shard_bytes).hexdigest(),
            }
        )

    snapshot = {
        "snapshot_version": "1.0",
        "base_url": root,
        "fetched_at": fetched_at,
        "counts": {
            "central_question_count": manifest["central_question_count"],
            "presentation_variant_count": manifest["presentation_variant_count"],
            "training_presentation_count": manifest["training_presentation_count"],
            "shards": len(manifest["shards"]),
        },
        "manifest": manifest,
        "resources": resources,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(f"{destination.suffix}.tmp")
    try:
        temporary.write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return snapshot
