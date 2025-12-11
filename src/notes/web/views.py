"""HTML views for the web UI."""

from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from notes.services import NoteService

router = APIRouter(tags=["views"])

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def _get_service() -> NoteService:
    return NoteService()


def _build_breadcrumbs(path: str) -> list[dict[str, str]]:
    """Build breadcrumb navigation from path."""
    if not path:
        return []
    parts = path.split("/")
    breadcrumbs = []
    for i, part in enumerate(parts):
        breadcrumbs.append({
            "name": part,
            "path": "/".join(parts[: i + 1]),
        })
    return breadcrumbs


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """Show all notes."""
    service = _get_service()
    paths = service.list_notes()

    notes = []
    for path in paths:
        note = service.read_note(path)
        if note:
            notes.append(note)

    return templates.TemplateResponse(
        request=request,
        name="notes_list.html",
        context={"notes": notes},
    )


@router.get("/search-results", response_class=HTMLResponse)
def search_results(request: Request, q: str = "") -> HTMLResponse:
    """Search results partial for htmx."""
    service = _get_service()

    if not q:
        paths = service.list_notes()
        notes = [service.read_note(p) for p in paths]
        notes = [n for n in notes if n]
    else:
        results = service.search_notes(q)
        notes = [service.read_note(r["path"]) for r in results]
        notes = [n for n in notes if n]

    return templates.TemplateResponse(
        request=request,
        name="search_results.html",
        context={"notes": notes},
    )


@router.get("/new", response_class=HTMLResponse)
def new_note_form(request: Request) -> HTMLResponse:
    """Show new note form."""
    return templates.TemplateResponse(
        request=request,
        name="note_new.html",
        context={},
    )


@router.post("/new", response_model=None)
def create_note_form(
    request: Request,
    path: str = Form(...),
    title: str = Form(...),
    tags: str = Form(""),
    content: str = Form(""),
) -> RedirectResponse | HTMLResponse:
    """Handle new note form submission."""
    service = _get_service()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    try:
        service.create_note(path=path, title=title, content=content, tags=tag_list)
    except (ValidationError, ValueError) as e:
        return templates.TemplateResponse(
            request=request,
            name="note_new.html",
            context={
                "error": str(e),
                "path": path,
                "title": title,
                "tags": tags,
                "content": content,
            },
            status_code=400,
        )
    return RedirectResponse(url=f"/notes/{path}", status_code=303)


# NOTE: Specific routes (/edit, /delete) must come BEFORE the greedy {path:path} routes
# because {path:path} will match "foo/edit" as a path otherwise.


@router.get("/notes/{path:path}/edit", response_class=HTMLResponse, response_model=None)
def edit_note_form(request: Request, path: str) -> HTMLResponse | RedirectResponse:
    """Show edit note form."""
    service = _get_service()
    note = service.read_note(path)

    if note is None:
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="note_detail.html",
        context={"note": note, "editing": True},
    )


@router.post("/notes/{path:path}/delete")
def delete_note_form(path: str) -> RedirectResponse:
    """Handle delete note form submission."""
    service = _get_service()
    service.delete_note(path)
    return RedirectResponse(url="/", status_code=303)


@router.get("/notes/{path:path}", response_class=HTMLResponse)
def view_note(request: Request, path: str) -> HTMLResponse:
    """View a note."""
    service = _get_service()
    note = service.read_note(path)

    if note is None:
        return templates.TemplateResponse(
            request=request,
            name="base.html",
            context={"content": f"Note not found: {path}"},
            status_code=404,
        )

    return templates.TemplateResponse(
        request=request,
        name="note_detail.html",
        context={"note": note, "editing": False},
    )


@router.post("/notes/{path:path}", response_model=None)
def update_note_form(
    request: Request,
    path: str,
    title: str = Form(...),
    tags: str = Form(""),
    content: str = Form(""),
) -> RedirectResponse | HTMLResponse:
    """Handle edit note form submission."""
    service = _get_service()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    try:
        service.update_note(path=path, title=title, content=content, tags=tag_list)
    except (ValidationError, ValueError) as e:
        # Create a mock note object for re-displaying the form
        from datetime import datetime

        # Use raw values to avoid re-triggering validation
        mock_note = type("MockNote", (), {
            "path": path,
            "title": title,
            "content": content,
            "tags": tag_list,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        })()
        return templates.TemplateResponse(
            request=request,
            name="note_detail.html",
            context={"note": mock_note, "editing": True, "error": str(e)},
            status_code=400,
        )
    return RedirectResponse(url=f"/notes/{path}", status_code=303)


@router.get("/tags", response_class=HTMLResponse)
def list_tags_view(request: Request) -> HTMLResponse:
    """Show all tags."""
    service = _get_service()
    tag_counts = service.list_tags()
    sorted_tags = sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))

    return templates.TemplateResponse(
        request=request,
        name="tags_list.html",
        context={"tags": sorted_tags},
    )


@router.get("/tags/{tag}", response_class=HTMLResponse)
def view_tag(request: Request, tag: str) -> HTMLResponse:
    """Show notes with a specific tag."""
    service = _get_service()
    notes = service.find_by_tag(tag)

    return templates.TemplateResponse(
        request=request,
        name="notes_list.html",
        context={"notes": notes},
    )


@router.get("/folder", response_class=HTMLResponse)
def view_top_level_folder(request: Request) -> HTMLResponse:
    """Show top-level notes only."""
    service = _get_service()
    paths = service.list_notes_in_folder("")

    notes = []
    for path in paths:
        note = service.read_note(path)
        if note:
            notes.append(note)

    return templates.TemplateResponse(
        request=request,
        name="folder_view.html",
        context={
            "notes": notes,
            "folder": "",
            "breadcrumbs": [],
        },
    )


@router.get("/folder/{path:path}", response_class=HTMLResponse)
def view_folder(request: Request, path: str) -> HTMLResponse:
    """Show notes in a folder."""
    service = _get_service()
    paths = service.list_notes_in_folder(path)

    notes = []
    for note_path in paths:
        note = service.read_note(note_path)
        if note:
            notes.append(note)

    return templates.TemplateResponse(
        request=request,
        name="folder_view.html",
        context={
            "notes": notes,
            "folder": path,
            "breadcrumbs": _build_breadcrumbs(path),
        },
    )
