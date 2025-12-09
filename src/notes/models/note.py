"""Note data model."""

import contextlib
import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class Note(BaseModel):
    """A note with content and metadata."""

    path: str
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate path contains only safe characters."""
        v = v.strip().lstrip("/")
        if not v:
            raise ValueError("Path cannot be empty")
        if ".." in v:
            raise ValueError("Path cannot contain '..'")
        if not re.match(r"^[\w\-/]+$", v):
            raise ValueError(
                "Path can only contain letters, numbers, hyphens, underscores, and slashes"
            )
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate and filter tags to safe characters only."""
        validated = []
        for tag in v:
            tag = tag.strip()
            if tag and re.match(r"^[\w\-]+$", tag):
                validated.append(tag)
        return validated

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate title is not empty and within length limit."""
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        if len(v) > 200:
            raise ValueError("Title cannot exceed 200 characters")
        return v

    def to_markdown(self) -> str:
        """Serialize note to markdown with YAML frontmatter."""
        frontmatter_lines = [
            "---",
            f"title: {self.title}",
            f"created: {self.created_at.isoformat()}",
            f"updated: {self.updated_at.isoformat()}",
        ]
        if self.tags:
            frontmatter_lines.append(f"tags: [{', '.join(self.tags)}]")
        frontmatter_lines.append("---")
        frontmatter_lines.append("")

        return "\n".join(frontmatter_lines) + self.content

    @classmethod
    def from_markdown(cls, path: str, content: str) -> Note:
        """Parse a note from markdown with YAML frontmatter."""
        # Extract frontmatter
        frontmatter_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)

        title = path.split("/")[-1]
        tags: list[str] = []
        created_at = datetime.now()
        updated_at = datetime.now()
        body = content

        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            body = content[frontmatter_match.end() :]

            # Parse frontmatter fields
            for line in frontmatter.split("\n"):
                if line.startswith("title:"):
                    title = line[6:].strip()
                elif line.startswith("tags:"):
                    tags_str = line[5:].strip()
                    # Parse [tag1, tag2] format
                    if tags_str.startswith("[") and tags_str.endswith("]"):
                        tags = [t.strip() for t in tags_str[1:-1].split(",") if t.strip()]
                elif line.startswith("created:"):
                    with contextlib.suppress(ValueError):
                        created_at = datetime.fromisoformat(line[8:].strip())
                elif line.startswith("updated:"):
                    with contextlib.suppress(ValueError):
                        updated_at = datetime.fromisoformat(line[8:].strip())

        return cls(
            path=path,
            title=title,
            content=body,
            tags=tags,
            created_at=created_at,
            updated_at=updated_at,
        )
