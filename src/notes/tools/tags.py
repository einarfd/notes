"""Tag management tools for MCP."""

from notes.config import get_config
from notes.server import mcp
from notes.storage import FilesystemStorage


def _get_storage() -> FilesystemStorage:
    config = get_config()
    config.ensure_dirs()
    return FilesystemStorage(config.notes_dir)


@mcp.tool()
def list_tags() -> str:
    """List all tags used across notes.

    Returns:
        A formatted list of all tags with their note counts
    """
    storage = _get_storage()
    paths = storage.list_all()

    tag_counts: dict[str, int] = {}
    for path in paths:
        note = storage.load(path)
        if note:
            for tag in note.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

    if not tag_counts:
        return "No tags found."

    sorted_tags = sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))

    output = ["Tags:", ""]
    for tag, count in sorted_tags:
        output.append(f"  - {tag} ({count} note{'s' if count != 1 else ''})")

    return "\n".join(output)


@mcp.tool()
def find_by_tag(tag: str) -> str:
    """Find all notes with a specific tag.

    Args:
        tag: The tag to search for

    Returns:
        A list of notes with the specified tag
    """
    storage = _get_storage()
    paths = storage.list_all()

    matching_notes = []
    for path in paths:
        note = storage.load(path)
        if note and tag in note.tags:
            matching_notes.append(note)

    if not matching_notes:
        return f"No notes found with tag '{tag}'"

    output = [f"Notes tagged '{tag}':", ""]
    for note in matching_notes:
        output.append(f"  - **{note.title}** ({note.path})")

    return "\n".join(output)
