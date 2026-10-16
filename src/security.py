"""Input controls and trust-boundary checks for the demo assistant."""

from __future__ import annotations

import re
from dataclasses import dataclass

from config import SETTINGS

_INJECTION_PATTERNS = (
    r"\bignore\b.{0,50}\b(previous|prior|above|all)\b.{0,30}\b(instructions?|rules?)\b",
    r"\b(reveal|print|show|repeat|disclose)\b.{0,40}\b(system prompt|hidden instructions?|secret prompt)\b",
    r"\bact as\b.{0,40}\b(system|developer|admin)\b",
    r"\b(jailbreak|bypass|override)\b.{0,40}\b(safety|instructions?|policy|access)\b",
)
_SENSITIVE_REQUEST_PATTERNS = (
    r"\b(other customers?|another customer(?:'s|’s)?|another user's?|all customers?)\b.{0,60}\b(data|records?|email|address|orders?)\b",
    r"\b(customer|user)\s+(password|credit card|social security|private email)\b",
    r"\b(show|give|tell|list|export)\b.{0,50}\b(personal data|private customer|customer records?)\b",
    r"\b(use|call|invoke|run|execute)\b.{0,50}\b(admin|unauthorized|external)?\s*(tool|action|command)\b",
    r"\b(cancel|delete|change|refund|ship|purchase|transfer)\b.{0,80}\b(another customer|someone else's|other user's|admin tool)\b",
)
_UNTRUSTED_DOCUMENT_PATTERNS = (
    r"\bignore (all )?(previous|prior) instructions\b",
    r"\breveal (the )?(system prompt|confidential|secret)\b",
    r"\bexfiltrate\b",
    r"\bdeveloper message\b",
)


@dataclass(frozen=True)
class InputDecision:
    """A validated user request or a safe refusal reason."""

    accepted: bool
    reason: str = ""


def validate_question(question: str) -> InputDecision:
    """Reject malformed, oversized, injected, or privacy-invasive questions."""
    if not isinstance(question, str) or not question.strip():
        return InputDecision(False, "Please enter a question.")
    if len(question) > SETTINGS.max_question_length:
        return InputDecision(False, "That question is too long. Please shorten it.")
    if any(ord(char) < 32 and char not in "\t\n\r" for char in question):
        return InputDecision(False, "The question contains unsupported control characters.")
    if _matches(question, _INJECTION_PATTERNS):
        return InputDecision(False, "I can’t reveal internal instructions or change my safety rules. I can help with questions covered by the support knowledge base.")
    if _matches(question, _SENSITIVE_REQUEST_PATTERNS):
        return InputDecision(False, "I can’t provide private or other customers’ information. I can only answer using authorized support information.")
    return InputDecision(True)


def is_safe_document(text: str) -> bool:
    """Exclude documents that contain obvious instruction-injection payloads."""
    return not _matches(text, _UNTRUSTED_DOCUMENT_PATTERNS)


def role_can_access(classification: str, role: str) -> bool:
    """Enforce access at retrieval time; public users only receive public records."""
    permitted = {
        "public": {"public"},
        "support": {"public", "internal"},
        "admin": {"public", "internal", "confidential"},
    }
    return classification.lower() in permitted.get(role.lower(), set())


def _matches(value: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, value, re.IGNORECASE | re.DOTALL) for pattern in patterns)
