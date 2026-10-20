from common.stages import stage

import math

import pytest

bm25 = stage("bm25").bm25

tfidf = stage("tfidf").tfidf

rank = stage("shortlist").rank


@pytest.mark.parametrize("method", [bm25, tfidf])
def test_relevant_document_outranks_unrelated_document(method):
    scores, evidence, config = method(
        "python forecasting", ["python forecasting data", "accounting tax ledger"]
    )
    assert scores[0] > scores[1]
    assert evidence[0]


def test_bm25_length_normalization_and_repeated_query_terms():
    scores, _, _ = bm25("python python", ["python", "python " + "unrelated " * 100])
    unique_scores, _, _ = bm25("python", ["python", "python " + "unrelated " * 100])
    assert scores == unique_scores
    assert scores[0] > scores[1]


def test_tfidf_zero_query_and_empty_corpus():
    scores, _, config = tfidf(
        "unknownword", ["python programmer", "finance accounting"]
    )
    assert scores == [0, 0]
    assert config["query_zero_vector"]
    with pytest.raises(ValueError):
        tfidf("python", ["", ""])


def test_top_five_unique_stable_ties_and_shortfall():
    candidates = [{"id": f"C{i}"} for i in reversed(range(7))]
    rows = rank("J", "bm25", candidates, [0] * 7, [[]] * 7)
    assert [r["candidate_id"] for r in rows[:5]] == ["C0", "C1", "C2", "C3", "C4"]
    assert sum(r["shortlisted"] for r in rows) == 5
    assert all(r["cutoff_tie"] and r["uninformative"] for r in rows)
    assert len(rank("J", "bm25", candidates[:3], [1] * 3, [[]] * 3)) == 3


def test_nonfinite_scores_rejected():
    with pytest.raises(ValueError):
        rank("J", "llm", [{"id": "C"}], [math.nan], [{}])
