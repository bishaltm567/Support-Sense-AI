"""Privacy-minimizing operational logging helpers."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

logger = logging.getLogger("supportsense")


def log_interaction(question: str, *, abstained: bool, citations: list[str], started_at: float) -> None:
    """Log a one-way question identifier and operational metadata, never raw text."""
    record: dict[str, Any] = {
        "event": "answer",
        "question_sha256_prefix": hashlib.sha256(question.encode("utf-8")).hexdigest()[:12],
        "abstained": abstained,
        "citation_count": len(citations),
        "latency_ms": round((time.perf_counter() - started_at) * 1000, 2),
    }
    logger.info(json.dumps(record, sort_keys=True))
