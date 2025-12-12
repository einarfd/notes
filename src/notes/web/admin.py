"""Admin routes for web UI."""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from notes.services import NoteService

router = APIRouter(prefix="/admin", tags=["admin"])

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def _get_service() -> NoteService:
    return NoteService()


@router.get("", response_class=HTMLResponse)
def admin_page(request: Request) -> HTMLResponse:
    """Show admin page."""
    return templates.TemplateResponse(request, "admin.html")


@router.post("/rebuild", response_class=HTMLResponse)
def rebuild_indexes(request: Request) -> HTMLResponse:
    """Rebuild all indexes and show result."""
    service = _get_service()
    result = service.rebuild_indexes()
    return templates.TemplateResponse(
        request,
        "admin.html",
        {"result": result},
    )
