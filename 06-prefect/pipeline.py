# ruff: noqa: E402
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.stages import stage
import os
from common.io import load, save

version_data = stage("dvc").version_data
track = stage("mlflow").track
audit = stage("fairlearn").audit
monitor = stage("evidently").monitor


def prefect_run(
    dataset,
    output,
    methods,
    rubric=None,
    jd_ids=None,
    gx=False,
    pool_scope="vacancy",
    tracking_uri=None,
    reference=None,
    groups=None,
    judgments_path=None,
    version_repository=None,
):
    os.environ.setdefault("PREFECT_HOME", str((Path(output).resolve() / ".prefect")))
    os.environ.setdefault("PREFECT_SERVER_ANALYTICS_ENABLED", "false")
    from prefect import flow, task

    execute = stage("matching").execute
    validate_dataset = stage("validation").validate_dataset

    @task(name="validate-inputs")
    def validate(path):
        data = load(path)
        result = validate_dataset(data)
        if gx:
            great_expectations_validate = stage(
                "validation"
            ).great_expectations_validate

            result["gx"] = great_expectations_validate(data)
        return result

    @task(name="compare-matching-methods", retries=0)
    def matching():
        directory, run = execute(
            dataset, output, methods, rubric, jd_ids, False, pool_scope
        )
        return str(directory), run["status"]

    @task(name="version-data")
    def version():
        return version_data(Path(dataset).parent, version_repository)

    @task(name="evaluate-rankings")
    def evaluate(path):
        compare = stage("comparison").compare
        judgments_from_csv = stage("comparison").judgments_from_csv

        labels = judgments_from_csv(judgments_path) if judgments_path else None
        report = compare(load(Path(path) / "run.json"), labels)
        save(Path(path) / "comparison.json", report)
        return report

    @task(name="track-experiment")
    def tracking(path):
        return track(Path(path) / "run.json", tracking_uri)

    @task(name="group-evaluation")
    def group_evaluation(path):
        judgments_from_csv = stage("comparison").judgments_from_csv

        labels = judgments_from_csv(judgments_path) if judgments_path else None
        return audit(Path(path) / "run.json", groups, Path(path) / "audit.json", labels)

    @task(name="monitor-rankings")
    def monitoring(path):
        return monitor(reference, Path(path) / "run.json", Path(path) / "monitoring")

    @flow(name="ethiopia-job-matching", log_prints=True)
    def pipeline():
        validate(dataset)
        if version_repository:
            version()
        directory, status = matching()
        evaluate(directory)
        if groups:
            group_evaluation(directory)
        if reference:
            monitoring(directory)
        if tracking_uri:
            tracking(directory)
        if status != "complete":
            raise RuntimeError(
                f"Incomplete matching run; inspect {Path(directory) / 'run.json'}"
            )
        return directory

    return pipeline()


if __name__ == "__main__":
    from jobmatch.cli import main

    raise SystemExit(main(["flow"] + sys.argv[1:]))
