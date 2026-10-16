"""Small local lexical retriever; intentionally not represented as semantic search."""

from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from config import DATA_DIR, SETTINGS
from src.security import is_safe_document, role_can_access

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "can", "do", "for", "from",
    "how", "i", "in", "is", "it", "my", "of", "on", "or", "our", "the",
    "to", "we", "what", "when", "where", "which", "with", "you", "your",
}


@dataclass(frozen=True)
class Document:
    """A single authorized knowledge-base record."""

    document_id: str
    category: str
    question: str
    answer: str
    source_document: str
    access_classification: str
    last_updated: str

    @property
    def searchable_text(self) -> str:
        return f"{self.category} {self.question} {self.answer}"


@dataclass(frozen=True)
class SearchHit:
    """A retrieved record and its normalized lexical relevance score."""

    document: Document
    score: float


def load_documents(
    csv_path: Path | str = DATA_DIR / "customer_faq.csv",
    policies_path: Path | str = DATA_DIR / "sample_policies.json",
) -> list[Document]:
    """Load FAQ CSV and optional policy JSON, validating required fields."""
    required = {
        "document_id", "category", "question", "answer", "source_document",
        "access_classification", "last_updated",
    }
    documents: list[Document] = []
    with Path(csv_path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not required.issubset(reader.fieldnames or ()):
            raise ValueError(f"FAQ dataset is missing columns: {sorted(required - set(reader.fieldnames or ())) }")
        for row in reader:
            if not all((row.get(field) or "").strip() for field in required):
                continue
            documents.append(Document(**{field: row[field].strip() for field in required}))
    policy_file = Path(policies_path)
    if policy_file.exists():
        records = json.loads(policy_file.read_text(encoding="utf-8"))
        for row in records:
            if required.issubset(row) and all(str(row[field]).strip() for field in required):
                documents.append(Document(**{field: str(row[field]).strip() for field in required}))
    unique: dict[str, Document] = {}
    for document in documents:
        unique[document.document_id] = document
    return list(unique.values())


def search(
    query: str,
    documents: Iterable[Document] | None = None,
    *,
    role: str = SETTINGS.default_user_role,
    limit: int = SETTINGS.max_results,
) -> list[SearchHit]:
    """Return authorized, non-injected records ranked by TF-IDF-like overlap."""
    candidates = [
        doc for doc in (documents if documents is not None else load_documents())
        if role_can_access(doc.access_classification, role)
        and is_safe_document(f"{doc.question} {doc.answer}")
    ]
    terms = _tokens(query)
    if not terms or not candidates:
        return []
    document_terms = [_tokens(doc.searchable_text) for doc in candidates]
    document_frequency = Counter(term for term in set(term for terms_ in document_terms for term in terms_))
    query_weights = {
        term: math.log(1 + len(candidates) / (1 + document_frequency.get(term, 0)))
        for term in set(terms)
    }
    denominator = sum(query_weights.values())
    if denominator == 0:
        return []
    matched_query_weight = sum(
        weight for term, weight in query_weights.items()
        if any(term in document_terms_ for document_terms_ in document_terms)
    )
    query_coverage = matched_query_weight / denominator
    hits: list[SearchHit] = []
    for document, tokens in zip(candidates, document_terms):
        counts = Counter(tokens)
        weighted_match = sum(
            weight * (1 + math.log(counts[term])) for term, weight in query_weights.items()
            if counts[term]
        )
        score = (weighted_match / denominator) * query_coverage
        if score >= SETTINGS.retrieval_threshold:
            hits.append(SearchHit(document, min(score, 1.0)))
    return sorted(hits, key=lambda hit: (-hit.score, hit.document.document_id))[:limit]


def _tokens(text: str) -> list[str]:
    return [token for token in _TOKEN_RE.findall(text.lower()) if token not in _STOP_WORDS]
