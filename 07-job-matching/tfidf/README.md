# TF-IDF: weighted term overlap baseline

## Where this fits

TF-IDF ranks candidates by cosine similarity between a JD vector and each CV vector. It is a lexical retrieval baseline, not a qualification verifier or probability of hiring.

## How scoring works

The vectorizer fits a vocabulary and inverse document frequencies on the frozen CV pool for one JD. It transforms the JD with that vocabulary, then computes cosine similarity to every CV. Terms that are common across the pool receive less weight; terms that are more distinctive receive more. L2 normalization makes the score depend on vector direction rather than raw document length alone.

## Settings (hyperparameters)

| Setting | Current value | Effect and tuning question |
|---|---|---|
| `ngram_range` | `(1, 1)` | Word unigrams only. Bigrams can capture phrases such as “project management” but create a larger, sparser vocabulary. |
| `lowercase` | `True` | Treats capitalization variants alike. |
| `token_pattern` | Shared `TOKEN_PATTERN` | Controls token boundaries and which terms are retained. Language and punctuation choices matter. |
| `stop_words` | `None` | No common words are removed. A list may help or may remove meaningful local terms. |
| `norm` | `l2` | Normalizes each vector before cosine similarity. |
| `min_df` / `max_df` | scikit-learn defaults | No explicit frequency filtering: terms are retained according to library defaults. A controlled experiment could set these explicitly. |

The current runner fixes these settings and does not sweep configurations. Vocabulary and IDF values are saved in run configuration so the fitted representation can be inspected.

## Code walkthrough

1. The `score.py` entry point invokes the shared runner for the TF-IDF method.
2. `execute()` loads and validates the dataset, selects vacancies, and creates a sorted candidate pool for each JD.
3. The runner calls `tfidf(query, documents)`. `TfidfVectorizer.fit_transform()` learns vocabulary and IDF weights from the pool's CV texts; `.transform()` encodes the JD using that vocabulary.
4. `cosine_similarity()` compares the JD vector with each candidate vector. Sparse vector products identify shared terms and their weighted contributions for the evidence field.
5. The method returns scores, evidence, and configuration including the vocabulary, IDF values, and whether the JD became a zero vector.
6. Shared `rank()` sorts candidates, applies deterministic ID tie-breaking, assigns top-five flags, and identifies all-zero rankings/cutoff ties. `validate_rankings()` checks pool and output invariants.
7. The runner writes the full run JSON, rankings/shortlists CSVs, blind judgment template, comparison report, and human-readable markdown report.

An empty-vocabulary exception or other scoring error is recorded for that JD-method pair in `run.json` under `failures`; the runner does not substitute BM25 or another method.

## How to test a setting

On development vacancies, hold candidate pools and labels fixed while varying one setting or a predeclared grid: for example unigram versus unigram+bigram, or selected `min_df` values. Compare supported Precision@5, Recall@5, and NDCG@5. Freeze the best development configuration before evaluating held-out vacancies. Do not treat overlap with BM25 as correctness.

## Run and inspect

```powershell
python 07-job-matching/tfidf/score.py --jd JD-01
```

The shared runner writes full rankings, top-five lists, raw cosine scores, and up to 20 shared weighted-term contributions. If the JD has no vocabulary overlap with the fitted candidate corpus, the configuration records `query_zero_vector=true`; the resulting equal zero scores produce an uninformative ranking flag. An empty vocabulary is recorded as a method failure.

## What discrepancy can it surface?

Inspect common weighted terms for a high-ranked CV to determine whether it matched real requirements or only generic JD language. Compare `query_zero_vector`, vocabulary, and pool hashes when scores change between runs. Fitted vocabulary and IDF depend on the candidate pool, so changing that pool changes the model representation.

## Discussion points

- Would phrase-level bigrams improve precision for this role family?
- Are common words noise, or do some encode required local qualifications?
- How should spelling variants, multilingual text, and transliteration be normalized?
- Does fitting on each vacancy pool make cross-vacancy score comparisons inappropriate?
- Which relevance metric should decide whether a setting is retained?

## Limits

TF-IDF does not understand synonyms, context, experience duration, or evidence quality. Scores depend on the pool and configuration; do not compare raw magnitudes with other methods.

## Related stages

See the [shared run contract](../README.md), [benchmark metrics](../comparison/README.md), and [MLflow experiment logging](../../03-mlflow/README.md).
