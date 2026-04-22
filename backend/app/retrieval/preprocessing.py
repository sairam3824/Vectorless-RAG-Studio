from __future__ import annotations

import math
import re


TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-']+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "with",
}


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text) if token.lower() not in STOPWORDS]


def normalize_query(text: str) -> str:
    return " ".join(tokenize(text))


def keyword_overlap_score(query: str, text: str) -> tuple[float, list[str]]:
    query_terms = set(tokenize(query))
    if not query_terms:
        return 0.0, []
    text_terms = set(tokenize(text))
    overlap = sorted(query_terms & text_terms)
    return len(overlap) / len(query_terms), overlap


def title_match_score(query: str, title: str) -> float:
    query_terms = set(tokenize(query))
    title_terms = set(tokenize(title))
    if not query_terms or not title_terms:
        return 0.0
    return len(query_terms & title_terms) / len(query_terms)


def exact_phrase_score(query: str, text: str, title: str = "") -> float:
    compact_query = " ".join(tokenize(query))
    if not compact_query:
        return 0.0
    haystacks = [" ".join(tokenize(title)), " ".join(tokenize(text))]
    if compact_query in haystacks[0]:
        return 1.0
    if compact_query in haystacks[1]:
        return 0.7
    return 0.0


def jaccard_similarity(left: str, right: str) -> float:
    left_terms = set(tokenize(left))
    right_terms = set(tokenize(right))
    if not left_terms or not right_terms:
        return 0.0
    intersection = len(left_terms & right_terms)
    union = len(left_terms | right_terms)
    return intersection / union if union else 0.0


def cosine_norm(values: list[float]) -> list[float]:
    if not values:
        return []
    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0:
        return [0.0 for _ in values]
    return [value / norm for value in values]
