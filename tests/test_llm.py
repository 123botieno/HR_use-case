from common.stages import stage

import json

import pytest

LLMScorer = stage("llm").LLMScorer

validate_evidence = stage("llm").validate_evidence

validate_rubric = stage("llm").validate_rubric

REQUIREMENTS = [
    {"id": "R1", "text": "Python", "weight": 2},
    {"id": "R2", "text": "Certificate", "weight": 1},
]

SECTIONS = [{"location": "paragraph:2", "text": "Developed Python forecasting tools."}]


def payload():
    return {
        "evidence": [
            {
                "requirement_id": "R1",
                "status": "supported",
                "quote": "Python forecasting",
                "location": "paragraph:2",
            },
            {"requirement_id": "R2", "status": "unknown", "quote": "", "location": ""},
        ]
    }


def test_evidence_and_unknown_preserved():
    score, result = validate_evidence(payload(), REQUIREMENTS, SECTIONS)
    assert score == pytest.approx(200 / 3)
    assert result["unknown_weight_share"] == pytest.approx(1 / 3)


def test_experimental_rubric_opt_in_does_not_mark_it_confirmed():
    rubric = {"J": {"confirmed": False, "requirements": REQUIREMENTS}}
    validate_rubric(rubric, [{"id": "J"}], allow_draft=True)
    assert rubric["J"]["confirmed"] is False


def test_fabricated_evidence_and_duplicate_requirements_rejected():
    value = payload()
    value["evidence"][0]["quote"] = "Ten years Python"
    with pytest.raises(ValueError):
        validate_evidence(value, REQUIREMENTS, SECTIONS)
    value = payload()
    value["evidence"][1]["requirement_id"] = "R1"
    with pytest.raises(ValueError):
        validate_evidence(value, REQUIREMENTS, SECTIONS)


def test_not_applicable_requires_rubric_permission():
    value = payload()
    value["evidence"][1]["status"] = "not_applicable"
    with pytest.raises(ValueError):
        validate_evidence(value, REQUIREMENTS, SECTIONS)


def test_llm_http_contract_and_cache(tmp_path, monkeypatch):
    calls = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return json.dumps(
                {
                    "choices": [
                        {"message": {"content": json.dumps(payload())}}
                    ],
                    "usage": {"total_tokens": 100},
                }
            ).encode()

    def mocked(req, timeout):
        calls.append(json.loads(req.data))
        return Response()

    monkeypatch.setattr(stage("llm").request, "urlopen", mocked)
    scorer = LLMScorer(
        "test-model", "http://localhost:8000/v1/chat/completions", tmp_path
    )
    candidate = {"sections": SECTIONS}
    score, first = scorer.score({}, candidate, REQUIREMENTS)
    score, second = scorer.score({}, candidate, REQUIREMENTS)
    assert len(calls) == 1
    assert first["cache_hit"] is False and second["cache_hit"] is True
    assert calls[0]["messages"][0]["role"] == "system"
    assert calls[0]["response_format"]["json_schema"]["strict"] is True


def test_llm_does_not_truncate(tmp_path):
    scorer = LLMScorer(
        "test", "http://localhost:8000/v1/chat/completions", tmp_path, max_chars=1
    )
    with pytest.raises(ValueError, match="no truncation"):
        scorer.score({}, {"sections": SECTIONS}, REQUIREMENTS)


def test_unconfirmed_rubric_rejected():
    with pytest.raises(ValueError, match="confirmed"):
        validate_rubric(
            {"J": {"confirmed": False, "requirements": REQUIREMENTS}}, [{"id": "J"}]
        )


def test_literal_citation_resolves_wrong_paragraph_without_inventing_text():
    value = payload()
    value["evidence"][0]["location"] = "paragraph:99"
    _, result = validate_evidence(value, REQUIREMENTS, SECTIONS)
    record = result["evidence"][0]
    assert record["location"] == "paragraph:2"
    assert record["citation_correction"]["reported_location"] == "paragraph:99"


def test_bad_evidence_is_repaired_and_usage_is_accumulated(tmp_path, monkeypatch):
    calls = []
    bad = payload()
    bad["evidence"][0]["quote"] = "Fabricated experience"
    responses = [bad, payload()]

    def mocked(req, timeout):
        calls.append(json.loads(req.data))
        answer = responses[len(calls) - 1]

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def read(self):
                return json.dumps(
                    {
                        "choices": [
                            {"message": {"content": json.dumps(answer)}}
                        ],
                        "usage": {
                            "prompt_tokens": 10,
                            "completion_tokens": 5,
                            "total_tokens": 15,
                            "prompt_tokens_details": {"cached_tokens": 2},
                        },
                    }
                ).encode()

        return Response()

    monkeypatch.setattr(stage("llm").request, "urlopen", mocked)
    scorer = LLMScorer("test", "http://localhost:8000/v1/chat/completions", tmp_path)
    score, evidence = scorer.score({}, {"sections": SECTIONS}, REQUIREMENTS)
    assert len(calls) == 2
    assert evidence["repair_count"] == 1
    assert evidence["usage"]["total_tokens"] == 30
    assert evidence["usage"]["prompt_tokens_details"]["cached_tokens"] == 4
    assert score == pytest.approx(200 / 3)
