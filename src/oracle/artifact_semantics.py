from __future__ import annotations

from src.models.contracts import ExecutionCondition


def required_fields() -> list[str]:
    return ["schema_type", "semantic_type", "unit", "reference_frame", "provenance"]


def compare_condition(actual: ExecutionCondition, required: ExecutionCondition, now: float = 0.0) -> dict[str, float]:
    deficits: dict[str, float] = {}
    for field in required_fields():
        req = getattr(required, field)
        if req is not None:
            deficits[field] = 0.0 if getattr(actual, field) == req else 1.0
    if required.max_age is not None:
        age = now - actual.timestamp if actual.timestamp is not None else required.max_age + 1
        deficits["freshness"] = min(1.0, max(0.0, (age - required.max_age) / required.max_age))
    if required.min_confidence is not None:
        conf = actual.confidence if actual.confidence is not None else 0.0
        deficits["confidence"] = min(1.0, max(0.0, (required.min_confidence - conf) / required.min_confidence))
    return deficits


def any_violation(deficits: dict[str, float]) -> bool:
    return any(v > 0 for v in deficits.values())
