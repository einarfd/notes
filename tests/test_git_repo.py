"""Tests for git repository manager."""

from pathlib import Path

import pytest

from botnotes.storage.git_repo import GitRepository


@pytest.fixture
def git_repo(temp_dir: Path) -> GitRepository:
    """Provide a git repository instance."""
    repo = GitRepository(temp_dir / "notes")
    repo.ensure_initialized()
    return repo


class TestGitRepositoryInit:
    """Tests for git repository initialization."""

    def test_ensure_initialized_creates_repo(self, temp_dir: Path) -> None:
        """Test that ensure_initialized creates a git repo."""
        repo = GitRepository(temp_dir / "notes")
        result = repo.ensure_initialized()

        assert result is True
        assert (temp_dir / "notes" / ".git").exists()

    def test_ensure_initialized_idempotent(self, temp_dir: Path) -> None:
        """Test that ensure_initialized is idempotent."""
        repo = GitRepository(temp_dir / "notes")
        repo.ensure_initialized()
        result = repo.ensure_initialized()

        assert result is False  # Already initialized


class TestGitRepositoryCommit:
    """Tests for commit operations."""

    def test_commit_change_creates_commit(self, git_repo: GitRepository) -> None:
        """Test that commit_change creates a git commit."""
        # Create a file
        (git_repo.repo_dir / "test.md").write_text("# Test\n\nContent")

        sha = git_repo.commit_change("test", "create", author="tester")

        assert len(sha) == 40  # Full SHA

    def test_commit_change_with_author(self, git_repo: GitRepository) -> None:
        """Test that commit includes author information."""
        (git_repo.repo_dir / "test.md").write_text("# Test")
        git_repo.commit_change("test", "create", author="alice")

        # Check the commit author
        log = git_repo._run_git("log", "-1", "--format=%an")
        assert "alice" in log

    def test_commit_change_without_author(self, git_repo: GitRepository) -> None:
        """Test commit without explicit author uses default."""
        (git_repo.repo_dir / "test.md").write_text("# Test")
        git_repo.commit_change("test", "create")

        # Should use default "Notes System"
        log = git_repo._run_git("log", "-1", "--format=%an")
        assert "Notes System" in log

    def test_commit_delete_operation(self, git_repo: GitRepository) -> None:
        """Test committing a delete operation."""
        # Create and commit a file
        (git_repo.repo_dir / "test.md").write_text("# Test")
        git_repo.commit_change("test", "create")

        # Delete the file
        (git_repo.repo_dir / "test.md").unlink()
        sha = git_repo.commit_change("test", "delete")

        assert len(sha) == 40
        # Verify file is no longer tracked
        log = git_repo._run_git("log", "-1", "--format=%s")
        assert "Delete" in log

    def test_commit_nested_path(self, git_repo: GitRepository) -> None:
        """Test committing a file in a nested directory."""
        nested_dir = git_repo.repo_dir / "projects" / "wiki"
        nested_dir.mkdir(parents=True)
        (nested_dir / "ideas.md").write_text("# Ideas")

        sha = git_repo.commit_change("projects/wiki/ideas", "create")

        assert len(sha) == 40


class TestGitRepositoryHistory:
    """Tests for history retrieval."""

    def test_get_file_history_empty(self, git_repo: GitRepository) -> None:
        """Test getting history for non-existent file."""
        history = git_repo.get_file_history("nonexistent")
        assert history == []

    def test_get_file_history_single_commit(self, git_repo: GitRepository) -> None:
        """Test getting history with single commit."""
        (git_repo.repo_dir / "test.md").write_text("# Test")
        git_repo.commit_change("test", "create", author="alice")

        history = git_repo.get_file_history("test")

        assert len(history) == 1
        assert history[0].author == "alice"
        assert "Create" in history[0].message
        assert len(history[0].commit_sha) == 7

    def test_get_file_history_multiple_commits(self, git_repo: GitRepository) -> None:
        """Test getting history with multiple commits."""
        (git_repo.repo_dir / "test.md").write_text("# Version 1")
        git_repo.commit_change("test", "create", author="alice")

        (git_repo.repo_dir / "test.md").write_text("# Version 2")
        git_repo.commit_change("test", "update", author="bob")

        (git_repo.repo_dir / "test.md").write_text("# Version 3")
        git_repo.commit_change("test", "update", author="charlie")

        history = git_repo.get_file_history("test")

        assert len(history) == 3
        # Most recent first
        assert history[0].author == "charlie"
        assert history[1].author == "bob"
        assert history[2].author == "alice"

    def test_get_file_history_with_limit(self, git_repo: GitRepository) -> None:
        """Test getting history with limit."""
        for i in range(5):
            (git_repo.repo_dir / "test.md").write_text(f"# Version {i}")
            git_repo.commit_change("test", "update" if i > 0 else "create")

        history = git_repo.get_file_history("test", limit=3)

        assert len(history) == 3

    def test_get_file_history_timestamp(self, git_repo: GitRepository) -> None:
        """Test that history includes valid timestamps."""
        (git_repo.repo_dir / "test.md").write_text("# Test")
        git_repo.commit_change("test", "create")

        history = git_repo.get_file_history("test")

        assert len(history) == 1
        assert history[0].timestamp is not None


class TestGitRepositoryVersion:
    """Tests for version retrieval."""

    def test_get_file_at_version_not_found(self, git_repo: GitRepository) -> None:
        """Test getting file at non-existent version."""
        content = git_repo.get_file_at_version("test", "abc123")
        assert content is None

    def test_get_file_at_version(self, git_repo: GitRepository) -> None:
        """Test getting file content at specific version."""
        (git_repo.repo_dir / "test.md").write_text("# Version 1")
        git_repo.commit_change("test", "create")
        history = git_repo.get_file_history("test")
        v1_sha = history[0].commit_sha

        (git_repo.repo_dir / "test.md").write_text("# Version 2")
        git_repo.commit_change("test", "update")

        # Get old version
        content = git_repo.get_file_at_version("test", v1_sha)

        assert content == "# Version 1"

    def test_get_file_at_version_full_sha(self, git_repo: GitRepository) -> None:
        """Test getting file with full SHA works."""
        (git_repo.repo_dir / "test.md").write_text("# Test")
        full_sha = git_repo.commit_change("test", "create")

        content = git_repo.get_file_at_version("test", full_sha)

        assert content == "# Test"


class TestGitRepositoryDiff:
    """Tests for diff generation."""

    def test_diff_versions(self, git_repo: GitRepository) -> None:
        """Test generating diff between two versions."""
        (git_repo.repo_dir / "test.md").write_text("line1\nline2")
        git_repo.commit_change("test", "create")
        v1 = git_repo._get_head_sha()[:7]

        (git_repo.repo_dir / "test.md").write_text("line1\nline2\nline3")
        git_repo.commit_change("test", "update")
        v2 = git_repo._get_head_sha()[:7]

        diff = git_repo.diff_versions("test", v1, v2)

        assert diff.path == "test"
        assert diff.from_version == v1
        assert diff.to_version == v2
        assert "+line3" in diff.diff_text
        assert diff.additions >= 1

    def test_diff_versions_counts(self, git_repo: GitRepository) -> None:
        """Test that diff correctly counts additions and deletions."""
        (git_repo.repo_dir / "test.md").write_text("line1\nline2\nline3")
        git_repo.commit_change("test", "create")
        v1 = git_repo._get_head_sha()[:7]

        # Remove line2, add line4
        (git_repo.repo_dir / "test.md").write_text("line1\nline3\nline4")
        git_repo.commit_change("test", "update")
        v2 = git_repo._get_head_sha()[:7]

        diff = git_repo.diff_versions("test", v1, v2)

        assert diff.deletions >= 1  # line2 removed
        assert diff.additions >= 1  # line4 added

    def test_diff_versions_no_change(self, git_repo: GitRepository) -> None:
        """Test diff when no changes (same version)."""
        (git_repo.repo_dir / "test.md").write_text("content")
        git_repo.commit_change("test", "create")
        v1 = git_repo._get_head_sha()[:7]

        diff = git_repo.diff_versions("test", v1, v1)

        assert diff.diff_text == ""
        assert diff.additions == 0
        assert diff.deletions == 0
