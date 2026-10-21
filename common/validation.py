"""Lightweight, HR-specific checks for prepared datasets and rankings."""

import math

from common.io import digest


def validate_dataset(data):
    expected = data.get("dataset_hash")
    if expected != digest({k: v for k, v in data.items() if k != "dataset_hash"}):
        raise ValueError("Dataset hash mismatch")
    jobs, candidates = data["jobs"], data["candidates"]
    if not jobs or not candidates:
        raise ValueError("No assessable jobs or candidates")
    for records in (jobs, candidates):
        identifiers = [r["id"] for r in records]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Duplicate IDs")
        for record in records:
            if not record.get("text", "").strip() or not record.get("sections"):
                raise ValueError("Missing text or source sections")
            if digest(record["text"]) != record["text_hash"]:
                raise ValueError("Text hash mismatch")
    job_ids = {r["id"] for r in jobs}
    if any(c["jd_id"] not in job_ids for c in candidates):
        raise ValueError("Orphan candidate")
    if any(not any(c["jd_id"] == j for c in candidates) for j in job_ids):
        raise ValueError("Empty candidate pool")
    return {"success": True, "jobs": len(jobs), "candidates": len(candidates)}


def validate_rankings(rows, pool):
    if len(rows) != len(pool) or {r["candidate_id"] for r in rows} != {
        c["id"] for c in pool
    }:
        raise ValueError("Ranking candidate pool mismatch")
    if len({r["candidate_id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate ranking candidates")
    if [r["rank"] for r in rows] != list(range(1, len(rows) + 1)):
        raise ValueError("Invalid ranks")
    if not all(math.isfinite(r["score"]) for r in rows):
        raise ValueError("Non-finite score")
    if rows != sorted(rows, key=lambda r: (-r["score"], r["candidate_id"])):
        raise ValueError("Invalid ranking order")
    if any(r["shortlisted"] != (r["rank"] <= 5) for r in rows):
        raise ValueError("Invalid shortlist membership")
    return {
        "success": True,
        "shortlist_count": min(5, len(rows)),
        "shortfall": max(0, 5 - len(rows)),
    }
