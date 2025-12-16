"""Tests for MCP tools."""

from botnotes.models.note import Note


def test_note_to_markdown():
    """Test note serialization to markdown."""
    note = Note(
        path="test",
        title="Test Note",
        content="Hello world",
        tags=["a", "b"],
    )

    md = note.to_markdown()
    assert "title: Test Note" in md
    assert "tags: [a, b]" in md
    assert "Hello world" in md


def test_note_from_markdown():
    """Test note parsing from markdown."""
    content = """---
title: Parsed Note
tags: [tag1, tag2]
created: 2024-01-01T00:00:00
updated: 2024-01-02T00:00:00
---
This is the body content."""

    note = Note.from_markdown("test/path", content)

    assert note.path == "test/path"
    assert note.title == "Parsed Note"
    assert note.tags == ["tag1", "tag2"]
    assert note.content == "This is the body content."


def test_note_from_markdown_no_frontmatter():
    """Test parsing markdown without frontmatter."""
    content = "Just plain content."

    note = Note.from_markdown("plain", content)

    assert note.path == "plain"
    assert note.title == "plain"  # Uses path as title
    assert note.content == "Just plain content."
