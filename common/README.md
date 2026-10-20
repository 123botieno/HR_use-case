# Shared utilities

Business logic lives inside the numbered tool folders. This folder contains only:

- [io.py](io.py): JSON/CSV reading, artifact writing, and hashes.
- [text.py](text.py): the tokenizer shared by BM25 and TF-IDF.
- [stages.py](stages.py): imports numbered folders using Python's importlib, because hyphens and leading numbers cannot appear in ordinary Python import statements.

The small `jobmatch/` package provides command-line argument parsing and dispatch, including `python -m jobmatch`. It does not contain matching, extraction, validation, monitoring, or orchestration implementations.
