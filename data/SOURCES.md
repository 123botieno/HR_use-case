# Data sources and license notes

## Supplied CV and job-description collections

- **Files:** two locally supplied collections previously stored under `Ethiopia_15_Government_JDs_750_CVs/` and `Ethiopia_250_Detailed_WORD_CVs/`.
- **Original publisher, collection method, and license:** not recorded in the workspace. The filenames do not establish a source or permission to redistribute. Obtain the data owner's provenance and written license/authorization before using or sharing these documents.
- **Repository handling:** raw documents and derived candidate-level prepared data are excluded from Git. The root `downloads.json` records SHA-256 hashes and relative paths for the locally available files. Restore from a trusted USB copy with `python scripts/download.py --from <USB folder>`; the helper rejects path traversal and verifies every copied file.
- **Changes:** `00-data/prepare.py` extracts supported text and records document IDs, associations, hashes, and inventory issues under ignored `data/prepared/`. It does not alter the source documents. Review the preparation report for missing and unreadable files.
- **Fairness teaching data:** see [`04-fairlearn/data/SOURCES.md`](../04-fairlearn/data/SOURCES.md). That cohort is generated locally and contains no real applicants.

## Model and software

The matching code uses BM25 and TF-IDF implementations from scikit-learn/SciPy dependencies, plus the configurable OpenAI-compatible chat-completions API. The default workshop model is OpenRouter's `meta-llama/llama-3.3-70b-instruct`; OpenRouter currently lists JSON-schema structured-output support for this model ([model page](https://openrouter.ai/meta-llama/llama-3.3-70b-instruct)). Meta distributes the model under its custom [Llama 3.3 Community License](https://github.com/meta-llama/llama-models/blob/main/models/llama3_3/LICENSE), not a standard permissive open-source license. The workshop uses OpenRouter's hosted service; no model weights are copied into this repository. The selected provider and OpenRouter's service terms also apply. No model fine-tuning or weight changes are made. See `requirements.lock` for package versions; each dependency retains its upstream license.

The project currently has no top-level license file. Reuse or redistribution of the software and data therefore requires the relevant owners' terms to be confirmed; this file is a provenance record, not a grant of rights.
