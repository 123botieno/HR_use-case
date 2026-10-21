"""HR fairness checks; shared MLOps tool tests live in the workshop hub."""

from common.stages import stage
from common.io import save, write_csv
from test_pipeline import dataset

execute = stage("matching").execute
audit = stage("fairlearn").audit
make_synthetic_scenario = stage("fairlearn").make_synthetic_scenario
compare_synthetic = stage("fairlearn").compare_synthetic
judgments_from_csv = stage("comparison").judgments_from_csv


def test_fairlearn_audit(tmp_path):
    path = tmp_path / "dataset.json"
    save(path, dataset())
    directory, _ = execute(path, tmp_path / "runs", methods=["bm25", "tfidf"])
    groups = tmp_path / "groups.csv"
    write_csv(
        groups,
        [
            {
                "jd_id": "J",
                "candidate_id": f"C{i}",
                "group": "fixture-A" if i < 3 else "fixture-B",
            }
            for i in range(6)
        ],
    )
    result = audit(directory / "run.json", groups, tmp_path / "audit.json")
    assert len(result["results"]) == 2
    assert result["results"][0]["audit_coverage"] == 1
    assert sum(g["count"] for g in result["results"][0]["group_metrics"]) == 6


def test_fairlearn_synthetic_bias_scenario(tmp_path):
    path = tmp_path / "dataset.json"
    save(path, dataset())
    directory, _ = execute(path, tmp_path / "runs", methods=["bm25", "tfidf"])
    artifacts = make_synthetic_scenario(directory / "run.json", tmp_path / "demo")
    comparison = compare_synthetic(
        artifacts["baseline_run"],
        artifacts["biased_run"],
        artifacts["groups"],
        tmp_path / "demo" / "comparison.json",
        judgments_from_csv(artifacts["judgments"]),
    )
    assert comparison["synthetic"] is True
    assert len(comparison["per_jd"]) == 2
