"""REST API routes for notes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError

from notes.services import NoteService

router = APIRouter(prefix="/api", tags=["api"])


class NoteCreate(BaseModel):
    """Request body for creating a note."""

    path: str
    title: str
    content: str
    tags: list[str] = []


class NoteUpdate(BaseModel):
    """Request body for updating a note."""

    title: str | None = None
    content: str | None = None
    tags: list[str] | None = None


class NoteResponse(BaseModel):
    """Response body for a note."""

    path: str
    title: str
    content: str
    tags: list[str]
    created_at: str
    updated_at: str


class SearchResult(BaseModel):
    """A single search result."""

    path: str
    title: str
    score: str


class FolderContents(BaseModel):
    """Contents of a folder."""

    notes: list[str]
    subfolders: list[str]


def _get_service() -> NoteService:
    return NoteService()


@router.get("/notes")
def list_notes(folder: str | None = None) -> FolderContents:
    """List note paths.

    Args:
        folder: Optional folder to filter by. If not provided, returns all notes
                with no subfolder info. Empty string lists top-level only.
    """
    service = _get_service()
    if folder is not None:
        contents = service.list_notes_in_folder(folder)
        return FolderContents(notes=contents["notes"], subfolders=contents["subfolders"])
    # No folder filter - return all notes, no subfolders
    return FolderContents(notes=service.list_notes(), subfolders=[])


@router.get("/notes/{path:path}")
def get_note(path: str) -> NoteResponse:
    """Get a note by path."""
    service = _get_service()
    note = service.read_note(path)

    if note is None:
        raise HTTPException(status_code=404, detail=f"Note not found: {path}")

    return NoteResponse(
        path=note.path,
        title=note.title,
        content=note.content,
        tags=note.tags,
        created_at=note.created_at.isoformat(),
        updated_at=note.updated_at.isoformat(),
    )


@router.post("/notes", status_code=201)
def create_note(body: NoteCreate) -> NoteResponse:
    """Create a new note."""
    service = _get_service()
    try:
        note = service.create_note(
            path=body.path,
            title=body.title,
            content=body.content,
            tags=body.tags,
        )
    except (ValidationError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from None

    return NoteResponse(
        path=note.path,
        title=note.title,
        content=note.content,
        tags=note.tags,
        created_at=note.created_at.isoformat(),
        updated_at=note.updated_at.isoformat(),
    )


@router.put("/notes/{path:path}")
def update_note(path: str, body: NoteUpdate) -> NoteResponse:
    """Update an existing note."""
    service = _get_service()
    try:
        note = service.update_note(
            path=path,
            title=body.title,
            content=body.content,
            tags=body.tags,
        )
    except (ValidationError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from None

    if note is None:
        raise HTTPException(status_code=404, detail=f"Note not found: {path}")

    return NoteResponse(
        path=note.path,
        title=note.title,
        content=note.content,
        tags=note.tags,
        created_at=note.created_at.isoformat(),
        updated_at=note.updated_at.isoformat(),
    )


@router.delete("/notes/{path:path}", status_code=204)
def delete_note(path: str) -> None:
    """Delete a note."""
    service = _get_service()
    result = service.delete_note(path)

    if not result.deleted:
        raise HTTPException(status_code=404, detail=f"Note not found: {path}")


@router.get("/search")
def search_notes(q: str, limit: int = 10) -> list[SearchResult]:
    """Search for notes."""
    service = _get_service()
    # Cap limit to prevent excessive results
    limit = min(limit, 100)
    results = service.search_notes(q, limit=limit)

    return [
        SearchResult(path=r["path"], title=r["title"], score=r["score"]) for r in results
    ]


@router.get("/tags")
def list_tags() -> dict[str, int]:
    """List all tags with counts."""
    service = _get_service()
    return service.list_tags()


@router.get("/tags/{tag}")
def find_by_tag(tag: str) -> list[NoteResponse]:
    """Find notes by tag."""
    service = _get_service()
    notes = service.find_by_tag(tag)

    return [
        NoteResponse(
            path=note.path,
            title=note.title,
            content=note.content,
            tags=note.tags,
            created_at=note.created_at.isoformat(),
            updated_at=note.updated_at.isoformat(),
        )
        for note in notes
    ]
