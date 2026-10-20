"""Import the numbered workshop folders without duplicating their implementations."""

from importlib import import_module

MODULES = {
    "data": "00-data.prepare",
    "dvc": "01-dvc.version",
    "validation": "02-great-expectations.validate",
    "mlflow": "03-mlflow.track",
    "fairlearn": "04-fairlearn.evaluate",
    "evidently": "05-evidently.monitor",
    "prefect": "06-prefect.pipeline",
    "matching": "07-job-matching.run",
    "llm": "07-job-matching.llm.score",
    "bm25": "07-job-matching.bm25.score",
    "tfidf": "07-job-matching.tfidf.score",
    "comparison": "07-job-matching.comparison.evaluate",
    "shortlist": "07-job-matching.shortlist",
}


def stage(name):
    return import_module(MODULES[name])
