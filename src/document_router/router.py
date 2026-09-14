from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
from typing import Callable

from .classifier import Decision, classify_ollama, classify_rules, load_rules, project_names
from .config import Config
from .converter import convert_pdf


@dataclass(frozen=True)
class RouteResult:
    source: str
    status: str
    project: str | None
    confidence: float
    reason: str
    pdf_destination: str | None
    markdown_destination: str | None
    sha256: str


def _unique(path: Path) -> Path:
    if not path.exists():
        return path
    counter = 2
    while True:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _log(config: Config, result: RouteResult) -> None:
    payload = {"timestamp": datetime.now(timezone.utc).isoformat(), **asdict(result)}
    with config.log_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def route_pdf(source: Path, config: Config, converter: Callable[[Path], str] = convert_pdf) -> RouteResult:
    source = source.expanduser().resolve()
    if source.suffix.lower() != ".pdf" or not source.is_file():
        raise ValueError("Source must be an existing PDF")
    markdown = converter(source)
    projects = project_names(config.projects_root)
    decision = classify_rules(source.name, markdown, projects, load_rules(config.rules_file))
    if decision.project is None and config.ollama.enabled and projects:
        try:
            decision = classify_ollama(source.name, markdown, projects, config.ollama)
        except Exception as exc:
            decision = Decision(None, decision.confidence, f"local model unavailable: {exc}", decision.candidates)

    approved = decision.project is not None and decision.confidence >= config.auto_route_threshold
    if approved:
        target_dir = config.projects_root / decision.project
        status = "routed"
    else:
        target_dir = config.unclear_dir
        status = "review_required"
    target_dir.mkdir(parents=True, exist_ok=True)
    pdf_target = _unique(target_dir / source.name)
    md_target = _unique(target_dir / f"{source.stem}.md")
    shutil.move(str(source), str(pdf_target))
    md_target.write_text(markdown, encoding="utf-8")
    result = RouteResult(
        source=str(source), status=status, project=decision.project if approved else None,
        confidence=decision.confidence, reason=decision.reason,
        pdf_destination=str(pdf_target), markdown_destination=str(md_target), sha256=_digest(pdf_target),
    )
    _log(config, result)
    return result
