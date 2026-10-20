"""Shared lexical tokenizer."""

import re

TOKEN_PATTERN = r"(?u)\b\w\w+\b"


def tokenize(text):
    return re.findall(TOKEN_PATTERN, text.lower())
