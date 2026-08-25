from __future__ import annotations

from src.models.contracts import ExecutionCondition


def condition_deficits(actual: ExecutionCondition, required: ExecutionCondition, now: float = 0.0, binary: bool = False) -> dict[str, float]:
    d: dict[str, float] = {}
    for field in ["schema_type", "semantic_type", "unit", "reference_frame", "provenance"]:
        req = getattr(required, field)
        if req is not None:
            violated = getattr(actual, field) != req
            d[field] = 1.0 if violated else 0.0
    if required.max_age is not None:
        age = now - actual.timestamp if actual.timestamp is not None else required.max_age + 1
        val = min(1.0, max(0.0, (age - required.max_age) / required.max_age))
        d["freshness"] = 1.0 if binary and val > 0 else val
    if required.min_confidence is not None:
        conf = actual.confidence if actual.confidence is not None else 0.0
        val = min(1.0, max(0.0, (required.min_confidence - conf) / required.min_confidence))
        d["confidence"] = 1.0 if binary and val > 0 else val
    return d


def violation_score(deficits: dict[str, float], weights: dict[str, float] | None = None) -> float:
    if not deficits:
        return 0.0
    if not weights:
        return max(0.0, min(1.0, sum(deficits.values()) / len(deficits)))
    total = sum(weights.get(k, 0.0) for k in deficits) or 1.0
    return max(0.0, min(1.0, sum(weights.get(k, 0.0) * v for k, v in deficits.items()) / total))
