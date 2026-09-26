"""Small, shared heuristics for recognizing identifier columns."""

import re


def is_identifier_column(column_name: str) -> bool:
    """Match ID/Code/No/Number as name tokens, not arbitrary substrings."""
    separated = re.sub(r"([a-z])([A-Z])", r"\1_\2", column_name)
    tokens = re.split(r"[^A-Za-z0-9]+", separated.lower())
    return any(token in {"id", "code", "number", "no"} for token in tokens)
