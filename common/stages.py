"""Import HR-specific implementation modules."""

from importlib import import_module

MODULES = {
    "data": "00-data.prepare",
    "fairlearn": "04-fairlearn.evaluate",
    "matching": "07-job-matching.run",
    "llm": "07-job-matching.llm.score",
    "bm25": "07-job-matching.bm25.score",
    "tfidf": "07-job-matching.tfidf.score",
    "comparison": "07-job-matching.comparison.evaluate",
    "shortlist": "07-job-matching.shortlist",
}


def stage(name):
    return import_module(MODULES[name])
