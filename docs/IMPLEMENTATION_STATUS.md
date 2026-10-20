# Implementation and verification status

Verified on 15 October 2026 with Python 3.11.9. Direct dependency versions are recorded in [requirements-tested.txt](../requirements-tested.txt).

## Implemented

Source organization now follows the workshop: each numbered tool folder contains its actual implementation. `common/` contains file I/O, tokenization, and a numbered-folder import helper; `jobmatch/` contains only CLI dispatch and package metadata.

After relocation, all 30 tests passed (28 in the main run, DVC separately with Windows cache access, and the opt-in Prefect test separately). A cached replay reproduced all 42 original JD/method rankings exactly with zero API requests: [verification](../runs/20261015T103003Z-9124af14/relocation_verification.json). Existing run artifacts and the MLflow database remain available.

- Twelve runnable Python entry points across the numbered tool/matching folders.
- Shared extraction, source references, manifests, hashes, and inventory issue reporting.
- BM25 and TF-IDF scoring, complete rankings, deterministic tie handling, and top-five selection.
- OpenAI Responses API scoring with a versioned prompt, strict output schema, confirmed requirements, exact citation checks, retries, usage accounting, and caching.
- Independent-judgment Precision@5, Recall@5, NDCG@5, shortlist overlap, and vacancy-level macro averages.
- Working DVC, Great Expectations, MLflow, Fairlearn, Evidently, and Prefect adapters.

## Verification

- 21 core tests passed, including a complete three-method flow with mocked OpenAI responses.
- All six installed-library integration tests passed: GX, MLflow, Fairlearn, Evidently, DVC, and Prefect.
- The final combined run passed 26 tests; the DVC test passed separately with Windows machine-cache access.
- Ruff checks and relative documentation links passed.

Integration fixtures contain synthetic text and invented audit group names, not inferred sensitive attributes. A subsequent live OpenAI run completed successfully; see [the live-run notes](LIVE_LLM_RUN.md). The updated core suite passes 24 tests, including citation resolution, corrective retries, and draft-rubric handling.

## Baseline output on the copied collection

The [validated lexical run](../runs/20261015T094629Z-0805f4a4/report.md) assessed 14 JDs and 699 CVs in their source-associated vacancy pools. It produced 28 successful JD/method combinations and 140 shortlist rows, with exactly five unique candidates in every shortlist.

The run also contains [side-by-side shortlist columns](../runs/20261015T094629Z-0805f4a4/comparison_shortlists.csv), full rankings, source/configuration hashes, blank full-pool review templates, and overlap reports. These generated artifacts are ignored by Git and must be versioned separately if shared.

Inventory issues: JD-13 and its 50 CVs are absent; CV-15-035 is not a valid DOCX ZIP archive. All 52 issues are recorded in data/prepared/inventory_issues.json; originals were preserved.

## Configuration and evidence still needed

- Review the generated data/rubric.json before treating experimental LLM shortlists as validated recommendations. The key is now configured locally in .env; it is not stored in reports or source control.
- Supply independent recruiter judgments before comparing suitability metrics or declaring a winning algorithm.
- Supply appropriately collected audit data before drawing real group-evaluation conclusions.
- Initialize Git/DVC in the intended repository before versioning project data; no remote was configured or data uploaded.
- The separate 250-CV collection is not merged automatically.
- OCR, automatic LLM chunking, formal uncertainty/significance analysis, automatic mitigation, and scheduled deployment are not implemented.

See [RUNNING.md](RUNNING.md) for commands.

