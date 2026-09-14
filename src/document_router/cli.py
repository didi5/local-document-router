from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

from .config import ensure_directories, load_config
from .watcher import process_once, watch


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="document-router", description="Local document routing agents")
    parser.add_argument("--config", type=Path, default=Path("config.toml"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="check local setup")
    sub.add_parser("once", help="process current inbox PDFs")
    sub.add_parser("watch", help="watch inbox continuously")
    sub.add_parser("install-agent", help="install a macOS LaunchAgent")
    return parser


def _install_agent(config_path: Path, config) -> Path:
    label = "com.dilemkaya.document-router"
    target = Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"
    target.parent.mkdir(parents=True, exist_ok=True)
    program = shutil.which("document-router")
    if program:
        arguments = f"<string>{program}</string><string>--config</string><string>{config_path}</string><string>watch</string>"
    else:
        arguments = f"<string>{sys.executable}</string><string>-m</string><string>document_router.cli</string><string>--config</string><string>{config_path}</string><string>watch</string>"
    plist = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>{label}</string>
<key>ProgramArguments</key><array>{arguments}</array>
<key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
<key>StandardOutPath</key><string>{config.log_file.parent / "launch-agent.log"}</string>
<key>StandardErrorPath</key><string>{config.log_file.parent / "launch-agent-error.log"}</string>
</dict></plist>'''
    target.write_text(plist, encoding="utf-8")
    return target


def main() -> None:
    args = _parser().parse_args()
    config_path = args.config.expanduser().resolve()
    config = load_config(config_path)
    ensure_directories(config)
    if args.command == "doctor":
        try:
            import markitdown  # noqa: F401
            markitdown_status = "ok"
        except ImportError:
            markitdown_status = "missing"
        print(json.dumps({"python": sys.version.split()[0], "markitdown": markitdown_status,
                          "inbox": str(config.inbox), "projects_root": str(config.projects_root)}, indent=2))
    elif args.command == "once":
        for result in process_once(config):
            print(json.dumps(result.__dict__, ensure_ascii=False))
    elif args.command == "watch":
        watch(config)
    elif args.command == "install-agent":
        print(_install_agent(config_path, config))


if __name__ == "__main__":
    main()
