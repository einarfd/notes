"""REST API routes for notes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ValidationError

from botnotes.services import NoteService
from botnotes.web.auth import verify_credentials

router = APIRouter(prefix="/api", tags=["api"], dependencies=[Depends(verify_credentials)])


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


class VersionInfo(BaseModel):
    """Version history entry."""

    version: str
    timestamp: str
    author: str
    message: str


class NoteVersionResponse(BaseModel):
    """Response body for a note at a specific version."""

    path: str
    title: str
    content: str
    tags: list[str]
    version: str
    created_at: str
    updated_at: str


class DiffResponse(BaseModel):
    """Response body for a diff between versions."""

    path: str
    from_version: str
    to_version: str
    diff: str
    additions: int
    deletions: int


class FolderContents(BaseModel):
    """Contents of a folder."""

    notes: list[str]
    subfolders: list[str]
    has_index: bool = False


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
        # Cast to satisfy mypy - we know the types
        notes = contents["notes"]
        subfolders = contents["subfolders"]
        has_index = contents["has_index"]
        assert isinstance(notes, list)
        assert isinstance(subfolders, list)
        assert isinstance(has_index, bool)
        return FolderContents(notes=notes, subfolders=subfolders, has_index=has_index)
    # No folder filter - return all notes, no subfolders
    return FolderContents(notes=service.list_notes(), subfolders=[])


# History API endpoints - must be before the generic {path:path} routes


@router.get("/notes/{path:path}/history")
def get_note_history(path: str, limit: int = 50) -> list[VersionInfo]:
    """Get version history for a note.

    Args:
        path: The note path
        limit: Maximum number of versions to return (default 50, max 100)
    """
    service = _get_service()
    limit = min(limit, 100)
    versions = service.get_note_history(path, limit=limit)

    return [
        VersionInfo(
            version=v.commit_sha,
            timestamp=v.timestamp.isoformat(),
            author=v.author,
            message=v.message,
        )
        for v in versions
    ]


@router.get("/notes/{path:path}/versions/{version}")
def get_note_version(path: str, version: str) -> NoteVersionResponse:
    """Get a specific version of a note.

    Args:
        path: The note path
        version: The commit SHA (short or full)
    """
    service = _get_service()
    note = service.get_note_version(path, version)

    if note is None:
        raise HTTPException(
            status_code=404, detail=f"Version '{version}' not found for note '{path}'"
        )

    return NoteVersionResponse(
        path=note.path,
        title=note.title,
        content=note.content,
        tags=note.tags,
        version=version,
        created_at=note.created_at.isoformat(),
        updated_at=note.updated_at.isoformat(),
    )


@router.get("/notes/{path:path}/diff")
def diff_note_versions(
    path: str, from_version: str, to_version: str
) -> DiffResponse:
    """Show diff between two versions of a note.

    Args:
        path: The note path
        from_version: Starting version (commit SHA)
        to_version: Ending version (commit SHA)
    """
    service = _get_service()
    diff = service.diff_note_versions(path, from_version, to_version)

    return DiffResponse(
        path=diff.path,
        from_version=diff.from_version,
        to_version=diff.to_version,
        diff=diff.diff_text,
        additions=diff.additions,
        deletions=diff.deletions,
    )


@router.post("/notes/{path:path}/restore/{version}")
def restore_note_version(
    path: str, version: str, username: str = Depends(verify_credentials)
) -> NoteResponse:
    """Restore a note to a previous version.

    This creates a new commit with the old content, preserving all history.

    Args:
        path: The note path
        version: The version SHA to restore
    """
    service = _get_service()
    # Use authenticated username as author, or "web" if auth is disabled
    author = username or "web"
    note = service.restore_note_version(path, version, author=author)

    if note is None:
        raise HTTPException(
            status_code=404, detail=f"Version '{version}' not found for note '{path}'"
        )

    return NoteResponse(
        path=note.path,
        title=note.title,
        content=note.content,
        tags=note.tags,
        created_at=note.created_at.isoformat(),
        updated_at=note.updated_at.isoformat(),
    )


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
def create_note(
    body: NoteCreate, username: str = Depends(verify_credentials)
) -> NoteResponse:
    """Create a new note."""
    service = _get_service()
    author = username or "web"
    try:
        note = service.create_note(
            path=body.path,
            title=body.title,
            content=body.content,
            tags=body.tags,
            author=author,
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
def update_note(
    path: str, body: NoteUpdate, username: str = Depends(verify_credentials)
) -> NoteResponse:
    """Update an existing note."""
    service = _get_service()
    author = username or "web"
    try:
        result = service.update_note(
            path=path,
            title=body.title,
            content=body.content,
            tags=body.tags,
            author=author,
        )
    except (ValidationError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from None

    if result is None:
        raise HTTPException(status_code=404, detail=f"Note not found: {path}")

    note = result.note
    return NoteResponse(
        path=note.path,
        title=note.title,
        content=note.content,
        tags=note.tags,
        created_at=note.created_at.isoformat(),
        updated_at=note.updated_at.isoformat(),
    )


@router.delete("/notes/{path:path}", status_code=204)
def delete_note(path: str, username: str = Depends(verify_credentials)) -> None:
    """Delete a note."""
    service = _get_service()
    author = username or "web"
    result = service.delete_note(path, author=author)

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
