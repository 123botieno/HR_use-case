# ruff: noqa: E402
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.io import load


def track(run_path, uri):
    import mlflow

    run = load(run_path)
    comparison = Path(run_path).parent / "comparison.json"
    evaluation = load(comparison) if comparison.exists() else {}
    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment("ethiopia-job-matching")
    with mlflow.start_run(run_name=run["run_id"]) as parent:
        mlflow.log_params(
            {
                "dataset_hash": run["dataset_hash"],
                "version": run["version"],
                "status": run["status"],
                "git_revision": run.get("git_revision") or "unversioned",
                "code_hash": run.get("code_hash", "unknown"),
            }
        )
        for entry in run["results"]:
            with mlflow.start_run(
                run_name=entry["jd_id"] + "-" + entry["algorithm"], nested=True
            ):
                mlflow.log_params(
                    {
                        "jd_id": entry["jd_id"],
                        "algorithm": entry["algorithm"],
                        "pool_hash": entry["pool_hash"],
                    }
                )
                mlflow.log_metrics(
                    {
                        "runtime_seconds": entry["runtime_seconds"],
                        "shortlist_count": min(5, len(entry["ranking"])),
                    }
                )
                evaluated = next(
                    (
                        row
                        for row in evaluation.get("per_jd", [])
                        if (row["jd_id"], row["algorithm"])
                        == (entry["jd_id"], entry["algorithm"])
                    ),
                    {},
                )
                mlflow.log_metrics(
                    {
                        key: evaluated[key]
                        for key in ("precision_at_5", "recall_at_5", "ndcg_at_5")
                        if evaluated.get(key) is not None
                    }
                )
                if entry["algorithm"] == "llm":
                    requests = [
                        r["evidence"]
                        for r in entry["ranking"]
                        if not r["evidence"].get("cache_hit")
                    ]
                    mlflow.log_metrics(
                        {
                            "input_tokens": sum(
                                e.get("usage", {}).get("input_tokens", 0)
                                for e in requests
                            ),
                            "output_tokens": sum(
                                e.get("usage", {}).get("output_tokens", 0)
                                for e in requests
                            ),
                            "cache_hits": sum(
                                r["evidence"].get("cache_hit", False)
                                for r in entry["ranking"]
                            ),
                        }
                    )
                # Avoid candidate evidence/text in tracking by default.
                mlflow.log_dict(entry["config"], "configuration.json")
        if comparison.exists():
            mlflow.log_dict(evaluation, "comparison.json")
        identifier = parent.info.run_id
    return {"mlflow_run_id": identifier}


if __name__ == "__main__":
    from jobmatch.cli import main

    raise SystemExit(main(["track"] + sys.argv[1:]))
