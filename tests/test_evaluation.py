from common.stages import stage

import pytest

metrics = stage("comparison").metrics

compare = stage("comparison").compare

judgments_from_csv = stage("comparison").judgments_from_csv


def ranking(order):
    return [
        {"jd_id": "J", "candidate_id": c, "rank": i} for i, c in enumerate(order, 1)
    ]


def test_known_metrics_and_no_missing_labels_as_negative():
    rows = ranking(["a", "b", "c", "d", "e", "f"])
    labels = {
        ("J", c): {
            "suitable": int(c in "af"),
            "relevance": 3 if c == "a" else (1 if c == "f" else 0),
        }
        for c in "abcdef"
    }
    result = metrics(rows, labels)
    assert result["precision_at_5"] == 0.2
    assert result["recall_at_5"] == 0.5
    assert 0 < result["ndcg_at_5"] < 1
    partial = metrics(rows, {("J", "a"): labels[("J", "a")]})
    assert partial["precision_at_5"] is None
    assert partial["recall_at_5"] is None
    assert partial["ndcg_at_5"] is None


def test_perfect_ndcg_and_no_positives():
    rows = ranking(["a", "b", "c"])
    labels = {
        ("J", c): {"suitable": 1, "relevance": 3 - i} for i, c in enumerate("abc")
    }
    assert metrics(rows, labels)["ndcg_at_5"] == pytest.approx(1)
    assert metrics(rows, labels)["precision_at_5"] == 0.6
    negative = {key: {"suitable": 0, "relevance": 0} for key in labels}
    assert metrics(rows, negative)["recall_at_5"] is None
    assert metrics(rows, negative)["ndcg_at_5"] is None


def test_judgment_validation(tmp_path):
    path = tmp_path / "labels.csv"
    path.write_text("jd_id,candidate_id,suitable,relevance\nJ,a,1,0\n")
    with pytest.raises(ValueError):
        judgments_from_csv(path)


def test_comparison_requires_same_pool():
    run = {
        "results": [
            {
                "jd_id": "J",
                "algorithm": "a",
                "ranking": ranking("abc"),
                "runtime_seconds": 1,
            },
            {
                "jd_id": "J",
                "algorithm": "b",
                "ranking": ranking("abd"),
                "runtime_seconds": 1,
            },
        ]
    }
    with pytest.raises(ValueError):
        compare(run)
