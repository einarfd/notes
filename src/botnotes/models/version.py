"""Version history data models."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class NoteVersion:
    """Represents a single version of a note in history."""

    commit_sha: str
    timestamp: datetime
    author: str
    message: str


@dataclass
class NoteDiff:
    """Represents a diff between two versions of a note."""

    path: str
    from_version: str
    to_version: str
    diff_text: str
    additions: int
    deletions: int
