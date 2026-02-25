from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse


def _load_index_html() -> str:
    ui_dir = Path(__file__).resolve().parent / "ui"
    index_path = ui_dir / "index.html"
    return index_path.read_text(encoding="utf-8")


def mount_ui(app: FastAPI) -> None:
    """
    Mount a simple UI page at `/`.
    The UI calls `/recommendations/pipeline` to run User → Filter → LLM → Response.
    """

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def index() -> HTMLResponse:
        return HTMLResponse(_load_index_html())

