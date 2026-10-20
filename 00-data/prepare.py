"""Extract documents with source locations and inventory missing files."""

# ruff: noqa: E402
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import re
import zipfile
from xml.etree import ElementTree
from common.io import digest, read_csv, save, write_csv

NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def extract(path):
    path = Path(path)
    if path.suffix.lower() == ".docx":
        with zipfile.ZipFile(path) as archive:
            root = ElementTree.fromstring(archive.read("word/document.xml"))
        paragraphs = [
            "".join(n.text or "" for n in p.iter(NS + "t")).strip()
            for p in root.iter(NS + "p")
        ]
        return [
            {"location": f"paragraph:{i}", "text": text}
            for i, text in enumerate(paragraphs, 1)
            if text
        ]
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        return [
            {"location": f"page:{i}", "text": page.extract_text() or ""}
            for i, page in enumerate(PdfReader(path).pages, 1)
        ]
    if path.suffix.lower() in {".txt", ".md"}:
        return [
            {"location": f"line:{i}", "text": text.strip()}
            for i, text in enumerate(
                path.read_text(encoding="utf-8-sig").splitlines(), 1
            )
            if text.strip()
        ]
    raise ValueError(f"Unsupported document type: {path.suffix}")


def matching_sections(sections, candidate=False, name=""):
    result = []
    for index, section in enumerate(sections):
        text = section["text"]
        # Known source format: first paragraph is the candidate's name.
        if candidate and index == 0:
            continue
        if candidate and re.match(
            r"(?i)^(synthetic id|name|full name|email|phone|gender|sex|nationality|date of birth|community)\s*:",
            text,
        ):
            continue
        if candidate and re.match(r"(?i)^application:", text):
            continue
        if name:
            text = re.sub(re.escape(name), "[REDACTED]", text, flags=re.I)
        text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[EMAIL]", text)
        result.append({**section, "text": text})
    return result


def prepare(source, output):
    source, output = Path(source).resolve(), Path(output)
    jobs, candidates, issues, manifest = [], [], [], []
    job_index = read_csv(source / "job_index.csv")
    candidate_index = read_csv(source / "candidate_manifest.csv")

    def document(path, identifier, kind, jd_id, name=""):
        try:
            resolved = path.resolve()
            if not resolved.is_relative_to(source):
                raise ValueError("Source path escapes dataset root")
            raw = resolved.read_bytes()
            sections = matching_sections(extract(resolved), kind == "cv", name)
            text = "\n".join(s["text"] for s in sections)
            if len(text.strip()) < 30:
                raise ValueError(
                    "Insufficient readable text; OCR/manual review required"
                )
            record = {
                "id": identifier,
                "jd_id": jd_id,
                "text": text,
                "sections": sections,
                "source": resolved.relative_to(source).as_posix(),
                "sha256": __import__("hashlib").sha256(raw).hexdigest(),
                "text_hash": digest(text),
            }
            manifest.append(
                {
                    "id": identifier,
                    "kind": kind,
                    "jd_id": jd_id,
                    "source": record["source"],
                    "sha256": record["sha256"],
                    "status": "ok",
                }
            )
            return record
        except (
            OSError,
            ValueError,
            zipfile.BadZipFile,
            ElementTree.ParseError,
            ImportError,
        ) as exc:
            issues.append(
                {
                    "id": identifier,
                    "kind": kind,
                    "jd_id": jd_id,
                    "source": str(path.relative_to(source)),
                    "reason": str(exc),
                }
            )
            return None

    for row in job_index:
        jd_id = f"JD-{int(row['JD_ID']):02d}"
        folders = sorted(source.glob(f"{int(row['JD_ID']):02d}_*"))
        path = (
            folders[0] / "JD.docx"
            if folders
            else source / f"{int(row['JD_ID']):02d}_MISSING/JD.docx"
        )
        record = document(path, jd_id, "jd", jd_id)
        if record:
            jobs.append({**record, "title": row["Title"], "job_family": row["Sector"]})
    available = {job["id"] for job in jobs}
    for row in candidate_index:
        jd_id = f"JD-{int(row['JD_ID']):02d}"
        candidate_id = f"CV-{int(row['JD_ID']):02d}-{int(row['Candidate_Number']):03d}"
        record = document(
            source / row["CV_Path"],
            candidate_id,
            "cv",
            jd_id,
            row.get("Fictional_Name", ""),
        )
        if record and jd_id in available:
            candidates.append(record)
        elif record:
            issues.append(
                {
                    "id": candidate_id,
                    "kind": "cv",
                    "jd_id": jd_id,
                    "source": record["source"],
                    "reason": "Associated JD unavailable",
                }
            )
    # Synthetic fit tiers intentionally never enter the prepared matching dataset.
    dataset = {
        "schema_version": 1,
        "extraction_version": "docx-xml-v1",
        "deidentification": "partial; manual review required before real candidate use",
        "pool_policy": "source vacancy association",
        "jobs": jobs,
        "candidates": candidates,
    }
    dataset["dataset_hash"] = digest(dataset)
    save(output / "dataset.json", dataset)
    save(output / "inventory_issues.json", issues)
    write_csv(output / "manifest.csv", manifest)
    return {
        "jobs": len(jobs),
        "candidates": len(candidates),
        "issues": len(issues),
        "dataset_hash": dataset["dataset_hash"],
    }


def build_rubric(data):
    result = {}
    headings = {
        "roles and responsibilities",
        "qualifications and experience",
        "required and desired skills",
    }
    stop = {"employment terms and application", "original job advertisement"}
    for job in data["jobs"]:
        active, requirements = False, []
        for section in job["sections"]:
            line = section["text"].strip()
            if line.lower() in headings:
                active = True
                continue
            if line.lower() in stop:
                active = False
            if active:
                requirements.append(
                    {
                        "id": f"R{len(requirements) + 1}",
                        "text": line,
                        "weight": 1,
                        "applicable": True,
                        "jd_source_location": section["location"],
                    }
                )
        result[job["id"]] = {"confirmed": False, "requirements": requirements}
    return result


if __name__ == "__main__":
    from jobmatch.cli import main

    raise SystemExit(main(["prepare"] + sys.argv[1:]))
