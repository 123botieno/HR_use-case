# ruff: noqa: E402
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import math
from collections import Counter
from common.text import tokenize, TOKEN_PATTERN


def bm25(query, documents, k1=1.5, b=0.75):
    if k1 <= 0 or not 0 <= b <= 1:
        raise ValueError("Require k1 > 0 and 0 <= b <= 1")
    tokens = [tokenize(text) for text in documents]
    if not tokens or not any(tokens):
        raise ValueError("Empty BM25 corpus")
    frequencies = [Counter(t) for t in tokens]
    document_frequency = Counter(term for t in tokens for term in set(t))
    average_length = sum(map(len, tokens)) / len(tokens)
    scores, evidence = [], []
    for terms in frequencies:
        contributions = {}
        for term in sorted(set(tokenize(query))):
            tf = terms[term]
            if tf:
                df = document_frequency[term]
                idf = math.log(1 + (len(tokens) - df + 0.5) / (df + 0.5))
                contributions[term] = (
                    idf
                    * tf
                    * (k1 + 1)
                    / (tf + k1 * (1 - b + b * sum(terms.values()) / average_length))
                )
        scores.append(sum(contributions.values()))
        evidence.append(sorted(contributions.items(), key=lambda p: (-p[1], p[0]))[:20])
    return (
        scores,
        evidence,
        {
            "k1": k1,
            "b": b,
            "token_pattern": TOKEN_PATTERN,
            "query_terms": "unique",
            "stop_words": None,
        },
    )


if __name__ == "__main__":
    from jobmatch.cli import main

    raise SystemExit(main(["run"] + sys.argv[1:] + ["--methods", "bm25"]))
