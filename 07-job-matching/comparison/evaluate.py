"""Judgment-aware retrieval metrics and pairwise shortlist overlap."""

# ruff: noqa: E402
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import itertools
import math
from common.io import read_csv


def judgments_from_csv(path):
    rows = read_csv(path)
    result = {}
    for row in rows:
        if row["suitable"] == "" and row["relevance"] == "":
            continue
        key = (row["jd_id"], row["candidate_id"])
        if key in result:
            raise ValueError(f"Duplicate judgment: {key}")
        suitable, relevance = int(row["suitable"]), int(row["relevance"])
        if suitable not in {0, 1} or relevance not in {0, 1, 2, 3}:
            raise ValueError("Judgments require suitable 0/1 and relevance 0..3")
        if bool(suitable) != (relevance > 0):
            raise ValueError("Rubric requires relevance 0=unsuitable, 1..3=suitable")
        result[key] = {"suitable": suitable, "relevance": relevance}
    return result


def metrics(rows, judgments):
    jd = rows[0]["jd_id"] if rows else ""
    pool = [r["candidate_id"] for r in rows]
    top = rows[:5]
    judged = {cid: judgments[(jd, cid)] for cid in pool if (jd, cid) in judgments}
    complete_top = all(r["candidate_id"] in judged for r in top)
    complete_pool = len(judged) == len(pool)
    precision = (
        sum(judged[r["candidate_id"]]["suitable"] for r in top) / 5
        if complete_top
        else None
    )
    suitable_count = sum(v["suitable"] for v in judged.values())
    recall = (
        sum(judged[r["candidate_id"]]["suitable"] for r in top) / suitable_count
        if complete_pool and suitable_count
        else None
    )
    ndcg = None
    if complete_pool:
        gains = [judged[r["candidate_id"]]["relevance"] for r in top]
        ideal = sorted((v["relevance"] for v in judged.values()), reverse=True)[:5]

        def dcg(values):
            return sum(
                (2**value - 1) / math.log2(i + 2) for i, value in enumerate(values)
            )

        denominator = dcg(ideal)
        ndcg = dcg(gains) / denominator if denominator else None
    return {
        "precision_at_5": precision,
        "recall_at_5": recall,
        "ndcg_at_5": ndcg,
        "returned_count": len(top),
        "pool_size": len(pool),
        "judged_count": len(judged),
        "complete_judgments": complete_pool,
        "suitable_count": suitable_count if complete_pool else None,
    }


def compare(run, judgments=None):
    judgments = judgments or {}
    known = {
        (entry["jd_id"], r["candidate_id"])
        for entry in run["results"]
        for r in entry["ranking"]
    }
    if set(judgments) - known:
        raise ValueError("Judgments contain IDs outside this run")
    records, overlap = [], []
    for entry in run["results"]:
        records.append(
            {
                "jd_id": entry["jd_id"],
                "algorithm": entry["algorithm"],
                **metrics(entry["ranking"], judgments),
                "runtime_seconds": entry["runtime_seconds"],
            }
        )
    for jd in sorted({e["jd_id"] for e in run["results"]}):
        entries = [e for e in run["results"] if e["jd_id"] == jd]
        for a, b in itertools.combinations(entries, 2):
            if {r["candidate_id"] for r in a["ranking"]} != {
                r["candidate_id"] for r in b["ranking"]
            }:
                raise ValueError("Cannot compare different candidate pools")
            left = {r["candidate_id"] for r in a["ranking"][:5]}
            right = {r["candidate_id"] for r in b["ranking"][:5]}
            overlap.append(
                {
                    "jd_id": jd,
                    "left": a["algorithm"],
                    "right": b["algorithm"],
                    "shared_count": len(left & right),
                    "jaccard": len(left & right) / len(left | right),
                }
            )
    aggregate = {}
    for method in sorted({r["algorithm"] for r in records}):
        subset = [r for r in records if r["algorithm"] == method]
        aggregate[method] = {}
        for metric in ("precision_at_5", "recall_at_5", "ndcg_at_5"):
            values = [r[metric] for r in subset if r[metric] is not None]
            aggregate[method][metric] = {
                "mean": sum(values) / len(values) if values else None,
                "evaluated_jds": len(values),
            }
    return {
        "per_jd": records,
        "overlap": overlap,
        "macro_average": aggregate,
        "note": "Missing judgments yield unavailable metrics; overlap is not correctness.",
    }


if __name__ == "__main__":
    from jobmatch.cli import main

    raise SystemExit(main(["compare"] + sys.argv[1:]))
