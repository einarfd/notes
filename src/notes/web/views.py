"""HTML views for the web UI."""

from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from notes.services import NoteService

router = APIRouter(tags=["views"])

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def _get_service() -> NoteService:
    return NoteService()


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


@router.post("/new")
def create_note_form(
    path: str = Form(...),
    title: str = Form(...),
    tags: str = Form(""),
    content: str = Form(""),
) -> RedirectResponse:
    """Handle new note form submission."""
    service = _get_service()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    service.create_note(path=path, title=title, content=content, tags=tag_list)
    return RedirectResponse(url=f"/notes/{path}", status_code=303)


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


@router.post("/notes/{path:path}")
def update_note_form(
    path: str,
    title: str = Form(...),
    tags: str = Form(""),
    content: str = Form(""),
) -> RedirectResponse:
    """Handle edit note form submission."""
    service = _get_service()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    service.update_note(path=path, title=title, content=content, tags=tag_list)
    return RedirectResponse(url=f"/notes/{path}", status_code=303)


@router.post("/notes/{path:path}/delete")
def delete_note_form(path: str) -> RedirectResponse:
    """Handle delete note form submission."""
    service = _get_service()
    service.delete_note(path)
    return RedirectResponse(url="/", status_code=303)


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
