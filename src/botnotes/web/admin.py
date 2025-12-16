"""Admin routes for web UI."""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from botnotes.backup import clear_notes, export_notes, import_notes
from botnotes.config import get_config
from botnotes.services import NoteService
from botnotes.web.auth import verify_credentials

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(verify_credentials)])

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


@router.get("/export")
def export_backup() -> FileResponse:
    """Export all notes as a tar.gz archive."""
    config = get_config()
    timestamp = datetime.now().strftime("%Y-%m-%d")
    filename = f"botnotes-backup-{timestamp}.tar.gz"

    # Create temp file for export
    tmp_dir = tempfile.mkdtemp()
    output_path = Path(tmp_dir) / filename
    export_notes(config.notes_dir, output_path)

    return FileResponse(
        path=output_path,
        filename=filename,
        media_type="application/gzip",
    )


@router.post("/import", response_class=HTMLResponse)
async def import_backup(
    request: Request,
    file: Annotated[UploadFile, File()],
    replace: Annotated[bool, Form()] = False,
) -> HTMLResponse:
    """Import notes from a tar.gz archive."""
    config = get_config()

    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        import_result = import_notes(config.notes_dir, tmp_path, replace=replace)

        # Rebuild indexes
        service = _get_service()
        rebuild_result = service.rebuild_indexes()

        return templates.TemplateResponse(
            request,
            "admin.html",
            {
                "import_result": import_result,
                "rebuild_result": rebuild_result,
            },
        )
    finally:
        tmp_path.unlink(missing_ok=True)


@router.post("/clear", response_class=HTMLResponse)
def clear_all_notes(request: Request) -> HTMLResponse:
    """Delete all notes."""
    config = get_config()
    count = clear_notes(config.notes_dir)

    # Rebuild indexes (they'll be empty)
    service = _get_service()
    service.rebuild_indexes()

    return templates.TemplateResponse(
        request,
        "admin.html",
        {"clear_result": count},
    )
