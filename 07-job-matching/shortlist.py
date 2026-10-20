# ruff: noqa: E402
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import math


def rank(jd_id, method, candidates, scores, evidence):
    if len(candidates) != len(scores) or len(candidates) != len(evidence):
        raise ValueError("Mismatched score/evidence lengths")
    if not all(math.isfinite(float(score)) for score in scores):
        raise ValueError("Non-finite scores")
    rows = [
        {
            "jd_id": jd_id,
            "candidate_id": c["id"],
            "algorithm": method,
            "score": float(score),
            "evidence": e,
        }
        for c, score, e in zip(candidates, scores, evidence)
    ]
    rows.sort(key=lambda row: (-row["score"], row["candidate_id"]))
    cutoff_tie = len(rows) > 5 and rows[4]["score"] == rows[5]["score"]
    for position, row in enumerate(rows, 1):
        row.update(
            rank=position,
            shortlisted=position <= 5,
            cutoff_tie=cutoff_tie and row["score"] == rows[4]["score"],
            uninformative=all(r["score"] == 0 for r in rows),
        )
    return rows
