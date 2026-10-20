from common.stages import stage

import zipfile

import pytest

from common.io import digest, save, load

extract = stage("data").extract

prepare = stage("data").prepare

execute = stage("matching").execute

validate_dataset = stage("validation").validate_dataset


def dataset():
    def doc(identifier, text):
        return {
            "id": identifier,
            "jd_id": "J",
            "text": text,
            "text_hash": digest(text),
            "sections": [{"location": "line:1", "text": text}],
        }

    value = {
        "jobs": [doc("J", "python forecasting")],
        "candidates": [
            doc(f"C{i}", "python forecasting" if i == 0 else "tax accounting")
            for i in range(6)
        ],
    }
    value["dataset_hash"] = digest(value)
    return value


def test_pipeline_lexical_and_explicit_llm_failure(tmp_path, monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    path = tmp_path / "dataset.json"
    save(path, dataset())
    directory, run = execute(path, tmp_path / "runs")
    assert run["status"] == "incomplete"
    assert [r["algorithm"] for r in run["results"]] == ["bm25", "tfidf"]
    assert run["failures"][0]["algorithm"] == "llm"
    for entry in run["results"]:
        assert entry["ranking"][0]["candidate_id"] == "C0"
        assert sum(r["shortlisted"] for r in entry["ranking"]) == 5
    assert (directory / "judgments_template.csv").exists()
    assert (directory / "report.md").exists()
    assert run["results"][0]["pool_hash"] == run["results"][1]["pool_hash"]


def test_tampered_data_rejected():
    data = dataset()
    data["candidates"][0]["text"] = "tampered"
    with pytest.raises(ValueError, match="hash"):
        validate_dataset(data)


def test_docx_text_and_source_locations(tmp_path):
    path = tmp_path / "sample.docx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Python </w:t></w:r><w:r><w:t>forecasting</w:t></w:r></w:p></w:body></w:document>',
        )
    assert extract(path) == [{"location": "paragraph:1", "text": "Python forecasting"}]


def test_prepare_reports_missing_source_and_excludes_synthetic_labels(tmp_path):
    source = tmp_path / "source"
    folder = source / "01_Test"
    folder.mkdir(parents=True)
    xml = '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{}</w:body></w:document>'

    def docx(name, paragraphs):
        with zipfile.ZipFile(folder / name, "w") as archive:
            archive.writestr(
                "word/document.xml",
                xml.format(
                    "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs)
                ),
            )

    docx("JD.docx", ["Python forecasting and data engineering position"])
    docx(
        "CV.docx", ["Person Name", "Python forecasting and data engineering experience"]
    )
    (source / "job_index.csv").write_text(
        "JD_ID,Title,Sector\n1,Test,IT\n2,Missing,IT\n"
    )
    (source / "candidate_manifest.csv").write_text(
        "JD_ID,Candidate_Number,Fictional_Name,CV_Path,Synthetic_Fit_Tier\n1,1,Person Name,01_Test/CV.docx,Strong\n2,1,Other,02_Missing/CV.docx,Weak\n"
    )
    output = tmp_path / "prepared"
    summary = prepare(source, output)
    assert (
        summary["jobs"] == 1 and summary["candidates"] == 1 and summary["issues"] == 2
    )
    text = (output / "dataset.json").read_text()
    assert "Strong" not in text and "Person Name" not in text
    assert validate_dataset(load(output / "dataset.json"))["success"]


def test_three_method_pipeline_with_mock_openai(tmp_path, monkeypatch):
    import json

    value = dataset()
    path = tmp_path / "dataset.json"
    save(path, value)
    rubric = tmp_path / "rubric.json"
    save(
        rubric,
        {
            "J": {
                "confirmed": True,
                "requirements": [
                    {
                        "id": "R1",
                        "text": "Python forecasting",
                        "weight": 1,
                        "applicable": True,
                    }
                ],
            }
        },
    )
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-key")
    calls = []

    def mocked(req, timeout):
        body = json.loads(req.data)
        user = json.loads(body["input"][1]["content"])
        section = user["sections"][0]
        supported = "python" in section["text"]
        response = {
            "status": "completed",
            "model": body["model"],
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": json.dumps(
                                {
                                    "evidence": [
                                        {
                                            "requirement_id": "R1",
                                            "status": "supported"
                                            if supported
                                            else "unknown",
                                            "quote": section["text"]
                                            if supported
                                            else "",
                                            "location": section["location"]
                                            if supported
                                            else "",
                                        }
                                    ]
                                }
                            ),
                        }
                    ],
                }
            ],
            "usage": {"input_tokens": 20, "output_tokens": 10},
        }
        calls.append(body)

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def read(self):
                return json.dumps(response).encode()

        return Response()

    monkeypatch.setattr(stage("llm").request, "urlopen", mocked)
    directory, run = execute(path, tmp_path / "runs", rubric_path=rubric)
    assert run["status"] == "complete"
    assert len(run["results"]) == 3
    assert all(e["ranking"][0]["candidate_id"] == "C0" for e in run["results"])
    assert len(calls) == 2  # Identical CV content reuses validated cache entries.
    assert (directory / "comparison_shortlists.csv").exists()
    assert len(load(directory / "comparison.json")["overlap"]) == 3
