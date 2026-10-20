"""Installed-library smoke tests; no live LLM calls or real group attributes."""

from common.stages import stage


import subprocess
import os

import sys

from pathlib import Path

import pytest

from common.io import load, save, write_csv

from test_pipeline import dataset

execute = stage("matching").execute

audit = stage("fairlearn").audit
make_synthetic_scenario = stage("fairlearn").make_synthetic_scenario
compare_synthetic = stage("fairlearn").compare_synthetic

monitor = stage("evidently").monitor

track = stage("mlflow").track

version_data = stage("dvc").version_data

prefect_run = stage("prefect").prefect_run

great_expectations_validate = stage("validation").great_expectations_validate


@pytest.fixture
def sample_run(tmp_path):
    path = tmp_path / "dataset.json"
    save(path, dataset())
    directory, run = execute(path, tmp_path / "runs", methods=["bm25", "tfidf"])
    return path, directory, run


def test_gx_real_validation():
    pytest.importorskip("great_expectations")
    assert great_expectations_validate(dataset())["success"]


def test_mlflow_tracking(sample_run, tmp_path, monkeypatch):
    pytest.importorskip("mlflow")
    monkeypatch.setenv("MLFLOW_DISABLE_TELEMETRY", "true")
    path, directory, run = sample_run
    uri = "sqlite:///" + (tmp_path / "tracking.db").as_posix()
    assert track(directory / "run.json", uri)["mlflow_run_id"]


def test_fairlearn_audit(sample_run, tmp_path):
    pytest.importorskip("fairlearn")
    path, directory, run = sample_run
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


def test_fairlearn_synthetic_bias_scenario(sample_run, tmp_path):
    pytest.importorskip("fairlearn")
    path, directory, run = sample_run
    artifacts = make_synthetic_scenario(directory / "run.json", tmp_path / "demo")
    comparison = compare_synthetic(
        artifacts["baseline_run"],
        artifacts["biased_run"],
        artifacts["groups"],
        tmp_path / "demo" / "comparison.json",
        stage("comparison").judgments_from_csv(artifacts["judgments"]),
    )
    assert comparison["synthetic"] is True
    assert len(comparison["per_jd"]) == 2
    for item in comparison["per_jd"]:
        groups = {row["group"]: row for row in item["groups"]}
        assert groups["Group B"]["selection_rate_change"] < 0
        assert groups["Group B"]["recall_change"] < 0


def test_evidently_report(sample_run, tmp_path):
    pytest.importorskip("evidently")
    path, directory, run = sample_run
    report = monitor(
        directory / "run.json", directory / "run.json", tmp_path / "monitor"
    )
    assert all(r["shortlist_jaccard"] == 1 for r in report)
    assert len(list((tmp_path / "monitor").glob("*.html"))) == 2


def test_dvc_local_versioning(tmp_path, monkeypatch):
    pytest.importorskip("dvc")
    monkeypatch.setenv("DVC_NO_ANALYTICS", "1")
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(["git", "init", str(repository)], check=True, capture_output=True)
    subprocess.run(
        [sys.executable, "-m", "dvc", "init"],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    target = repository / "data"
    target.mkdir()
    (target / "fixture.txt").write_text("synthetic")
    assert version_data(target, repository)["uploaded"] is False
    assert (repository / "data.dvc").exists()
    with pytest.raises(ValueError):
        version_data(tmp_path, repository)


@pytest.mark.skipif(
    os.getenv("RUN_PREFECT_TEST") != "1",
    reason="Starts a local Prefect test server; opt in",
)
def test_prefect_flow(sample_run, tmp_path, monkeypatch):
    pytest.importorskip("prefect")
    monkeypatch.setenv("PREFECT_HOME", str(tmp_path / "prefect"))
    monkeypatch.setenv("PREFECT_SERVER_ANALYTICS_ENABLED", "false")
    path, directory, run = sample_run
    from prefect.testing.utilities import prefect_test_harness

    with prefect_test_harness():
        result = prefect_run(str(path), str(tmp_path / "flows"), ["bm25", "tfidf"])
    assert load(Path(result) / "run.json")["status"] == "complete"
