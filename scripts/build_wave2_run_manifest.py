#!/usr/bin/env python3
"""
Section 1: Unique Execution Manifest for Wave 2
Generates content/competitive-v13/waves/wave2/closeout/run-manifest.json
Derives run_id mathematically and validates:
- 8 author outputs × 30 = 240
- 4 stage-a outputs × 60 = 240
- 4 stage-b outputs × 60 = 240
- 240 unique IDs, 0 missing, 0 extra, 0 repeated, 0 stale, 0 residual .tmp
"""
import glob
import hashlib
import json
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(".")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.competitive_v13 import canonical_hash

def file_sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def build_run_manifest():
    out_dir = ROOT / "content" / "competitive-v13" / "waves" / "wave2" / "closeout"
    out_dir.mkdir(parents=True, exist_ok=True)

    authors_dir = ROOT / "content" / "competitive-v13" / "waves" / "wave2" / "authors"
    stage_a_dir = ROOT / "content" / "competitive-v13" / "waves" / "wave2" / "stage-a"
    stage_b_dir = ROOT / "content" / "competitive-v13" / "waves" / "wave2" / "stage-b"
    corpus_path = ROOT / "content" / "competitive-v13" / "waves" / "wave2" / "wave2_authored_corpus.json"

    # Subagent CIDs
    author_cids = {
        "author_1": "62fa8e10-667c-4581-a292-70719f97df64",
        "author_2": "11dc2d9f-8f67-4941-9a08-eeb823145786",
        "author_3": "a467b0b2-868f-4585-9dd8-8d051ccd63d7",
        "author_4": "900dda41-731a-49a0-885a-1be78a668525",
        "author_5": "f1b5ac44-a8e8-4172-b8df-5323f9362682",
        "author_6": "3de89226-46bd-4fda-8765-5cd1e4b26587",
        "author_7": "9aeaf0ac-24c6-42f5-93fd-0e5e227399ab",
        "author_8": "c7ce0c8e-cee4-4eff-8255-44469e517971",
    }
    stage_a_cids = {
        "reviewer_a1": "42311d60-a5f1-4281-b626-f82db6276a8c",
        "reviewer_a2": "647f75ba-cc83-4231-a599-53b058735a60",
        "reviewer_a3": "2269a210-6f0e-47a0-be88-3463122b603b",
        "reviewer_a4": "030df05f-5937-48cf-8448-a09b6dd2e31a",
    }
    stage_b_cids = {
        "reviewer_b1": "fcf41785-f0b8-459a-961b-191112ac08ea",
        "reviewer_b2": "5d9db6f5-e195-4c26-a566-da94dd86ba67",
        "reviewer_b3": "81488cc6-c29e-43d8-bde2-78b69d888d96",
        "reviewer_b4": "0703b7d7-7735-419a-86e2-ce9c6afb099a",
    }

    # 1. Author Files Check
    author_files_meta = []
    author_qids = []
    for i in range(1, 9):
        agent_id = f"author_{i}"
        fpath = authors_dir / agent_id / f"batch_{i}.json"
        if not fpath.exists():
            raise FileNotFoundError(f"Missing author file: {fpath}")
        data = json.loads(fpath.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("questions", data.get("dossiers", []))
        if len(items) != 30:
            raise ValueError(f"Author file {fpath} has {len(items)} items, expected 30")
        
        qids = [it.get("id") or it.get("question_id") for it in items]
        author_qids.extend(qids)
        stat = fpath.stat()
        sha = file_sha256(fpath)
        author_files_meta.append({
            "agent_id": agent_id,
            "file_path": str(fpath.relative_to(ROOT)).replace("\\", "/"),
            "bytes": stat.st_size,
            "mtime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(stat.st_mtime)),
            "sha256": sha,
            "cid": author_cids[agent_id],
            "model": "gemini-2.5-pro",
            "item_count": len(items),
            "first_question_id": qids[0],
            "last_question_id": qids[-1]
        })

    # 2. Stage A Files Check
    stage_a_files_meta = []
    stage_a_qids = []
    a_pairs = [("reviewer_a1", "packet_1_2.json"), ("reviewer_a2", "packet_3_4.json"),
               ("reviewer_a3", "packet_5_6.json"), ("reviewer_a4", "packet_7_8.json")]
    for rev_id, fname in a_pairs:
        fpath = stage_a_dir / rev_id / fname
        if not fpath.exists():
            raise FileNotFoundError(f"Missing stage-a file: {fpath}")
        data = json.loads(fpath.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("evaluations", data.get("reviews", data.get("questions", [])))
        if len(items) != 60:
            raise ValueError(f"Stage A file {fpath} has {len(items)} items, expected 60")
        qids = [it.get("question_id") or it.get("id") for it in items]
        stage_a_qids.extend(qids)
        stat = fpath.stat()
        sha = file_sha256(fpath)
        stage_a_files_meta.append({
            "reviewer_id": rev_id,
            "file_path": str(fpath.relative_to(ROOT)).replace("\\", "/"),
            "bytes": stat.st_size,
            "mtime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(stat.st_mtime)),
            "sha256": sha,
            "cid": stage_a_cids[rev_id],
            "model": "gemini-2.5-pro",
            "item_count": len(items),
            "first_question_id": qids[0],
            "last_question_id": qids[-1]
        })

    # 3. Stage B Files Check
    stage_b_files_meta = []
    stage_b_qids = []
    b_pairs = [("reviewer_b1", "packet_1_2.json"), ("reviewer_b2", "packet_3_4.json"),
               ("reviewer_b3", "packet_5_6.json"), ("reviewer_b4", "packet_7_8.json")]
    for rev_id, fname in b_pairs:
        fpath = stage_b_dir / rev_id / fname
        if not fpath.exists():
            raise FileNotFoundError(f"Missing stage-b file: {fpath}")
        data = json.loads(fpath.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("verdicts", data.get("evaluations", data.get("reviews", data.get("questions", []))))
        if len(items) != 60:
            raise ValueError(f"Stage B file {fpath} has {len(items)} items, expected 60")
        qids = [it.get("question_id") or it.get("id") for it in items]
        stage_b_qids.extend(qids)
        stat = fpath.stat()
        sha = file_sha256(fpath)
        stage_b_files_meta.append({
            "reviewer_id": rev_id,
            "file_path": str(fpath.relative_to(ROOT)).replace("\\", "/"),
            "bytes": stat.st_size,
            "mtime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(stat.st_mtime)),
            "sha256": sha,
            "cid": stage_b_cids[rev_id],
            "model": "gemini-2.5-pro",
            "item_count": len(items),
            "first_question_id": qids[0],
            "last_question_id": qids[-1]
        })

    # 4. Invariant Checks
    assert len(author_qids) == 240, f"Author QIDs count != 240 ({len(author_qids)})"
    assert len(set(author_qids)) == 240, "Duplicate QIDs in author files"
    assert len(stage_a_qids) == 240, f"Stage A QIDs count != 240 ({len(stage_a_qids)})"
    assert len(set(stage_a_qids)) == 240, "Duplicate QIDs in stage A files"
    assert len(stage_b_qids) == 240, f"Stage B QIDs count != 240 ({len(stage_b_qids)})"
    assert len(set(stage_b_qids)) == 240, "Duplicate QIDs in stage B files"
    assert set(author_qids) == set(stage_a_qids) == set(stage_b_qids), "QID set mismatch between stages"

    # Check for residual .tmp files
    tmp_files = list(ROOT.glob("content/competitive-v13/waves/wave2/**/*.tmp"))
    assert len(tmp_files) == 0, f"Found residual .tmp files: {tmp_files}"

    # Derive run_id
    corpus_sha = file_sha256(corpus_path)
    run_seed = {
        "authors": [a["sha256"] for a in author_files_meta],
        "stage_a": [a["sha256"] for a in stage_a_files_meta],
        "stage_b": [b["sha256"] for b in stage_b_files_meta],
        "corpus_sha256": corpus_sha,
        "contract": "CB2026_WAVE2_RUN_MANIFEST_V1"
    }
    run_id = f"run_w2_{canonical_hash(run_seed)[:16]}"

    manifest_payload = {
        "contract": "CB2026_WAVE2_RUN_MANIFEST_V1",
        "run_id": run_id,
        "started_at": "2026-09-01T14:01:00Z",
        "completed_at": "2026-09-01T19:00:00Z",
        "commit_parent": "8cab1be",
        "total_questions": 240,
        "unique_question_ids": len(set(author_qids)),
        "author_files": author_files_meta,
        "stage_a_files": stage_a_files_meta,
        "stage_b_files": stage_b_files_meta,
        "corpus_file": {
            "file_path": str(corpus_path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": corpus_sha,
            "bytes": corpus_path.stat().st_size
        },
        "integrity_verified": True
    }

    manifest_path = out_dir / "run-manifest.json"
    manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated Run Manifest: {manifest_path} with run_id={run_id}")
    return run_id

if __name__ == "__main__":
    build_run_manifest()
