from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class OllamaConfig:
    enabled: bool = False
    url: str = "http://127.0.0.1:11434"
    model: str = "qwen2.5:3b"


@dataclass(frozen=True)
class Config:
    inbox: Path
    projects_root: Path
    unclear_dir: Path
    log_file: Path
    rules_file: Path
    auto_route_threshold: float = 0.85
    review_threshold: float = 0.60
    poll_seconds: int = 3
    stable_checks: int = 2
    ollama: OllamaConfig = OllamaConfig()


def _path(value: str, base: Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base / path).resolve()


def load_config(path: Path) -> Config:
    path = path.expanduser().resolve()
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    base = path.parent
    ollama = raw.get("ollama", {})
    return Config(
        inbox=_path(raw["inbox"], base),
        projects_root=_path(raw["projects_root"], base),
        unclear_dir=_path(raw["unclear_dir"], base),
        log_file=_path(raw["log_file"], base),
        rules_file=_path(raw.get("rules_file", "routing_rules.toml"), base),
        auto_route_threshold=float(raw.get("auto_route_threshold", 0.85)),
        review_threshold=float(raw.get("review_threshold", 0.60)),
        poll_seconds=int(raw.get("poll_seconds", 3)),
        stable_checks=int(raw.get("stable_checks", 2)),
        ollama=OllamaConfig(
            enabled=bool(ollama.get("enabled", False)),
            url=str(ollama.get("url", "http://127.0.0.1:11434")).rstrip("/"),
            model=str(ollama.get("model", "qwen2.5:3b")),
        ),
    )


def ensure_directories(config: Config) -> None:
    for path in (config.inbox, config.projects_root, config.unclear_dir, config.log_file.parent):
        path.mkdir(parents=True, exist_ok=True)
