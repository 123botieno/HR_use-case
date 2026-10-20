# ruff: noqa: E402
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from common.text import TOKEN_PATTERN


def tfidf(query, documents):
    vectorizer = TfidfVectorizer(
        lowercase=True, token_pattern=TOKEN_PATTERN, ngram_range=(1, 1), norm="l2"
    )
    matrix = vectorizer.fit_transform(documents)
    query_vector = vectorizer.transform([query])
    scores = cosine_similarity(query_vector, matrix).ravel().tolist()
    features = vectorizer.get_feature_names_out()
    evidence = []
    for row in matrix:
        products = row.multiply(query_vector).tocoo()
        pairs = [
            (str(features[col]), float(value))
            for col, value in zip(products.col, products.data)
        ]
        evidence.append(sorted(pairs, key=lambda p: (-p[1], p[0]))[:20])
    return (
        scores,
        evidence,
        {
            "token_pattern": TOKEN_PATTERN,
            "ngram_range": [1, 1],
            "stop_words": None,
            "norm": "l2",
            "query_zero_vector": query_vector.nnz == 0,
            "vocabulary": vectorizer.vocabulary_,
            "idf": np.asarray(vectorizer.idf_).tolist(),
        },
    )


if __name__ == "__main__":
    from jobmatch.cli import main

    raise SystemExit(main(["run"] + sys.argv[1:] + ["--methods", "tfidf"]))
