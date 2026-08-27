from pathlib import Path

from src.baselines import direct_tool_planning, mirror_inspired, tool_mvr_inspired
from src.mcp.registry import ToolRegistry
from src.tasks.generator import generate_tasks


BASELINE_FILES = [
    Path("src/baselines/direct_tool_planning.py"),
    Path("src/baselines/mirror_inspired.py"),
    Path("src/baselines/tool_mvr_inspired.py"),
]


def test_external_baselines_do_not_import_oracle_or_proposed_risk():
    banned = [
        "src.oracle",
        "GT_success",
        "GT_operational_valid",
        "src.orchestration.risk",
        "src.orchestration.proposed",
    ]
    for path in BASELINE_FILES:
        text = path.read_text()
        assert not any(term in text for term in banned), path


def test_external_baselines_are_not_identical_for_all_tasks():
    registry = ToolRegistry()
    found_difference = False
    for task in generate_tasks(42):
        direct, *_ = direct_tool_planning.plan(task, registry)
        mirror, _, _, mirror_meta = mirror_inspired.plan(task, registry)
        toolmvr, _, _, toolmvr_meta = tool_mvr_inspired.plan(task, registry)
        signatures = {str(direct.to_dict()), str(mirror.to_dict()), str(toolmvr.to_dict())}
        if len(signatures) > 1 or mirror_meta["correction_count"] or toolmvr_meta["correction_count"]:
            found_difference = True
            break
    assert found_difference


def test_reflection_baselines_have_non_degenerate_corrections():
    registry = ToolRegistry()
    mirror_counts = []
    toolmvr_counts = []
    for task in generate_tasks(42):
        _, _, _, mirror_meta = mirror_inspired.plan(task, registry)
        _, _, _, toolmvr_meta = tool_mvr_inspired.plan(task, registry)
        mirror_counts.append(mirror_meta["correction_count"])
        toolmvr_counts.append(toolmvr_meta["correction_count"])
    assert any(c > 0 for c in mirror_counts)
    assert any(c > 0 for c in toolmvr_counts)
    assert any(c == 0 for c in mirror_counts)
    assert any(c == 0 for c in toolmvr_counts)
