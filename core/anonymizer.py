import re
from typing import Any

# Simple PII patterns
PII_PATTERNS = {
    "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "PHONE": r"\b(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "SSN": r"\b\d{3}[-.]?\d{2}[-.]?\d{4}\b",
    "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b"
}

class ContentAnonymizer:
    def __init__(self, active: bool = True):
        self.active = active
        self.patterns = {name: re.compile(pat) for name, pat in PII_PATTERNS.items()}

    def anonymize(self, text: str) -> str:
        if not self.active or not text:
            return text
            
        anonymized = text
        for name, pattern in self.patterns.items():
            anonymized = pattern.sub(f"[REDACTED_{name}]", anonymized)
            
        return anonymized
