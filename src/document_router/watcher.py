from __future__ import annotations

from pathlib import Path
import time

from .config import Config
from .router import RouteResult, route_pdf


def is_stable(path: Path, checks: int, delay: float = 0.5) -> bool:
    previous = -1
    for _ in range(max(1, checks)):
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            return False
        if size == previous:
            return True
        previous = size
        time.sleep(delay)
    return checks <= 1


def process_once(config: Config) -> list[RouteResult]:
    results = []
    for path in sorted(config.inbox.glob("*.pdf")):
        if is_stable(path, config.stable_checks):
            results.append(route_pdf(path, config))
    return results


def watch(config: Config) -> None:
    while True:
        process_once(config)
        time.sleep(config.poll_seconds)
