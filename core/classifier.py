from typing import Optional, Dict


class BaseClassifier:
    """Interface for pluggable ML/heuristic classifiers."""

    def predict(self, text: str) -> Optional[Dict[str, object]]:
        """Return a dict like {"is_injection": bool, "confidence": float} or None."""
        raise NotImplementedError()


class BasicKeywordClassifier(BaseClassifier):
    """A tiny keyword-based classifier useful as a demo or fallback.

    It is not meant to be production-grade; operators should replace it with a trained model.
    """

    KEYWORDS = ["jailbreak", "ignore previous", "send to", "password", "exfiltrate"]

    def predict(self, text: str) -> Optional[Dict[str, object]]:
        t = text.lower()
        hits = [k for k in self.KEYWORDS if k in t]
        if not hits:
            return None
        # crude confidence based on number of hits
        conf = min(0.9, 0.3 + 0.2 * len(hits))
        return {"is_injection": True, "confidence": conf, "explanation": f"Keywords: {', '.join(hits)}"}
