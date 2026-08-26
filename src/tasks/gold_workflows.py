from src.models.workflow import Workflow, WorkflowNode


FAMILY_TOOLS = {
    "F1": [
        ["T01", "T04", "T06", "T19", "T23"],
        ["T01", "T04", "T06", "T11", "T19", "T23"],
        ["T01", "T04", "T06", "T09", "T19", "T23"],
    ],
    "F2": [
        ["T01", "T04", "T07", "T16", "T20", "T23"],
        ["T01", "T04", "T02", "T03", "T07", "T16", "T20", "T23"],
        ["T01", "T04", "T07", "T12", "T16", "T20", "T23"],
    ],
    "F3": [
        ["T01", "T04", "T05", "T21", "T23"],
        ["T01", "T04", "T05", "T14", "T21", "T23"],
        ["T01", "T04", "T06", "T05", "T21", "T23"],
    ],
    "F4": [
        ["T01", "T04", "T08", "T18", "T22", "T23"],
        ["T01", "T04", "T08", "T15", "T18", "T22", "T23"],
        ["T01", "T04", "T08", "T11", "T18", "T22", "T23"],
    ],
    "F5": [
        ["T01", "T04", "T07", "T05", "T17", "T20", "T23"],
        ["T01", "T04", "T07", "T12", "T05", "T17", "T20", "T23"],
        ["T01", "T04", "T07", "T05", "T16", "T20", "T23"],
    ],
    "F6": [
        ["T01", "T04", "T07", "T05", "T17", "T19", "T23", "T24"],
        ["T01", "T04", "T07", "T12", "T05", "T17", "T20", "T23", "T24"],
        ["T01", "T04", "T02", "T03", "T07", "T05", "T17", "T19", "T23", "T24"],
    ],
}

OUTPUT_NAMES = {
    "T01": "position", "T02": "object_position", "T03": "updated_position", "T04": "destination", "T05": "weather", "T06": "terrain", "T07": "threat",
    "T08": "comm", "T09": "data", "T10": "data", "T11": "position", "T12": "threat",
    "T14": "data", "T15": "data", "T16": "threat_map", "T17": "situation", "T18": "comm_assessment",
    "T19": "route", "T20": "route", "T21": "route", "T22": "route", "T23": "validation", "T24": "visualization",
}


def initial_workflow(family: str, variant_index: int = 0) -> Workflow:
    variants = FAMILY_TOOLS[family]
    tools = variants[variant_index % len(variants)]
    artifacts = {"platform_id": "platform_id", "mission_id": "mission_id", "area_id": "area_id", "constraints": "constraints"}
    nodes = []
    for idx, tid in enumerate(tools, 1):
        inputs = {}
        if tid == "T01":
            inputs = {"platform_id": "platform_id"}
        elif tid == "T04":
            inputs = {"mission_id": "mission_id"}
        elif tid in {"T05", "T06", "T07"}:
            inputs = {"area_id": "area_id"}
        elif tid == "T08":
            inputs = {"platform_id": "platform_id"}
        elif tid == "T03":
            inputs = {"object_position": artifacts["object_position"]}
        elif tid == "T16":
            inputs = {"threat": artifacts["threat"], "position": artifacts["position"]}
        elif tid == "T17":
            inputs = {"position": artifacts["position"], "threat": artifacts["threat"], "weather": artifacts["weather"]}
        elif tid == "T18":
            inputs = {"comm": artifacts["comm"], "position": artifacts["position"]}
        elif tid == "T09":
            inputs = {"data": artifacts["position"]}
        elif tid == "T10":
            inputs = {"data": artifacts["position"]}
        elif tid == "T11":
            inputs = {"position": artifacts["position"]}
        elif tid == "T12":
            inputs = {"threat": artifacts["threat"]}
        elif tid == "T14":
            inputs = {"data": artifacts.get("weather", artifacts["position"])}
        elif tid == "T15":
            inputs = {"data": artifacts.get("comm", artifacts["position"])}
        elif tid == "T19":
            inputs = {"start": artifacts["position"], "destination": artifacts["destination"], "terrain": artifacts.get("terrain", "terrain")}
        elif tid == "T20":
            inputs = {"start": artifacts["position"], "destination": artifacts["destination"], "threat_map": artifacts.get("threat_map", "threat_map")}
        elif tid == "T21":
            inputs = {"start": artifacts["position"], "destination": artifacts["destination"], "weather": artifacts["weather"]}
        elif tid == "T22":
            inputs = {"start": artifacts["position"], "destination": artifacts["destination"], "comm_assessment": artifacts["comm_assessment"]}
        elif tid == "T23":
            inputs = {"route": artifacts["route"], "constraints": "constraints"}
        elif tid == "T24":
            inputs = {"route": artifacts["route"], "situation": artifacts["situation"]}
        out = OUTPUT_NAMES[tid]
        artifact = f"{out}_{tid.lower()}_{idx}" if tid in {"T09", "T10", "T11", "T12", "T14", "T15"} else out
        if tid == "T03":
            artifacts["position"] = artifact
        elif tid in {"T09", "T10", "T11"}:
            artifacts["position"] = artifact
        elif tid == "T12":
            artifacts["threat"] = artifact
        elif tid in {"T14", "T15"}:
            if "weather" in inputs.get("data", ""):
                artifacts["weather"] = artifact
            elif "comm" in inputs.get("data", ""):
                artifacts["comm"] = artifact
            else:
                artifacts["position"] = artifact
        artifacts[out] = artifact
        nodes.append(WorkflowNode(f"n{idx}", tid, inputs, {out: artifact}))
    return Workflow(nodes, goal="visualization" if family == "F6" else "validation")
