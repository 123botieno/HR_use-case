"""Reusable ranking and Fairlearn helpers for the job matching workshop.

The matching inputs are job text and fictional, de-identified CV text. Audit
attributes live only in the synthetic history table and are never features.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


WORKSHOP_DIR = Path(__file__).resolve().parent
REPO_ROOT = WORKSHOP_DIR.parent
DATA_DIR = WORKSHOP_DIR / "data"
DEFAULT_LLM_CACHE = DATA_DIR / "llm_precomputed_top5.csv"
TOKEN_PATTERN = re.compile(r"(?u)\b\w\w+\b")


def load_jobs(data_dir: str | Path = DATA_DIR) -> pd.DataFrame:
    """Load job metadata and text, one row per job."""
    root = Path(data_dir) / "job_descriptions"
    index = pd.read_csv(root / "jobs.csv", dtype={"job_id": str})
    texts = {p.stem: p.read_text(encoding="utf-8") for p in root.glob("JD-*.txt")}
    index["text"] = index["job_id"].map(texts)
    if index["text"].isna().any():
        raise ValueError("A job description text file is missing")
    return index


def load_candidates(job_id: str, data_dir: str | Path = DATA_DIR) -> pd.DataFrame:
    """Load candidate CV text for one vacancy; IDs are stable across files."""
    root = Path(data_dir) / "candidate_cvs" / job_id
    rows = []
    for path in sorted(root.glob("CV-*.txt")):
        candidate_id = path.stem
        rows.append(
            {"candidate_id": candidate_id, "job_id": job_id,
             "text": path.read_text(encoding="utf-8")}
        )
    if not rows:
        raise ValueError(f"No CVs found for {job_id}")
    return pd.DataFrame(rows)


def load_history(data_dir: str | Path = DATA_DIR) -> pd.DataFrame:
    """Load the fictional decision history while preserving unknown outcomes."""
    return pd.read_csv(Path(data_dir) / "historical_hiring_synthetic.csv")


def preprocess_text(text: str) -> str:
    """Normalize case and whitespace without removing qualification terms."""
    return " ".join(str(text).lower().split())


def _rank(candidate_ids, scores, algorithm, evidence=None):
    frame = pd.DataFrame(
        {"candidate_id": candidate_ids, "score": np.asarray(scores, dtype=float)}
    )
    frame["algorithm"] = algorithm
    if evidence is not None:
        frame["evidence"] = evidence
    frame = frame.sort_values(["score", "candidate_id"], ascending=[False, True]).reset_index(drop=True)
    frame["rank"] = np.arange(1, len(frame) + 1)
    return frame


def match_tfidf(
    job_description: str,
    candidate_cvs: pd.DataFrame,
    *,
    ngram_range: tuple[int, int] = (1, 1),
    max_features: int | None = None,
    min_df: int | float = 1,
    max_df: int | float = 1.0,
) -> pd.DataFrame:
    """Rank CVs by TF-IDF cosine similarity; scores are method-specific."""
    docs = [preprocess_text(t) for t in candidate_cvs["text"]]
    query = preprocess_text(job_description)
    vectorizer = TfidfVectorizer(
        ngram_range=ngram_range, max_features=max_features,
        min_df=min_df, max_df=max_df,
    )
    matrix = vectorizer.fit_transform([query, *docs])
    scores = cosine_similarity(matrix[0:1], matrix[1:]).ravel()
    return _rank(candidate_cvs["candidate_id"].tolist(), scores, "TF-IDF")


def _tokens(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(preprocess_text(text))


def match_bm25(
    job_description: str,
    candidate_cvs: pd.DataFrame,
    *,
    k1: float = 1.5,
    b: float = 0.75,
) -> pd.DataFrame:
    """Rank CVs using a compact Okapi BM25 implementation."""
    if k1 < 0 or not 0 <= b <= 1:
        raise ValueError("BM25 requires k1 >= 0 and b between 0 and 1")
    docs = [_tokens(t) for t in candidate_cvs["text"]]
    query = sorted(set(_tokens(job_description)))
    n_docs = len(docs)
    avgdl = sum(map(len, docs)) / max(n_docs, 1)
    dfs = Counter(term for doc in docs for term in set(doc))
    scores = []
    for doc in docs:
        frequencies = Counter(doc)
        score = 0.0
        for term in query:
            tf = frequencies[term]
            if not tf:
                continue
            df = dfs[term]
            idf = np.log(1 + (n_docs - df + 0.5) / (df + 0.5))
            denominator = tf + k1 * (1 - b + b * len(doc) / max(avgdl, 1))
            score += idf * (tf * (k1 + 1)) / denominator
        scores.append(score)
    return _rank(candidate_cvs["candidate_id"].tolist(), scores, "BM25")


def select_top_k(ranking: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    if k < 1:
        raise ValueError("k must be at least 1")
    return ranking.nsmallest(k, "rank").copy()


def compare_rankings(rankings: dict[str, pd.DataFrame], k: int = 5) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return long-form ranks and pairwise Top-K overlap counts."""
    long = pd.concat(
        [df[["candidate_id", "score", "rank"]].assign(algorithm=name)
         for name, df in rankings.items()], ignore_index=True
    )
    names = list(rankings)
    overlaps = []
    for i, left in enumerate(names):
        left_ids = set(select_top_k(rankings[left], k)["candidate_id"])
        for right in names[i + 1:]:
            right_ids = set(select_top_k(rankings[right], k)["candidate_id"])
            overlaps.append({"left": left, "right": right,
                             "shared_top_k": len(left_ids & right_ids),
                             "k": k})
    return long, pd.DataFrame(overlaps)


def match_llm(
    job_id: str,
    job_description: str,
    candidate_cvs: pd.DataFrame,
    *,
    mode: str = "cached",
    model: str = "meta-llama/llama-3.3-70b-instruct",
    rubric: list[dict] | None = None,
    scoring_prompt: str | None = None,
    temperature: float | None = None,
    cache_path: str | Path = DEFAULT_LLM_CACHE,
    endpoint: str = "https://openrouter.ai/api/v1/chat/completions",
) -> pd.DataFrame:
    """Use verified project LLM evidence scoring or historical cached Top-5.

    The packaged cache contains only K=5 lists from an earlier project run.
    It is not live inference and cannot support different K values. Live mode
    reuses the project's LLMScorer and its evidence validation/caching.
    """
    if mode == "cached":
        cache = pd.read_csv(cache_path, dtype={"job_id": str, "candidate_id": str})
        rows = cache.loc[cache.job_id == job_id].copy()
        if rows.empty:
            raise ValueError(f"No cached LLM ranking is packaged for {job_id}")
        if not set(rows.candidate_id).issubset(set(candidate_cvs.candidate_id)):
            raise ValueError("Cached LLM candidate IDs do not match this CV pool")
        rows["algorithm"] = "LLM (cached project run)"
        rows["cache_status"] = "cached; not live inference"
        return rows.sort_values("rank").reset_index(drop=True)
    if mode != "live":
        raise ValueError("mode must be 'cached' or 'live'")
    if not rubric:
        raise ValueError("Live LLM mode requires an explicit job-related rubric")
    sys.path.insert(0, str(REPO_ROOT))
    from common.stages import stage
    from common.io import digest, load, save
    llm_module = stage("llm")
    scorer_class = llm_module.LLMScorer
    scorer = scorer_class(
        model=model, endpoint=endpoint,
        cache=WORKSHOP_DIR / ".llm_cache",
    )
    requirements = [
        {"id": f"R{i+1}", "text": str(item["text"]),
         "weight": float(item.get("weight", 1)),
         "applicable": True}
        for i, item in enumerate(rubric)
    ]
    job = {"id": job_id, "text": job_description}
    scores, evidence = [], []
    for row in candidate_cvs.itertuples(index=False):
        sections = [
            {"location": f"section:{i+1}", "text": paragraph}
            for i, paragraph in enumerate(row.text.split("\n\n")) if paragraph.strip()
        ]
        candidate = {"sections": sections}
        if scoring_prompt is None and temperature is None:
            score, detail = scorer.score(job, candidate, requirements)
        else:
            # The existing project scorer owns request transport and evidence validation;
            # this small workshop extension adds optional prompt/temperature controls.
            import json
            content = {"requirements": requirements, "sections": sections}
            system = llm_module.SYSTEM
            if scoring_prompt:
                system += "\nWorkshop scoring instruction (job-related only): " + scoring_prompt
            body = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(content, ensure_ascii=False)},
                ],
                "response_format": {"type": "json_schema", "json_schema": {
                    "name": "candidate_evidence", "strict": True,
                    "schema": llm_module.EVIDENCE_SCHEMA,
                }},
            }
            if temperature is not None:
                if not 0 <= temperature <= 2:
                    raise ValueError("temperature must be between 0 and 2")
                body["temperature"] = temperature
            cache_key = digest({"body": body, "prompt_version": "workshop-llm-v1"})
            cache_file = scorer.cache / f"workshop-{cache_key}.json"
            if cache_file.exists():
                response = load(cache_file)
            else:
                response = scorer._request(body)
                save(cache_file, response)
            payload = json.loads(scorer._text(response))
            score, detail = llm_module.validate_evidence(payload, requirements, sections)
        scores.append(score)
        evidence.append(detail)
    result = _rank(candidate_cvs.candidate_id.tolist(), scores, "LLM (live)", evidence)
    result["cache_status"] = "project response cache may be used"
    return result


def prepare_group_selection_data(
    ranking: pd.DataFrame, history: pd.DataFrame, *, job_id: str, k: int = 5,
    group: str = "sex",
) -> pd.DataFrame:
    if group not in {"sex", "geographic_location"}:
        raise ValueError("Audit group must be sex or geographic_location")
    selected = set(select_top_k(ranking, k)["candidate_id"])
    data = history.loc[history.job_id == job_id, ["candidate_id", "job_id", group]].copy()
    data["selected"] = data.candidate_id.isin(selected).astype(int)
    return data


def fairness_metrics(selection_data: pd.DataFrame, group: str) -> tuple[pd.DataFrame, dict]:
    """Compute Fairlearn selection rates and demographic parity difference/ratio."""
    from fairlearn.metrics import (
        MetricFrame, selection_rate, demographic_parity_difference,
        demographic_parity_ratio,
    )
    y_pred = selection_data["selected"].astype(int)
    groups = selection_data[group]
    frame = MetricFrame(metrics={"selection_rate": selection_rate},
                        y_true=np.ones(len(y_pred), dtype=int),
                        y_pred=y_pred, sensitive_features=groups)
    details = {
        "demographic_parity_difference": float(
            demographic_parity_difference(np.ones(len(y_pred), dtype=int), y_pred,
                                          sensitive_features=groups)
        ),
        "demographic_parity_ratio": float(
            demographic_parity_ratio(np.ones(len(y_pred), dtype=int), y_pred,
                                     sensitive_features=groups)
        ),
    }
    result = frame.by_group["selection_rate"].to_frame()
    result["n"] = groups.value_counts().reindex(result.index).astype(int)
    return result.reset_index(names=group), details


def group_agreement_metrics(
    selection_data: pd.DataFrame, group: str,
    historical_column: str = "historical_shortlisted",
) -> pd.DataFrame:
    """Fairlearn agreement rates against history; never call these correctness."""
    from fairlearn.metrics import MetricFrame, selection_rate
    merged = selection_data.merge(
        load_history()[["candidate_id", historical_column]],
        on="candidate_id", validate="one_to_one",
    )
    frame = MetricFrame(
        metrics={"agreement_rate": lambda y, p: float(np.mean(y == p))},
        y_true=merged[historical_column].astype(int),
        y_pred=merged.selected.astype(int), sensitive_features=merged[group],
    )
    return frame.by_group.reset_index(names=group)


def fairness_metrics_with_reference_labels(
    selection_data: pd.DataFrame,
    group: str,
    reference_labels: pd.Series,
    *,
    labels_are_independent_and_complete: bool = False,
) -> tuple[pd.DataFrame, float]:
    """Compute group performance and equalized-odds metrics only with valid labels.

    The caller must explicitly attest that labels cover the applicant pool and
    are independent of the selection process. Historical hire labels in this
    workshop fail that requirement and must not be supplied here.
    """
    if not labels_are_independent_and_complete:
        raise ValueError("Independent complete reference labels are required")
    if reference_labels.isna().any() or len(reference_labels) != len(selection_data):
        raise ValueError("Reference labels must be complete and row-aligned")
    from fairlearn.metrics import MetricFrame, selection_rate, equalized_odds_difference
    from sklearn.metrics import accuracy_score, precision_score, recall_score
    y_true = reference_labels.astype(int).to_numpy()
    y_pred = selection_data.selected.astype(int).to_numpy()
    groups = selection_data[group].to_numpy()
    metrics = {
        "selection_rate": selection_rate,
        "accuracy": accuracy_score,
        "precision": lambda y, p: precision_score(y, p, zero_division=0),
        "recall": lambda y, p: recall_score(y, p, zero_division=0),
    }
    frame = MetricFrame(metrics=metrics, y_true=y_true, y_pred=y_pred,
                        sensitive_features=groups)
    eo_difference = float(equalized_odds_difference(
        y_true, y_pred, sensitive_features=groups
    ))
    return frame.by_group, eo_difference


def plot_rankings(rankings: dict[str, pd.DataFrame], k: int = 10):
    """Plot rank positions for the union of candidates appearing in Top-K."""
    import matplotlib.pyplot as plt
    ids = sorted(set().union(*(set(df.head(k).candidate_id) for df in rankings.values())))
    fig, ax = plt.subplots(figsize=(10, max(4, len(ids) * 0.24)))
    for name, ranking in rankings.items():
        positions = ranking.set_index("candidate_id")["rank"]
        ax.scatter(positions.reindex(ids), ids, label=name, s=35)
    ax.set_xlabel("Rank (lower is better)")
    ax.set_ylabel("Candidate ID")
    ax.grid(axis="x", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    return fig, ax


def plot_group_rates(group_rates: pd.DataFrame, *, group: str, title: str):
    import matplotlib.pyplot as plt
    ax = group_rates.set_index(group)["selection_rate"].plot.bar(
        color="#3977a8", ylim=(0, 1), figsize=(7, 4),
    )
    ax.set_ylabel("Selection rate")
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.25)
    return ax.figure, ax
