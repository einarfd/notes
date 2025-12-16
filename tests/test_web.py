"""Tests for web API routes."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from botnotes.config import Config
from botnotes.services import NoteService
from botnotes.web.app import app


@pytest.fixture
def client(config: Config):
    """Create a test client with mocked service."""

    def make_test_service() -> NoteService:
        return NoteService(config)

    with (
        patch("botnotes.web.routes._get_service", make_test_service),
        patch("botnotes.web.views._get_service", make_test_service),
        patch("botnotes.web.admin._get_service", make_test_service),
        patch("botnotes.web.admin.get_config", return_value=config),
        patch("botnotes.web.auth.get_config", return_value=config),
    ):
        yield TestClient(app)


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check(self, client: TestClient):
        """Test health check returns ok."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestNotesAPI:
    """Tests for notes CRUD API."""

    def test_list_notes_empty(self, client: TestClient):
        """Test listing notes when none exist."""
        response = client.get("/api/notes")

        assert response.status_code == 200
        assert response.json() == {"notes": [], "subfolders": []}

    def test_create_note(self, client: TestClient):
        """Test creating a note."""
        response = client.post(
            "/api/notes",
            json={
                "path": "test/note",
                "title": "Test Note",
                "content": "Hello world",
                "tags": ["test"],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["path"] == "test/note"
        assert data["title"] == "Test Note"
        assert data["content"] == "Hello world"
        assert data["tags"] == ["test"]

    def test_get_note(self, client: TestClient):
        """Test getting a note."""
        # Create first
        client.post(
            "/api/notes",
            json={"path": "readable", "title": "Readable", "content": "Content"},
        )

        response = client.get("/api/notes/readable")

        assert response.status_code == 200
        assert response.json()["title"] == "Readable"

    def test_get_note_not_found(self, client: TestClient):
        """Test getting a nonexistent note."""
        response = client.get("/api/notes/nonexistent")

        assert response.status_code == 404

    def test_update_note(self, client: TestClient):
        """Test updating a note."""
        client.post(
            "/api/notes",
            json={"path": "updatable", "title": "Original", "content": "Content"},
        )

        response = client.put(
            "/api/notes/updatable",
            json={"title": "Updated"},
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Updated"

    def test_update_note_not_found(self, client: TestClient):
        """Test updating a nonexistent note."""
        response = client.put(
            "/api/notes/nonexistent",
            json={"title": "New"},
        )

        assert response.status_code == 404

    def test_delete_note(self, client: TestClient):
        """Test deleting a note."""
        client.post(
            "/api/notes",
            json={"path": "deletable", "title": "Delete Me", "content": "Bye"},
        )

        response = client.delete("/api/notes/deletable")

        assert response.status_code == 204

        # Verify it's gone
        response = client.get("/api/notes/deletable")
        assert response.status_code == 404

    def test_delete_note_not_found(self, client: TestClient):
        """Test deleting a nonexistent note."""
        response = client.delete("/api/notes/nonexistent")

        assert response.status_code == 404

    def test_list_notes(self, client: TestClient):
        """Test listing notes."""
        client.post("/api/notes", json={"path": "note1", "title": "Note 1", "content": ""})
        client.post("/api/notes", json={"path": "note2", "title": "Note 2", "content": ""})

        response = client.get("/api/notes")

        assert response.status_code == 200
        data = response.json()
        assert "note1" in data["notes"]
        assert "note2" in data["notes"]
        assert data["subfolders"] == []

    def test_list_notes_in_folder(self, client: TestClient):
        """Test listing notes and subfolders in a specific folder."""
        client.post("/api/notes", json={"path": "top", "title": "Top", "content": ""})
        client.post(
            "/api/notes", json={"path": "projects/proj1", "title": "Proj 1", "content": ""}
        )
        client.post(
            "/api/notes", json={"path": "projects/proj2", "title": "Proj 2", "content": ""}
        )
        client.post(
            "/api/notes", json={"path": "projects/sub/note", "title": "Sub", "content": ""}
        )
        client.post("/api/notes", json={"path": "other/note", "title": "Other", "content": ""})

        response = client.get("/api/notes?folder=projects")

        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == ["projects/proj1", "projects/proj2"]
        assert data["subfolders"] == ["projects/sub"]

    def test_list_notes_top_level(self, client: TestClient):
        """Test listing top-level notes and subfolders."""
        client.post("/api/notes", json={"path": "top1", "title": "Top 1", "content": ""})
        client.post("/api/notes", json={"path": "top2", "title": "Top 2", "content": ""})
        client.post(
            "/api/notes", json={"path": "folder/nested", "title": "Nested", "content": ""}
        )

        response = client.get("/api/notes?folder=")

        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == ["top1", "top2"]
        assert data["subfolders"] == ["folder"]

    def test_list_notes_in_folder_empty(self, client: TestClient):
        """Test listing from a folder with no contents."""
        client.post("/api/notes", json={"path": "elsewhere/note", "title": "Note", "content": ""})

        response = client.get("/api/notes?folder=nonexistent")

        assert response.status_code == 200
        assert response.json() == {"notes": [], "subfolders": []}


class TestSearchAPI:
    """Tests for search API."""

    def test_search_notes(self, client: TestClient):
        """Test searching notes."""
        client.post(
            "/api/notes",
            json={"path": "python", "title": "Python Guide", "content": "Learn Python"},
        )
        client.post(
            "/api/notes",
            json={"path": "rust", "title": "Rust Guide", "content": "Learn Rust"},
        )

        response = client.get("/api/search?q=Python")

        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["title"] == "Python Guide"

    def test_search_no_results(self, client: TestClient):
        """Test search with no results."""
        client.post("/api/notes", json={"path": "test", "title": "Test", "content": ""})

        response = client.get("/api/search?q=nonexistent")

        assert response.status_code == 200
        assert response.json() == []


class TestTagsAPI:
    """Tests for tags API."""

    def test_list_tags(self, client: TestClient):
        """Test listing tags."""
        client.post(
            "/api/notes",
            json={"path": "note1", "title": "Note 1", "content": "", "tags": ["python", "guide"]},
        )
        client.post(
            "/api/notes",
            json={"path": "note2", "title": "Note 2", "content": "", "tags": ["python"]},
        )

        response = client.get("/api/tags")

        assert response.status_code == 200
        tags = response.json()
        assert tags["python"] == 2
        assert tags["guide"] == 1

    def test_list_tags_empty(self, client: TestClient):
        """Test listing tags when none exist."""
        response = client.get("/api/tags")

        assert response.status_code == 200
        assert response.json() == {}

    def test_find_by_tag(self, client: TestClient):
        """Test finding notes by tag."""
        client.post(
            "/api/notes",
            json={"path": "note1", "title": "Python 1", "content": "", "tags": ["python"]},
        )
        client.post(
            "/api/notes",
            json={"path": "note2", "title": "Python 2", "content": "", "tags": ["python"]},
        )
        client.post(
            "/api/notes",
            json={"path": "note3", "title": "Rust", "content": "", "tags": ["rust"]},
        )

        response = client.get("/api/tags/python")

        assert response.status_code == 200
        notes = response.json()
        assert len(notes) == 2
        titles = [n["title"] for n in notes]
        assert "Python 1" in titles
        assert "Python 2" in titles

    def test_find_by_tag_no_results(self, client: TestClient):
        """Test finding notes by nonexistent tag."""
        client.post(
            "/api/notes",
            json={"path": "note1", "title": "Note", "content": "", "tags": ["other"]},
        )

        response = client.get("/api/tags/nonexistent")

        assert response.status_code == 200
        assert response.json() == []


class TestHTMLViews:
    """Tests for HTML view endpoints."""

    def test_index_page(self, client: TestClient):
        """Test the index page returns HTML."""
        response = client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_index_shows_notes(self, client: TestClient):
        """Test index page shows created notes."""
        client.post("/api/notes", json={"path": "mytest", "title": "My Test", "content": ""})

        response = client.get("/")

        assert response.status_code == 200
        assert "My Test" in response.text

    def test_new_note_form(self, client: TestClient):
        """Test the new note form page."""
        response = client.get("/new")

        assert response.status_code == 200
        assert "Create New Note" in response.text

    def test_create_note_via_form(self, client: TestClient):
        """Test creating a note via form submission."""
        response = client.post(
            "/new",
            data={"path": "formtest", "title": "Form Test", "tags": "a, b", "content": "Hello"},
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/notes/formtest"

    def test_view_note_page(self, client: TestClient):
        """Test viewing a note page."""
        client.post("/api/notes", json={"path": "viewme", "title": "View Me", "content": "Body"})

        response = client.get("/notes/viewme")

        assert response.status_code == 200
        assert "View Me" in response.text
        assert "Body" in response.text

    def test_view_note_not_found(self, client: TestClient):
        """Test viewing a nonexistent note."""
        response = client.get("/notes/nonexistent")

        assert response.status_code == 404

    def test_edit_note_form(self, client: TestClient):
        """Test the edit note form page."""
        client.post("/api/notes", json={"path": "editable", "title": "Editable", "content": ""})

        response = client.get("/notes/editable/edit")

        assert response.status_code == 200
        assert "Editable" in response.text
        assert 'method="POST"' in response.text

    def test_edit_note_form_not_found(self, client: TestClient):
        """Test edit form for nonexistent note redirects."""
        response = client.get("/notes/nonexistent/edit", follow_redirects=False)

        assert response.status_code == 303
        assert response.headers["location"] == "/"

    def test_update_note_via_form(self, client: TestClient):
        """Test updating a note via form submission."""
        client.post(
            "/api/notes", json={"path": "updateme", "title": "Original", "content": "Old"}
        )

        response = client.post(
            "/notes/updateme",
            data={"new_path": "updateme", "title": "Updated", "tags": "", "content": "New"},
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/notes/updateme"

        # Verify update
        get_response = client.get("/api/notes/updateme")
        assert get_response.json()["title"] == "Updated"

    def test_move_note_via_form(self, client: TestClient):
        """Test moving a note via form submission."""
        client.post(
            "/api/notes", json={"path": "old/path", "title": "Movable", "content": "Content"}
        )

        response = client.post(
            "/notes/old/path",
            data={"new_path": "new/location", "title": "Movable", "tags": "", "content": "Content"},
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/notes/new/location"

        # Verify move
        old_response = client.get("/api/notes/old/path")
        assert old_response.status_code == 404

        new_response = client.get("/api/notes/new/location")
        assert new_response.status_code == 200
        assert new_response.json()["title"] == "Movable"

    def test_delete_note_via_form(self, client: TestClient):
        """Test deleting a note via form submission."""
        client.post("/api/notes", json={"path": "deleteme", "title": "Delete", "content": ""})

        response = client.post("/notes/deleteme/delete", follow_redirects=False)

        assert response.status_code == 303
        assert response.headers["location"] == "/"

        # Verify deletion
        get_response = client.get("/api/notes/deleteme")
        assert get_response.status_code == 404

    def test_tags_page(self, client: TestClient):
        """Test the tags listing page."""
        client.post(
            "/api/notes",
            json={"path": "tagged", "title": "Tagged", "content": "", "tags": ["mytag"]},
        )

        response = client.get("/tags")

        assert response.status_code == 200
        assert "mytag" in response.text

    def test_tag_filter_page(self, client: TestClient):
        """Test filtering notes by tag."""
        client.post(
            "/api/notes",
            json={"path": "py1", "title": "Python 1", "content": "", "tags": ["python"]},
        )
        client.post(
            "/api/notes",
            json={"path": "rs1", "title": "Rust 1", "content": "", "tags": ["rust"]},
        )

        response = client.get("/tags/python")

        assert response.status_code == 200
        assert "Python 1" in response.text
        assert "Rust 1" not in response.text

    def test_search_results_partial(self, client: TestClient):
        """Test the search results htmx partial."""
        client.post(
            "/api/notes",
            json={"path": "searchable", "title": "Searchable", "content": "findme"},
        )

        response = client.get("/search-results?q=findme")

        assert response.status_code == 200
        assert "Searchable" in response.text

    def test_folder_view_top_level(self, client: TestClient):
        """Test viewing top-level notes and subfolders."""
        client.post("/api/notes", json={"path": "top1", "title": "Top 1", "content": ""})
        client.post("/api/notes", json={"path": "top2", "title": "Top 2", "content": ""})
        client.post(
            "/api/notes", json={"path": "myfolder/nested", "title": "Nested", "content": ""}
        )

        response = client.get("/folder")

        assert response.status_code == 200
        assert "Top 1" in response.text
        assert "Top 2" in response.text
        assert "myfolder" in response.text  # Subfolder should appear
        assert "Nested" not in response.text  # But not the nested note title

    def test_folder_view_specific_folder(self, client: TestClient):
        """Test viewing notes and subfolders in a specific folder."""
        client.post(
            "/api/notes", json={"path": "root-note", "title": "Root Note", "content": ""}
        )
        client.post(
            "/api/notes", json={"path": "projects/proj1", "title": "Proj 1", "content": ""}
        )
        client.post(
            "/api/notes", json={"path": "projects/proj2", "title": "Proj 2", "content": ""}
        )
        client.post(
            "/api/notes", json={"path": "projects/sub/deep", "title": "Deep", "content": ""}
        )

        response = client.get("/folder/projects")

        assert response.status_code == 200
        assert "Proj 1" in response.text
        assert "Proj 2" in response.text
        assert "sub" in response.text  # Subfolder should appear
        assert "Root Note" not in response.text

    def test_folder_view_shows_breadcrumbs(self, client: TestClient):
        """Test that folder view shows breadcrumb navigation."""
        client.post(
            "/api/notes",
            json={"path": "projects/web/note", "title": "Web Note", "content": ""},
        )

        response = client.get("/folder/projects/web")

        assert response.status_code == 200
        assert "projects" in response.text
        assert "web" in response.text

    def test_folder_view_only_subfolders(self, client: TestClient):
        """Test viewing folder with only subfolders, no direct notes."""
        client.post(
            "/api/notes", json={"path": "projects/web/note", "title": "Note", "content": ""}
        )

        response = client.get("/folder/projects")

        assert response.status_code == 200
        assert "web" in response.text
        assert "Folders" in response.text

    def test_folder_view_empty_folder(self, client: TestClient):
        """Test viewing an empty folder."""
        client.post("/api/notes", json={"path": "elsewhere/note", "title": "Note", "content": ""})

        response = client.get("/folder/empty")

        assert response.status_code == 200
        assert "No contents in this folder" in response.text


class TestAdminViews:
    """Tests for admin page."""

    def test_admin_page(self, client: TestClient):
        """Test the admin page returns HTML."""
        response = client.get("/admin")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Administration" in response.text
        assert "Rebuild" in response.text

    def test_admin_rebuild_empty(self, client: TestClient):
        """Test rebuilding indexes when no notes exist."""
        response = client.post("/admin/rebuild")

        assert response.status_code == 200
        assert "Rebuild complete" in response.text
        assert "0 notes" in response.text

    def test_admin_rebuild_with_notes(self, client: TestClient):
        """Test rebuilding indexes with notes."""
        client.post("/api/notes", json={"path": "note1", "title": "Note 1", "content": ""})
        client.post("/api/notes", json={"path": "note2", "title": "Note 2", "content": ""})
        client.post("/api/notes", json={"path": "note3", "title": "Note 3", "content": ""})

        response = client.post("/admin/rebuild")

        assert response.status_code == 200
        assert "Rebuild complete" in response.text
        assert "3 notes" in response.text

    def test_admin_link_in_nav(self, client: TestClient):
        """Test that admin link appears in navigation."""
        response = client.get("/")

        assert response.status_code == 200
        assert 'href="/admin"' in response.text

    def test_admin_page_has_backup_section(self, client: TestClient):
        """Test that admin page has backup section."""
        response = client.get("/admin")

        assert response.status_code == 200
        assert "Backup" in response.text
        assert "Download Backup" in response.text
        assert "Import" in response.text

    def test_admin_export(self, client: TestClient):
        """Test exporting notes as tar.gz archive."""
        # Create some notes first
        client.post(
            "/api/notes",
            json={"path": "export1", "title": "Export 1", "content": "Content 1"},
        )
        client.post(
            "/api/notes",
            json={"path": "export2", "title": "Export 2", "content": "Content 2"},
        )

        response = client.get("/admin/export")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/gzip"
        assert "notes-backup-" in response.headers.get("content-disposition", "")
        assert ".tar.gz" in response.headers.get("content-disposition", "")
        # Verify it's actually a gzip file (starts with gzip magic bytes)
        assert response.content[:2] == b'\x1f\x8b'

    def test_admin_import_merge(self, client: TestClient, tmp_path: Path):
        """Test importing notes in merge mode."""
        import tarfile

        # Create a test archive
        archive_path = tmp_path / "test-backup.tar.gz"
        notes_tmp = tmp_path / "notes"
        notes_tmp.mkdir()
        (notes_tmp / "imported1.md").write_text("---\ntitle: Imported 1\n---\nContent 1")
        (notes_tmp / "imported2.md").write_text("---\ntitle: Imported 2\n---\nContent 2")

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(notes_tmp / "imported1.md", arcname="imported1.md")
            tar.add(notes_tmp / "imported2.md", arcname="imported2.md")

        # Upload the archive
        with open(archive_path, "rb") as f:
            response = client.post(
                "/admin/import",
                files={"file": ("backup.tar.gz", f, "application/gzip")},
                data={"replace": "false"},
            )

        assert response.status_code == 200
        assert "Import complete" in response.text
        assert "2 notes" in response.text

        # Verify notes were imported
        note1 = client.get("/api/notes/imported1")
        assert note1.status_code == 200
        assert note1.json()["title"] == "Imported 1"

    def test_admin_import_with_replace(self, client: TestClient, tmp_path: Path):
        """Test importing notes with replace mode."""
        import tarfile

        # Create an existing note
        client.post("/api/notes", json={"path": "existing", "title": "Existing", "content": "Old"})

        # Create a test archive with different note
        archive_path = tmp_path / "test-backup.tar.gz"
        notes_tmp = tmp_path / "notes"
        notes_tmp.mkdir()
        (notes_tmp / "new.md").write_text("---\ntitle: New Note\n---\nNew content")

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(notes_tmp / "new.md", arcname="new.md")

        # Upload with replace=true
        with open(archive_path, "rb") as f:
            response = client.post(
                "/admin/import",
                files={"file": ("backup.tar.gz", f, "application/gzip")},
                data={"replace": "true"},
            )

        assert response.status_code == 200
        assert "Import complete" in response.text

        # Old note should be gone
        old = client.get("/api/notes/existing")
        assert old.status_code == 404

        # New note should exist
        new = client.get("/api/notes/new")
        assert new.status_code == 200

    def test_admin_page_has_danger_zone(self, client: TestClient):
        """Test that admin page has danger zone section."""
        response = client.get("/admin")

        assert response.status_code == 200
        assert "Danger Zone" in response.text
        assert "Clear All Notes" in response.text

    def test_admin_clear(self, client: TestClient):
        """Test clearing all notes via admin."""
        # Create some notes first
        client.post(
            "/api/notes",
            json={"path": "clear1", "title": "Clear 1", "content": "Content 1"},
        )
        client.post(
            "/api/notes",
            json={"path": "clear2", "title": "Clear 2", "content": "Content 2"},
        )

        # Verify notes exist
        assert client.get("/api/notes/clear1").status_code == 200
        assert client.get("/api/notes/clear2").status_code == 200

        # Clear all notes
        response = client.post("/admin/clear")

        assert response.status_code == 200
        assert "Cleared" in response.text
        assert "2" in response.text

        # Verify notes are gone
        assert client.get("/api/notes/clear1").status_code == 404
        assert client.get("/api/notes/clear2").status_code == 404


class TestMarkdownRendering:
    """Tests for markdown rendering in views."""

    def test_view_note_renders_markdown(self, client: TestClient):
        """Test that note content is rendered as markdown."""
        client.post(
            "/api/notes",
            json={
                "path": "mdtest",
                "title": "Markdown Test",
                "content": "# Heading\n\n**Bold** and *italic*.",
            },
        )

        response = client.get("/notes/mdtest")

        assert response.status_code == 200
        assert "<h1>Heading</h1>" in response.text
        assert "<strong>Bold</strong>" in response.text
        assert "<em>italic</em>" in response.text

    def test_view_note_renders_wiki_links(self, client: TestClient):
        """Test that wiki links are rendered as HTML links."""
        client.post(
            "/api/notes",
            json={
                "path": "wikitest",
                "title": "Wiki Test",
                "content": "See [[other/note]] for more.",
            },
        )

        response = client.get("/notes/wikitest")

        assert response.status_code == 200
        assert 'href="/notes/other/note"' in response.text
        assert 'class="wiki-link"' in response.text

    def test_view_note_renders_wiki_link_with_display(self, client: TestClient):
        """Test wiki link with display text."""
        client.post(
            "/api/notes",
            json={
                "path": "wiki2",
                "title": "Wiki Display",
                "content": "See [[path|Custom Text]].",
            },
        )

        response = client.get("/notes/wiki2")

        assert response.status_code == 200
        assert 'href="/notes/path"' in response.text
        assert ">Custom Text</a>" in response.text

    def test_edit_form_shows_raw_markdown(self, client: TestClient):
        """Test that edit form shows raw markdown, not rendered."""
        client.post(
            "/api/notes",
            json={
                "path": "rawedit",
                "title": "Raw Edit",
                "content": "# Heading\n\n[[wiki/link]]",
            },
        )

        response = client.get("/notes/rawedit/edit")

        assert response.status_code == 200
        # The textarea should contain raw markdown
        assert "# Heading" in response.text
        assert "[[wiki/link]]" in response.text
        # The raw content should be in the textarea, not as rendered HTML
        html = response.text
        # Find textarea content - it should have the raw markdown
        assert "<textarea" in html

    def test_rendered_markdown_has_css_class(self, client: TestClient):
        """Test that rendered content has the correct CSS class."""
        client.post(
            "/api/notes",
            json={"path": "csstest", "title": "CSS Test", "content": "Hello"},
        )

        response = client.get("/notes/csstest")

        assert response.status_code == 200
        assert 'class="note-content rendered-markdown"' in response.text

    def test_preview_endpoint(self, client: TestClient):
        """Test the markdown preview endpoint."""
        response = client.post(
            "/preview",
            data={"content": "# Hello\n\n**Bold** text and [[wiki/link]]"},
        )

        assert response.status_code == 200
        assert "<h1>Hello</h1>" in response.text
        assert "<strong>Bold</strong>" in response.text
        assert 'href="/notes/wiki/link"' in response.text

    def test_preview_endpoint_empty(self, client: TestClient):
        """Test preview with empty content."""
        response = client.post("/preview", data={"content": ""})

        assert response.status_code == 200
        assert response.text == ""

    def test_edit_form_has_preview_toggle(self, client: TestClient):
        """Test that edit form has preview toggle buttons."""
        client.post(
            "/api/notes",
            json={"path": "previewtest", "title": "Preview Test", "content": "Test"},
        )

        response = client.get("/notes/previewtest/edit")

        assert response.status_code == 200
        assert 'id="edit-tab"' in response.text
        assert 'id="preview-tab"' in response.text
        assert 'id="preview-pane"' in response.text

    def test_create_form_has_preview_toggle(self, client: TestClient):
        """Test that create form has preview toggle buttons."""
        response = client.get("/new")

        assert response.status_code == 200
        assert 'id="edit-tab"' in response.text
        assert 'id="preview-tab"' in response.text
        assert 'id="preview-pane"' in response.text


class TestHistoryAPI:
    """Tests for version history API."""

    def test_get_note_history(self, client: TestClient):
        """Test getting note history."""
        # Create a note
        client.post(
            "/api/notes",
            json={"path": "history-test", "title": "History Test", "content": "v1"},
        )
        # Update it to create a second version
        client.put(
            "/api/notes/history-test",
            json={"content": "v2"},
        )

        response = client.get("/api/notes/history-test/history")

        assert response.status_code == 200
        versions = response.json()
        assert len(versions) >= 2
        assert "version" in versions[0]
        assert "timestamp" in versions[0]
        assert "author" in versions[0]
        assert "message" in versions[0]

    def test_get_note_history_single_version(self, client: TestClient):
        """Test getting history for note with only creation commit."""
        client.post(
            "/api/notes",
            json={"path": "single-version", "title": "Single Version", "content": "content"},
        )

        response = client.get("/api/notes/single-version/history")

        assert response.status_code == 200
        versions = response.json()
        # Should have exactly one version (the creation commit)
        assert len(versions) == 1
        assert versions[0]["message"] == "Create note: single-version"

    def test_get_note_version(self, client: TestClient):
        """Test getting a specific version of a note."""
        # Create a note
        client.post(
            "/api/notes",
            json={"path": "version-test", "title": "Original", "content": "original"},
        )
        # Update it
        client.put(
            "/api/notes/version-test",
            json={"title": "Updated", "content": "updated"},
        )

        # Get history to find version SHA
        history_response = client.get("/api/notes/version-test/history")
        versions = history_response.json()

        if len(versions) >= 2:
            # Get the older version
            old_version = versions[-1]["version"]
            response = client.get(f"/api/notes/version-test/versions/{old_version}")

            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Original"
            assert data["content"] == "original"
            assert data["version"] == old_version

    def test_get_note_version_not_found(self, client: TestClient):
        """Test getting a nonexistent version."""
        client.post(
            "/api/notes",
            json={"path": "ver-test", "title": "Test", "content": "content"},
        )

        response = client.get("/api/notes/ver-test/versions/nonexistent123")

        assert response.status_code == 404

    def test_diff_note_versions(self, client: TestClient):
        """Test diffing two versions."""
        # Create and update a note
        client.post(
            "/api/notes",
            json={"path": "diff-test", "title": "Diff Test", "content": "line 1"},
        )
        client.put(
            "/api/notes/diff-test",
            json={"content": "line 1\nline 2"},
        )

        # Get versions
        history_response = client.get("/api/notes/diff-test/history")
        versions = history_response.json()

        if len(versions) >= 2:
            from_ver = versions[-1]["version"]
            to_ver = versions[0]["version"]

            response = client.get(
                f"/api/notes/diff-test/diff?from_version={from_ver}&to_version={to_ver}"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["path"] == "diff-test"
            assert data["from_version"] == from_ver
            assert data["to_version"] == to_ver
            assert "diff" in data
            assert "additions" in data
            assert "deletions" in data

    def test_restore_note_version(self, client: TestClient):
        """Test restoring a note to a previous version."""
        # Create and update a note
        client.post(
            "/api/notes",
            json={"path": "restore-test", "title": "Original", "content": "original"},
        )
        client.put(
            "/api/notes/restore-test",
            json={"title": "Updated", "content": "updated"},
        )

        # Get versions
        history_response = client.get("/api/notes/restore-test/history")
        versions = history_response.json()

        if len(versions) >= 2:
            old_version = versions[-1]["version"]

            response = client.post(f"/api/notes/restore-test/restore/{old_version}")

            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Original"
            assert data["content"] == "original"


class TestHistoryViews:
    """Tests for version history HTML views."""

    def test_view_note_has_history_link(self, client: TestClient):
        """Test that note view page has a history link."""
        client.post(
            "/api/notes",
            json={"path": "link-test", "title": "Link Test", "content": "content"},
        )

        response = client.get("/notes/link-test")

        assert response.status_code == 200
        assert 'href="/notes/link-test/history"' in response.text

    def test_history_page(self, client: TestClient):
        """Test the history page shows version list."""
        client.post(
            "/api/notes",
            json={"path": "hist-page", "title": "Hist Page", "content": "content"},
        )

        response = client.get("/notes/hist-page/history")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Hist Page" in response.text
        assert "History" in response.text

    def test_history_page_not_found(self, client: TestClient):
        """Test history page for nonexistent note."""
        response = client.get("/notes/nonexistent/history")

        assert response.status_code == 404

    def test_version_page(self, client: TestClient):
        """Test viewing a specific version page."""
        client.post(
            "/api/notes",
            json={"path": "ver-page", "title": "Ver Page", "content": "original"},
        )
        client.put(
            "/api/notes/ver-page",
            json={"content": "updated"},
        )

        # Get versions
        history_response = client.get("/api/notes/ver-page/history")
        versions = history_response.json()

        if len(versions) >= 2:
            old_version = versions[-1]["version"]
            response = client.get(f"/notes/ver-page/versions/{old_version}")

            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
            assert "Ver Page" in response.text
            assert old_version[:7] in response.text

    def test_diff_page(self, client: TestClient):
        """Test the diff comparison page."""
        client.post(
            "/api/notes",
            json={"path": "diff-page", "title": "Diff Page", "content": "content"},
        )

        response = client.get("/notes/diff-page/diff")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Compare" in response.text

    def test_restore_via_form(self, client: TestClient):
        """Test restoring via form submission."""
        client.post(
            "/api/notes",
            json={"path": "form-restore", "title": "Original", "content": "original"},
        )
        client.put(
            "/api/notes/form-restore",
            json={"title": "Updated", "content": "updated"},
        )

        # Get versions
        history_response = client.get("/api/notes/form-restore/history")
        versions = history_response.json()

        if len(versions) >= 2:
            old_version = versions[-1]["version"]

            response = client.post(
                f"/notes/form-restore/restore/{old_version}",
                follow_redirects=False,
            )

            assert response.status_code == 303
            assert response.headers["location"] == "/notes/form-restore"

            # Verify restoration
            note_response = client.get("/api/notes/form-restore")
            assert note_response.json()["title"] == "Original"
