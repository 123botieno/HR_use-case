# LLM matching: evidence against a confirmed rubric

## Where this fits

The LLM scorer evaluates CV passages against job-related requirements and returns structured evidence. It is a separate method from BM25 and TF-IDF. Its score is weighted supported-evidence coverage, not a probability of hiring or job success.

## Flow

1. Review a rubric generated from the source JD; confirm requirements and weights before normal scoring.
2. Send one candidate's sections and the requirements to the OpenRouter chat-completions API using the shared workshop OpenRouter key and a strict JSON schema. The compatible endpoint can be changed with `LLM_BASE_URL` for a self-hosted service.
3. Validate every requirement status and resolve each cited quote to literal source text.
4. Retry transient request errors with bounded exponential backoff; allow up to two corrective response attempts after the initial response for invalid evidence.
5. Cache successful responses by request/configuration hash; calculate weighted evidence coverage deterministically in application code.
6. Rank candidates and expose unknown evidence and citation corrections for review.

The prompt treats CVs as untrusted content and instructs the model not to use identity, school prestige, writing style, or career gaps. This instruction does not prove those signals cannot affect model outputs; audits remain necessary.

## Settings and experiment controls

| Setting | Current behavior | Interpretation |
|---|---|---|
| Model | `meta-llama/llama-3.3-70b-instruct` default, override via `OPENROUTER_MODEL` | Record exact response model; model updates can change behavior. |
| Rubric | Per-JD requirements and fixed weights | A content/decision setting. Confirm it before evaluation; changing weights changes the target being measured. |
| Prompt/schema | Versioned prompt and strict JSON schema | Changes should be versioned and evaluated as separate configurations. |
| Temperature | Omitted from API payload | Do not assume deterministic responses; repeated uncached runs may differ. |
| Input limit | 60,000 serialized characters | Longer inputs fail explicitly; no silent truncation or automatic chunking. |
| Concurrency | One worker by default; runner allows up to 8 | Affects throughput and service pressure, not intended score meaning. |
| Retries | Up to 3 request attempts for transient errors; up to 2 evidence corrections | Retries can affect cost and latency; they do not switch algorithms. |

The runner is not a hyperparameter optimizer. Evaluate model, prompt, or rubric changes on development vacancies with fixed blinded judgments, then freeze them for held-out evaluation. Record token use, cache hits, latency, and estimated request costs when token prices are configured.

## Code walkthrough

1. The `score.py` entry point dispatches to the shared runner with `--methods llm`.
2. `execute()` loads and validates the dataset, selects vacancies and pools, loads the rubric, and calls `validate_rubric()`. Unconfirmed rubrics fail unless the explicitly experimental override is used.
3. `LLMScorer.score()` combines one candidate's source sections with the JD requirements and rejects serialized input above the configured character limit.
4. It builds a chat-completions API request with the model, system instructions, `store=false`, and a strict JSON evidence schema. It hashes the request and prompt version to check the local response cache.
5. If not cached, `_request()` sends HTTPS requests, retries transient network/HTTP errors with bounded backoff, and `_text()` extracts completed output while detecting refusals.
6. `validate_evidence()` checks requirement IDs and statuses, resolves quotes to literal source text, and calculates weighted supported-evidence coverage. Invalid uncached output can trigger corrective requests; repeated failure is saved under the cache's `validation_failures` directory and raised.
7. Successful responses are cached. The scorer attaches model, prompt/schema version, token usage, repair count, cache status, and optional estimated cost to the evidence record.
8. `execute()` scores candidates, sends returned values through shared `rank()` and `validate_rankings()`, then writes run JSON, CSV outputs, judgment template, comparison JSON, and report Markdown.

API or evidence-validation failures are caught by the runner per JD-method pair and recorded in `run.json` under `failures`; no lexical fallback is used. A run with any such failure is marked incomplete.

## Run and inspect

```powershell
python -m jobmatch rubric-template --output data/rubric.json
# Review requirements and weights, then set confirmed=true for each JD.
# Copy .env.example to .env and add the workshop-provided shared key.
python 07-job-matching/llm/score.py --rubric data/rubric.json --jd JD-01
```

API credentials are not stored in the repository. CV text is sent to the configured provider, so use only data approved for that service under the workshop's data-use policy. The generated template is a draft, not a validated hiring rubric.

## What discrepancy can it surface?

Evidence records show which requirements were supported, explicitly not met, unknown, or not applicable, and where source quotes were found. If a candidate scores poorly with a large unknown share, that can indicate missing evidence rather than lack of qualification. A citation failure becomes a visible method failure instead of being silently treated as evidence.

## Discussion points

- Are requirements observable from CVs and weighted in a defensible way?
- How should unknown evidence be handled and routed to recruiter review?
- Do repeated runs change shortlist membership or only evidence wording?
- Are input length and document formatting causing unequal failures?
- How will prompt injection, fabricated citations, and sensitive attributes be checked?

## Limits

Structured output constrains format, not truth. Literal quote checks validate citation location, not whether a passage supports the claim. Long-CV chunking is not implemented. The model can still reflect biases in data or learned associations despite prompt instructions.

## Related stages

See the [shared run contract](../README.md), [comparison procedure](../comparison/README.md), and workshop hub for experiment tracking.
