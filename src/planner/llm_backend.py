from __future__ import annotations

import json
import os
import urllib.request


def available() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_COMPATIBLE_API_KEY"))


def complete(prompt: str, model_name: str, temperature: float = 0.0, base_url: str | None = None) -> str | None:
    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_COMPATIBLE_API_KEY")
    if not key:
        return None
    url = (base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/") + "/chat/completions"
    payload = {
        "model": model_name,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    return data["choices"][0]["message"]["content"]
