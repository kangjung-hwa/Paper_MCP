from src.evaluation.metrics import ci95, mean, std


def descriptive(rows, field):
    xs = [float(r[field]) for r in rows]
    return {"mean": mean(xs), "std": std(xs), "ci95": ci95(xs), "n": len(xs)}
