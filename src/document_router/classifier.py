from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import tomllib
from urllib.request import Request, urlopen

from .config import OllamaConfig


@dataclass(frozen=True)
class Decision:
    project: str | None
    confidence: float
    reason: str
    candidates: tuple[str, ...] = ()


def project_names(projects_root: Path) -> list[str]:
    if not projects_root.exists():
        return []
    return sorted(path.name for path in projects_root.iterdir() if path.is_dir() and not path.name.startswith("."))


def load_rules(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    return {
        project: [str(item).lower() for item in values.get("keywords", [])]
        for project, values in raw.get("projects", {}).items()
    }


def _tokens(value: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9äöüß]+", value.lower()) if len(token) > 2]


def classify_rules(filename: str, text: str, projects: list[str], rules: dict[str, list[str]]) -> Decision:
    haystack = f"{filename}\n{text[:50000]}".lower()
    scores: dict[str, float] = {}
    reasons: dict[str, list[str]] = {}
    for project in projects:
        keywords = list(rules.get(project, [])) + _tokens(project)
        unique = sorted(set(keyword for keyword in keywords if keyword))
        hits = [keyword for keyword in unique if keyword in haystack]
        if hits:
            filename_hits = sum(keyword in filename.lower() for keyword in hits)
            score = min(0.98, 0.48 + 0.12 * len(hits) + 0.12 * filename_hits)
            scores[project] = score
            reasons[project] = hits
    if not scores:
        return Decision(None, 0.0, "no matching project signals")
    ranked = sorted(scores, key=scores.get, reverse=True)
    best = ranked[0]
    if len(ranked) > 1 and scores[best] - scores[ranked[1]] < 0.12:
        return Decision(None, scores[best], "ambiguous rule match", tuple(ranked[:3]))
    return Decision(best, scores[best], "matched: " + ", ".join(reasons[best][:6]), tuple(ranked[:3]))


def classify_ollama(filename: str, text: str, projects: list[str], config: OllamaConfig) -> Decision:
    prompt = (
        "Classify this local document into exactly one allowed project or null. "
        "Return JSON only with project, confidence from 0 to 1, and reason. "
        f"Allowed projects: {json.dumps(projects)}\nFilename: {filename}\nText:\n{text[:12000]}"
    )
    payload = json.dumps({"model": config.model, "prompt": prompt, "stream": False, "format": "json"}).encode()
    request = Request(config.url + "/api/generate", data=payload, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=60) as response:
        outer = json.loads(response.read())
    result = json.loads(outer["response"])
    project = result.get("project")
    if project not in projects:
        project = None
    confidence = max(0.0, min(1.0, float(result.get("confidence", 0))))
    return Decision(project, confidence, "Ollama: " + str(result.get("reason", "no reason")))
