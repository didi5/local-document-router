# Local Document Router

A privacy-first agent workflow that converts incoming PDFs to Markdown and routes both files into the right project folder. It runs locally, discovers new project folders automatically, and uses explicit safety thresholds before moving documents.

## Why this project exists

Research papers, pitch decks, grant documents, and project notes often arrive in one download folder. Manual conversion and filing wastes time and creates inconsistent archives. Local Document Router turns one inbox into a reproducible workflow:

```text
PDF inbox → conversion agent → routing agent → safety check → project folders + audit log
```

The default path uses no paid API. MarkItDown performs conversion. Deterministic project rules perform classification. Ollama support is optional for uncertain documents.

## Features

- Converts local PDFs to Markdown with Microsoft MarkItDown
- Discovers every project directory under `01_Projekte`
- Combines filename, document content, project names, and configurable keywords
- Sends uncertain or ambiguous documents to `99_Unklar`
- Never overwrites an existing file
- Keeps the original PDF beside the routed Markdown output
- Writes a JSON Lines audit log with confidence, reason, destination, and SHA-256
- Runs once, continuously, or automatically through a macOS LaunchAgent
- Keeps private documents, local configuration, and outputs out of Git

## Architecture

The workflow uses three bounded agents:

1. Conversion agent: transforms a local PDF into Markdown.
2. Routing agent: scores only project folders found at runtime.
3. Safety agent: accepts high-confidence decisions and quarantines every other result.

Ollama acts as an optional local classifier when deterministic rules find no safe match. Its response is validated against the discovered project allowlist.

## Quick start on macOS

Python 3.11 to 3.13 is recommended.

```bash
git clone https://github.com/YOUR_USERNAME/local-document-router.git
cd local-document-router
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
cp config.example.toml config.toml
cp routing_rules.example.toml routing_rules.toml
```

Edit `config.toml` so the paths point to your local workspace. Edit `routing_rules.toml` to add project-specific terms.

Create project folders such as:

```text
AI_OS/
├── 00_Inbox/
├── 01_Projekte/
│   ├── SolAegis/
│   ├── Overgrid/
    ├── Health Tech platform/
│   └── Any_New_Project/
└── 99_Unklar/
```

Check the setup:

```bash
document-router --config config.toml doctor
```

Process every current inbox PDF:

```bash
document-router --config config.toml once
```

Watch continuously in the foreground:

```bash
document-router --config config.toml watch
```

## Automatic macOS startup

Install the per-user LaunchAgent:

```bash
document-router --config config.toml install-agent
launchctl bootstrap gui/$(id -u) "$HOME/Library/LaunchAgents/com.dilemkaya.document-router.plist"
```

Stop it:

```bash
launchctl bootout gui/$(id -u) "$HOME/Library/LaunchAgents/com.dilemkaya.document-router.plist"
```

After installation, dropping a PDF into `00_Inbox` triggers processing without a terminal command.

## Optional local AI with Ollama

Install Ollama separately, pull a small model suited to your Mac, then update `config.toml`:

```toml
[ollama]
enabled = true
url = "http://127.0.0.1:11434"
model = "qwen2.5:3b"
```

The workflow remains functional when Ollama is disabled. If Ollama fails, the document goes to review rather than being routed on a guess.

## Tests

The tests use synthetic documents and never call an external service:

```bash
python -m unittest discover -s tests -v
```

## Privacy and safety

- Only local PDF files from the configured inbox are processed.
- Document text is treated as data, not as executable instructions.
- Project destinations come from actual local directories.
- Real papers, health data, API keys, local configuration, and generated outputs are excluded by `.gitignore`.
- Keep patient-level or confidential institutional data outside GitHub.

## Scope

Version 0.1 routes PDF and Markdown files. Research extraction, evidence tables, and source verification belong in separate opt-in modules so basic document handling stays predictable and auditable.

## License

MIT
