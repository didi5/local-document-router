from __future__ import annotations

from pathlib import Path


def convert_pdf(source: Path) -> str:
    try:
        from markitdown import MarkItDown
    except ImportError as exc:
        raise RuntimeError("MarkItDown is missing. Run: python -m pip install 'markitdown[pdf]'") from exc
    converter = MarkItDown(enable_plugins=False)
    if hasattr(converter, "convert_local"):
        result = converter.convert_local(source)
    else:
        result = converter.convert(source)
    markdown = getattr(result, "markdown", None) or getattr(result, "text_content", None)
    if not markdown:
        raise RuntimeError(f"No text extracted from {source.name}")
    return str(markdown)
