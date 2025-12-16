"""Backup and restore functionality for notes."""

import shutil
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ExportResult:
    """Result of an export operation."""

    path: Path
    notes_count: int


@dataclass
class ImportResult:
    """Result of an import operation."""

    imported_count: int
    skipped_count: int
    replaced: bool


def export_notes(notes_dir: Path, output_path: Path | None = None) -> ExportResult:
    """Export all notes to a tar.gz archive.

    Args:
        notes_dir: Directory containing the notes
        output_path: Path for the output archive. If None, generates a timestamped name.

    Returns:
        ExportResult with the archive path and note count
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y-%m-%d")
        output_path = Path(f"botnotes-backup-{timestamp}.tar.gz")

    # Ensure output has .tar.gz extension
    if not str(output_path).endswith(".tar.gz"):
        output_path = Path(f"{output_path}.tar.gz")

    # Get list of markdown files
    md_files = list(notes_dir.rglob("*.md"))
    notes_count = len(md_files)

    # Create archive
    with tarfile.open(output_path, "w:gz") as tar:
        for md_file in md_files:
            # Use relative path within archive
            arcname = md_file.relative_to(notes_dir)
            tar.add(md_file, arcname=arcname)

    return ExportResult(path=output_path.resolve(), notes_count=notes_count)


def clear_notes(notes_dir: Path) -> int:
    """Delete all notes from the notes directory.

    Args:
        notes_dir: Directory containing the notes

    Returns:
        Number of notes deleted
    """
    md_files = list(notes_dir.rglob("*.md"))
    count = len(md_files)

    for md_file in md_files:
        md_file.unlink()

    # Clean up empty directories
    for dir_path in sorted(notes_dir.rglob("*"), reverse=True):
        if dir_path.is_dir() and not any(dir_path.iterdir()):
            dir_path.rmdir()

    return count


def import_notes(
    notes_dir: Path, archive_path: Path, replace: bool = False
) -> ImportResult:
    """Import notes from a tar.gz archive.

    Args:
        notes_dir: Directory to import notes into
        archive_path: Path to the archive file
        replace: If True, clear existing notes before import

    Returns:
        ImportResult with counts of imported and skipped notes

    Raises:
        FileNotFoundError: If archive doesn't exist
        tarfile.ReadError: If archive is invalid
    """
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    imported_count = 0
    skipped_count = 0

    # If replacing, clear the notes directory first
    if replace and notes_dir.exists():
        for md_file in notes_dir.rglob("*.md"):
            md_file.unlink()
        # Clean up empty directories
        for dir_path in sorted(notes_dir.rglob("*"), reverse=True):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                dir_path.rmdir()

    # Extract to temp directory first for validation
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        with tarfile.open(archive_path, "r:gz") as tar:
            # Security: check for path traversal attacks
            for member in tar.getmembers():
                if member.name.startswith("/") or ".." in member.name:
                    raise ValueError(f"Invalid path in archive: {member.name}")
                if not member.name.endswith(".md"):
                    continue  # Skip non-markdown files

            # Extract only markdown files
            tar.extractall(tmp_path, filter="data")

        # Copy markdown files to notes directory
        for md_file in tmp_path.rglob("*.md"):
            rel_path = md_file.relative_to(tmp_path)
            dest_path = notes_dir / rel_path

            if dest_path.exists() and not replace:
                # In merge mode, skip existing files
                skipped_count += 1
            else:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(md_file, dest_path)
                imported_count += 1

    return ImportResult(
        imported_count=imported_count,
        skipped_count=skipped_count,
        replaced=replace,
    )
