from __future__ import annotations

from src.models.contracts import ToolSpec
from src.tools.base import BaseTool, c


def _tool(tool_id, name, category, inputs, outputs, oracle=None, latency=100, jitter=20, agent=False):
    return ToolSpec(tool_id, name, name, inputs, outputs, oracle or inputs, category, latency, jitter, agent)


def build_tool_specs() -> dict[str, ToolSpec]:
    pos_pub = c(semantic_type="Position")
    pos_enu_m = c(semantic_type="Position", reference_frame="ENU", unit="meter", max_age=10, min_confidence=0.80, provenance="verified")
    fresh_pos = c(semantic_type="Position", reference_frame="ENU", unit="meter", timestamp=0, confidence=0.9, provenance="verified")
    specs = [
        _tool("T01", "GetOwnPosition", "information", {"platform_id": c(schema_type="str")}, {"position": fresh_pos}, latency=80, jitter=30),
        _tool("T02", "DetectObject", "information", {"image": c(schema_type="image")}, {"object_position": c(semantic_type="ObjectPosition", reference_frame="WGS84", unit="meter", confidence=0.72, provenance="unverified")}, latency=130, jitter=20),
        _tool("T03", "TrackObject", "information", {"object_position": c(semantic_type="ObjectPosition")}, {"updated_position": c(semantic_type="Position", reference_frame="ENU", unit="meter", timestamp=0, confidence=0.82, provenance="verified")}, latency=110, jitter=30),
        _tool("T04", "GetDestination", "information", {"mission_id": c(schema_type="str")}, {"destination": c(semantic_type="Position", reference_frame="ENU", unit="meter", timestamp=0, confidence=0.95, provenance="verified")}, latency=70, jitter=20),
        _tool("T05", "GetWeather", "information", {"area_id": c(schema_type="str")}, {"weather": c(semantic_type="Weather", timestamp=0, confidence=0.85, provenance="verified")}, latency=120, jitter=30),
        _tool("T06", "GetTerrain", "information", {"area_id": c(schema_type="str")}, {"terrain": c(semantic_type="TerrainMap", reference_frame="ENU", unit="meter", confidence=0.9, provenance="verified")}, latency=140, jitter=20),
        _tool("T07", "GetThreatInfo", "information", {"area_id": c(schema_type="str")}, {"threat": c(semantic_type="ThreatInfo", reference_frame="ENU", timestamp=0, confidence=0.78, provenance="unverified")}, latency=120, jitter=20),
        _tool("T08", "GetCommunicationStatus", "information", {"platform_id": c(schema_type="str")}, {"comm": c(semantic_type="CommStatus", reference_frame="ENU", timestamp=0, confidence=0.82, provenance="verified")}, latency=80, jitter=20),
        _tool("T09", "CoordinateTransform", "conversion", {"data": c(semantic_type="SpatialData")}, {"data": c(reference_frame="ENU")}, oracle={"data": c()}, latency=25, jitter=15),
        _tool("T10", "UnitConversion", "conversion", {"data": c()}, {"data": c(unit="meter")}, oracle={"data": c()}, latency=20, jitter=10),
        _tool("T11", "RefreshPosition", "refresh", {"position": c(semantic_type="Position")}, {"position": fresh_pos}, oracle={"position": pos_pub}, latency=130, jitter=50),
        _tool("T12", "RefreshThreatInfo", "refresh", {"threat": c(semantic_type="ThreatInfo")}, {"threat": c(semantic_type="ThreatInfo", reference_frame="ENU", timestamp=0, confidence=0.86, provenance="verified")}, latency=150, jitter=50),
        _tool("T13", "SensorFusion", "enhancement", {"primary": c(), "secondary": c()}, {"fused": c(confidence=0.9, provenance="verified")}, oracle={"primary": c(), "secondary": c()}, latency=500, jitter=200),
        _tool("T14", "ConfidenceEnhancement", "enhancement", {"data": c()}, {"data": c(confidence=0.88)}, oracle={"data": c()}, latency=220, jitter=80),
        _tool("T15", "ValidateSource", "enhancement", {"data": c()}, {"data": c(provenance="verified")}, oracle={"data": c()}, latency=180, jitter=70),
        _tool("T16", "ThreatAnalysisAgent", "agent", {"threat": c(semantic_type="ThreatInfo"), "position": pos_pub}, {"threat_map": c(semantic_type="ThreatMap", reference_frame="ENU", timestamp=0, confidence=0.82, provenance="verified")}, oracle={"threat": c(semantic_type="ThreatInfo", reference_frame="ENU", max_age=5, min_confidence=0.75), "position": pos_enu_m}, latency=700, jitter=250, agent=True),
        _tool("T17", "SituationAnalysisAgent", "agent", {"position": pos_pub, "threat": c(semantic_type="ThreatInfo"), "weather": c(semantic_type="Weather")}, {"situation": c(semantic_type="Situation", reference_frame="ENU", timestamp=0, confidence=0.82, provenance="verified")}, oracle={"position": pos_enu_m, "threat": c(semantic_type="ThreatInfo", reference_frame="ENU", max_age=8, min_confidence=0.75), "weather": c(semantic_type="Weather", max_age=30, min_confidence=0.75)}, latency=850, jitter=150, agent=True),
        _tool("T18", "CommunicationAnalysisAgent", "agent", {"comm": c(semantic_type="CommStatus"), "position": pos_pub}, {"comm_assessment": c(semantic_type="CommAssessment", reference_frame="ENU", timestamp=0, confidence=0.84, provenance="verified")}, oracle={"comm": c(semantic_type="CommStatus", reference_frame="ENU", max_age=10, min_confidence=0.75), "position": pos_enu_m}, latency=650, jitter=200, agent=True),
        _tool("T19", "RoutePlanning", "planning", {"start": pos_pub, "destination": pos_pub, "terrain": c(semantic_type="TerrainMap")}, {"route": c(semantic_type="Route", reference_frame="ENU", unit="meter", confidence=0.84, provenance="verified")}, oracle={"start": pos_enu_m, "destination": c(semantic_type="Position", reference_frame="ENU", unit="meter"), "terrain": c(semantic_type="TerrainMap", reference_frame="ENU", unit="meter")}, latency=260, jitter=100),
        _tool("T20", "ThreatAwareRoutePlanning", "planning", {"start": pos_pub, "destination": pos_pub, "threat_map": c(semantic_type="ThreatMap")}, {"route": c(semantic_type="Route", reference_frame="ENU", unit="meter", confidence=0.88, provenance="verified")}, oracle={"start": pos_enu_m, "destination": c(semantic_type="Position", reference_frame="ENU", unit="meter"), "threat_map": c(semantic_type="ThreatMap", reference_frame="ENU", max_age=5, min_confidence=0.80, provenance="verified")}, latency=330, jitter=70),
        _tool("T21", "WeatherAwareRoutePlanning", "planning", {"start": pos_pub, "destination": pos_pub, "weather": c(semantic_type="Weather")}, {"route": c(semantic_type="Route", reference_frame="ENU", unit="meter", confidence=0.84, provenance="verified")}, oracle={"start": pos_enu_m, "destination": c(semantic_type="Position", reference_frame="ENU", unit="meter"), "weather": c(semantic_type="Weather", max_age=30, min_confidence=0.75)}, latency=280, jitter=80),
        _tool("T22", "CommunicationAwareRoutePlanning", "planning", {"start": pos_pub, "destination": pos_pub, "comm_assessment": c(semantic_type="CommAssessment")}, {"route": c(semantic_type="Route", reference_frame="ENU", unit="meter", confidence=0.85, provenance="verified")}, oracle={"start": pos_enu_m, "destination": c(semantic_type="Position", reference_frame="ENU", unit="meter"), "comm_assessment": c(semantic_type="CommAssessment", reference_frame="ENU", max_age=10, min_confidence=0.80)}, latency=300, jitter=70),
        _tool("T23", "RouteValidation", "validation", {"route": c(semantic_type="Route"), "constraints": c(schema_type="Constraints")}, {"validation": c(semantic_type="ValidationResult", confidence=0.95, provenance="verified")}, oracle={"route": c(semantic_type="Route", reference_frame="ENU", unit="meter", min_confidence=0.80), "constraints": c(schema_type="Constraints")}, latency=90, jitter=30),
        _tool("T24", "ResultVisualization", "visualization", {"route": c(semantic_type="Route"), "situation": c(semantic_type="Situation")}, {"visualization": c(semantic_type="Visualization")}, oracle={"route": c(semantic_type="Route"), "situation": c(semantic_type="Situation")}, latency=120, jitter=40),
        _tool("T25", "FastCoordinateTransform", "conversion", {"data": c()}, {"data": c(reference_frame="ENU", confidence=0.78)}, oracle={"data": c()}, latency=12, jitter=8),
        _tool("T26", "PreciseCoordinateTransform", "conversion", {"data": c()}, {"data": c(reference_frame="ENU", confidence=0.94, provenance="verified")}, oracle={"data": c()}, latency=60, jitter=20),
        _tool("T27", "FastThreatRefresh", "refresh", {"threat": c(semantic_type="ThreatInfo")}, {"threat": c(semantic_type="ThreatInfo", reference_frame="ENU", timestamp=0, confidence=0.79, provenance="verified")}, latency=80, jitter=30),
        _tool("T28", "SensorBasedThreatRefresh", "refresh", {"threat": c(semantic_type="ThreatInfo")}, {"threat": c(semantic_type="ThreatInfo", reference_frame="ENU", timestamp=0, confidence=0.91, provenance="verified")}, latency=280, jitter=90),
    ]
    return {s.tool_id: s for s in specs}


class ToolRegistry:
    def __init__(self, specs: dict[str, ToolSpec] | None = None):
        self.specs = specs or build_tool_specs()
        self.tools = {k: BaseTool(v) for k, v in self.specs.items()}

    def public_specs(self, full_metadata: bool = True) -> list[dict]:
        return [s.public_spec(full_metadata) for s in self.specs.values()]

    def get(self, tool_id: str) -> ToolSpec:
        return self.specs[tool_id]
