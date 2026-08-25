from __future__ import annotations

import random

VIOLATION_TYPES = ["coordinate", "unit", "freshness", "confidence", "provenance", "compound"]


def choose_violation(rng: random.Random, severity: str) -> str:
    if severity == "normal":
        return "none"
    return rng.choice(VIOLATION_TYPES)


def initial_attributes(violation_type: str, severity: str) -> dict:
    attrs = {
        "position": {"reference_frame": "ENU", "unit": "meter", "age": 1, "confidence": 0.9, "provenance": "verified"},
        "destination": {"reference_frame": "ENU", "unit": "meter", "age": 1, "confidence": 0.95, "provenance": "verified"},
        "threat": {"reference_frame": "ENU", "unit": "meter", "age": 2, "confidence": 0.82, "provenance": "verified"},
        "weather": {"age": 5, "confidence": 0.82, "provenance": "verified"},
        "terrain": {"reference_frame": "ENU", "unit": "meter", "age": 10, "confidence": 0.9, "provenance": "verified"},
        "comm": {"reference_frame": "ENU", "age": 2, "confidence": 0.84, "provenance": "verified"},
    }
    if severity == "normal":
        return attrs
    value = {
        "coordinate": ("position", {"reference_frame": "WGS84"}),
        "unit": ("position", {"unit": "kilometer"}),
        "freshness": ("position", {"age": 11 if severity == "minor" else 25}),
        "confidence": ("position", {"confidence": 0.78 if severity == "minor" else 0.55}),
        "provenance": ("position", {"provenance": "unverified"}),
    }
    if violation_type == "compound":
        mods = [value["coordinate"], value["freshness"], value["confidence"]]
    else:
        mods = [value[violation_type]]
    for key, patch in mods:
        attrs.setdefault(key, {}).update(patch)
    return attrs
