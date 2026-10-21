"""Manual comparison flow with explicit method failures and immutable run directories."""

# ruff: noqa: E402
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.stages import stage
from common.validation import validate_dataset, validate_rankings

import os
import platform
import importlib.metadata
import subprocess
import time
from datetime import datetime, timezone
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from jobmatch import __version__
from common.io import digest, load, save, write_csv

bm25 = stage("bm25").bm25
tfidf = stage("tfidf").tfidf
rank = stage("shortlist").rank
LLMScorer = stage("llm").LLMScorer
validate_rubric = stage("llm").validate_rubric
DEFAULT_MODEL = stage("llm").DEFAULT_MODEL
DEFAULT_ENDPOINT = stage("llm").DEFAULT_ENDPOINT
PROMPT_VERSION = stage("llm").PROMPT_VERSION
compare = stage("comparison").compare


def execute(
    dataset_path,
    output_root,
    methods=("bm25", "tfidf", "llm"),
    rubric_path=None,
    jd_ids=None,
    pool_scope="vacancy",
    allow_draft_rubric=False,
    llm_workers=1,
):
    if (
        not methods
        or len(set(methods)) != len(methods)
        or set(methods) - {"bm25", "tfidf", "llm"}
    ):
        raise ValueError("Choose unique methods from bm25, tfidf, llm")
    if pool_scope not in {"vacancy", "all"}:
        raise ValueError("pool_scope must be vacancy or all")
    if not 1 <= llm_workers <= 8:
        raise ValueError("llm_workers must be between 1 and 8")
    data = load(dataset_path)
    validate_dataset(data)
    selected = set(jd_ids or [j["id"] for j in data["jobs"]])
    if selected - {j["id"] for j in data["jobs"]}:
        raise ValueError("Unknown or unavailable JD IDs")
    jobs = [j for j in data["jobs"] if j["id"] in selected]
    run_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    )
    directory = Path(output_root) / run_id
    directory.mkdir(parents=True, exist_ok=False)
    try:
        revision = (
            subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True
            ).stdout.strip()
            or None
        )
    except OSError:
        revision = None
    result = {
        "run_id": run_id,
        "version": __version__,
        "python": platform.python_version(),
        "git_revision": revision,
        "dataset_hash": data["dataset_hash"],
        "requested_methods": list(methods),
        "pool_scope": pool_scope,
        "results": [],
        "failures": [],
    }
    result["code_hash"] = digest(
        {
            p.relative_to(Path(__file__).resolve().parents[1]).as_posix(): p.read_text(
                encoding="utf-8"
            )
            for p in sorted(
                list(Path(__file__).resolve().parents[1].glob("0*/**/*.py"))
                + list(Path(__file__).resolve().parents[1].glob("common/*.py"))
                + list(Path(__file__).resolve().parents[1].glob("jobmatch/*.py"))
            )
        }
    )
    result["dependencies"] = {
        name: importlib.metadata.version(name)
        for name in ("numpy", "pandas", "scikit-learn")
    }
    rubric = load(rubric_path) if rubric_path else {}
    result["rubric_status"] = (
        "draft_experiment"
        if "llm" in methods
        and any(rubric.get(j["id"], {}).get("confirmed") is not True for j in jobs)
        else "confirmed_or_not_used"
    )
    scorer = None
    llm_error = None
    if "llm" in methods:
        try:
            validate_rubric(rubric, jobs, allow_draft=allow_draft_rubric)
            scorer = LLMScorer(
                os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL),
                os.getenv("LLM_BASE_URL", DEFAULT_ENDPOINT),
                Path(output_root) / "llm-cache",
            )
        except (ValueError, KeyError, TypeError) as exc:
            llm_error = str(exc)
    for job in jobs:
        candidates = sorted(
            [
                c
                for c in data["candidates"]
                if pool_scope == "all" or c["jd_id"] == job["id"]
            ],
            key=lambda c: c["id"],
        )
        pool_hash = digest([(c["id"], c["text_hash"]) for c in candidates])
        for method in methods:
            started = time.perf_counter()
            try:
                if method == "llm":
                    if llm_error:
                        raise ValueError(llm_error)

                    def score_candidate(candidate):
                        return scorer.score(
                            job, candidate, rubric[job["id"]]["requirements"]
                        )

                    with ThreadPoolExecutor(max_workers=llm_workers) as executor:
                        values = list(executor.map(score_candidate, candidates))
                    scores, evidence = zip(*values)
                    config = {
                        "model": scorer.model,
                        "endpoint": scorer.endpoint,
                        "rubric_hash": digest(rubric[job["id"]]),
                        "prompt_version": PROMPT_VERSION,
                        "provider": "openrouter" if scorer.endpoint.startswith("https://openrouter.ai/") else "openai-compatible",
                        "rubric_confirmed": rubric[job["id"]].get("confirmed") is True,
                    }
                else:
                    scores, evidence, config = (bm25 if method == "bm25" else tfidf)(
                        job["text"], [c["text"] for c in candidates]
                    )
                ranking = rank(job["id"], method, candidates, scores, evidence)
                lengths = {c["id"]: len(c["text"]) for c in candidates}
                for row in ranking:
                    row["cv_characters"] = lengths[row["candidate_id"]]
                validation = validate_rankings(ranking, candidates)
                result["results"].append(
                    {
                        "jd_id": job["id"],
                        "job_family": job.get("job_family", ""),
                        "algorithm": method,
                        "pool_hash": pool_hash,
                        "config": config,
                        "runtime_seconds": time.perf_counter() - started,
                        "validation": validation,
                        "ranking": ranking,
                    }
                )
            except Exception as exc:
                # Persist an explicit failure; do not issue a partial candidate ranking.
                result["failures"].append(
                    {
                        "jd_id": job["id"],
                        "algorithm": method,
                        "error_type": type(exc).__name__,
                        "reason": str(exc),
                    }
                )
            save(directory / "run.json", result)
    result["status"] = "complete" if not result["failures"] else "incomplete"
    save(directory / "run.json", result)
    rows = []
    for entry in result["results"]:
        for row in entry["ranking"]:
            rows.append({k: v for k, v in row.items() if k != "evidence"})
    write_csv(directory / "rankings.csv", rows)
    write_csv(directory / "shortlists.csv", [r for r in rows if r["shortlisted"]])
    side_by_side = []
    for job in jobs:
        entries = {
            e["algorithm"]: e for e in result["results"] if e["jd_id"] == job["id"]
        }
        for position in range(5):
            record = {"jd_id": job["id"], "rank": position + 1}
            for method in methods:
                ranking = entries.get(method, {}).get("ranking", [])
                row = ranking[position] if position < len(ranking) else {}
                record[method + "_candidate"] = row.get("candidate_id", "")
                record[method + "_score"] = row.get("score", "")
            side_by_side.append(record)
    write_csv(directory / "comparison_shortlists.csv", side_by_side)
    # Full pools, sorted by ID and without algorithm information: ready for blind review.
    write_csv(
        directory / "judgments_template.csv",
        [
            {"jd_id": j["id"], "candidate_id": c["id"], "suitable": "", "relevance": ""}
            for j in jobs
            for c in sorted(data["candidates"], key=lambda c: c["id"])
            if pool_scope == "all" or c["jd_id"] == j["id"]
        ],
    )
    save(directory / "comparison.json", compare(result))
    report = [
        "# Job matching run",
        "",
        f"Run: {run_id}",
        f"Status: {result['status']}",
        "",
        "Scores are method-specific relevance/evidence scores, not hiring probabilities.",
        "",
    ]
    for entry in result["results"]:
        report.extend(
            [
                f"## {entry['jd_id']} — {entry['algorithm']}",
                "",
                "| Rank | Candidate | Score | Review |",
                "|---|---|---|---|",
            ]
        )
        for row in entry["ranking"][:5]:
            flags = []
            if row["cutoff_tie"]:
                flags.append("cutoff tie")
            if row["uninformative"]:
                flags.append("no term evidence")
            if isinstance(row["evidence"], dict) and row["evidence"].get(
                "unknown_weight_share", 0
            ):
                flags.append("unknown requirements")
            report.append(
                f"| {row['rank']} | {row['candidate_id']} | {row['score']:.4f} | {', '.join(flags)} |"
            )
        if entry["validation"]["shortfall"]:
            report.append(f"Shortfall: {entry['validation']['shortfall']}")
        report.append("")
    if result["failures"]:
        report.extend(["## Incomplete methods", ""])
        report.extend(
            f"- {e['jd_id']} / {e['algorithm']}: {e['reason']}"
            for e in result["failures"]
        )
    (directory / "report.md").write_text("\n".join(report), encoding="utf-8")
    if result["rubric_status"] == "draft_experiment":
        report_path = directory / "report.md"
        report_path.write_text(
            "> EXPERIMENTAL: uses unconfirmed draft JD rubrics; recruiter review is pending.\n\n"
            + report_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    return directory, result


if __name__ == "__main__":
    from jobmatch.cli import main

    raise SystemExit(main(["run"] + sys.argv[1:]))
