# 00 — Data preparation

## Purpose

Prepare shared, traceable inputs for LLM, BM25, and TF-IDF. Extraction, manifest preparation, and draft rubric construction are implemented in [prepare.py](prepare.py).

## Inputs

The existing JD and CV collections listed in the [project README](../README.md). Keep original documents unchanged and inventory document types, counts, duplication, and candidate-to-vacancy associations before processing.

## Planned workflow

1. Assign stable document, candidate, and vacancy IDs; record source-relative paths and file hashes.
2. Extract text with page or paragraph references. Route unreadable files and failed OCR to review.
3. Produce a matching-text version with direct identity information removed where practical.
4. Confirm job-related requirements with a recruiter. Represent evidence as supported, explicitly not met, unknown, or not applicable.
5. Freeze one candidate pool per JD and split development and evaluation sets by vacancy. Check candidate/document overlap across partitions to avoid leakage.
6. Collect independent suitability judgments and graded relevance, blind to the matching algorithm.

## Planned outputs

- Source manifest: document ID, candidate/JD ID, relative path, hash, extraction status, and text version.
- Extracted text and source references.
- Confirmed JD requirements with rubric versions.
- Candidate pools and fixed evaluation partitions.
- Recruiter judgments and a separate, restricted audit dataset where available.

Names, photographs, gender, community identity, and other sensitive attributes must not become scoring features. Do not infer audit attributes from names or text. Missing experience or certification evidence remains unknown.

## Setup and use

From the project root:

```powershell
python 00-data/prepare.py --source "Ethiopia_15_Government_JDs_750_CVs/Ethiopia_15_Public_Sector_JDs_750_CVs"
```

Writes `data/prepared/dataset.json`, `manifest.csv`, and `inventory_issues.json`. DOCX extraction includes table paragraphs; TXT/MD are also supported by the extractor. PDF extraction requires the optional pypdf package; scanned pages require separate OCR. The source adapter currently targets the supplied job_index/candidate_manifest CSV format, not the separate 250-CV collection. Deidentification is partial and tailored to these synthetic CVs.

Sensitive source documents and generated artifacts should stay out of Git. See [the running guide](../docs/RUNNING.md).

## Next stage

[DVC](../01-dvc/README.md) records versions; [Great Expectations](../02-great-expectations/README.md) checks data quality before matching.

## Synthetic fairness teaching data

The Fairlearn stage contains a separate reproducible demo: [synthetic HR data and reports](../04-fairlearn/synthetic_hr_demo/README.md). It creates fabricated historical application records with controlled disparities by gender, ethnicity, economic class, and geography. These files are explicitly synthetic and are not evidence about real applicants or historical hiring.

