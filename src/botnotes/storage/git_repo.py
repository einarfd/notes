"""Git repository manager for version history."""

import subprocess
from datetime import datetime
from pathlib import Path

from botnotes.models.version import NoteDiff, NoteVersion


class GitRepository:
    """Manages git operations for the notes directory."""

    def __init__(self, repo_dir: Path) -> None:
        """Initialize the git repository manager.

        Args:
            repo_dir: The directory containing the notes (will be the git repo root).
        """
        self.repo_dir = repo_dir

    def ensure_initialized(self) -> bool:
        """Initialize git repo if not exists.

        Returns:
            True if newly initialized, False if already existed.
        """
        git_dir = self.repo_dir / ".git"
        if git_dir.exists():
            return False

        self.repo_dir.mkdir(parents=True, exist_ok=True)
        self._run_git("init")
        # Configure default identity for commits without author
        self._run_git("config", "user.name", "Notes System")
        self._run_git("config", "user.email", "notes@localhost")
        return True

    def commit_change(
        self,
        file_path: str,
        operation: str,
        author: str | None = None,
    ) -> str:
        """Stage and commit a change to a note.

        Args:
            file_path: The note path (without .md extension).
            operation: The operation type ("create", "update", "delete", "move", "restore").
            author: Optional author name for the commit.

        Returns:
            The commit SHA.
        """
        rel_path = f"{file_path}.md"

        if operation == "delete":
            # Stage the deletion - use git add with update flag to track removed files
            self._run_git("add", "--all", "--", rel_path)
        else:
            self._run_git("add", rel_path)

        # Build commit message
        message = f"{operation.capitalize()} note: {file_path}"

        # Build commit command with optional author
        cmd = ["commit", "-m", message, "--allow-empty"]
        if author:
            cmd.extend(["--author", f"{author} <{author}@notes>"])

        self._run_git(*cmd)
        return self._get_head_sha()

    def get_file_history(self, file_path: str, limit: int = 50) -> list[NoteVersion]:
        """Get commit history for a specific note.

        Args:
            file_path: The note path (without .md extension).
            limit: Maximum number of versions to return.

        Returns:
            List of NoteVersion objects, most recent first.
        """
        rel_path = f"{file_path}.md"

        try:
            output = self._run_git(
                "log",
                f"--max-count={limit}",
                "--format=%H|%aI|%an|%s",  # SHA|ISO date|author|subject
                "--follow",  # Follow renames
                "--",
                rel_path,
            )
        except subprocess.CalledProcessError:
            return []

        versions = []
        for line in output.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 3)
            if len(parts) < 4:
                continue
            sha, date_str, author, message = parts
            try:
                timestamp = datetime.fromisoformat(date_str)
            except ValueError:
                timestamp = datetime.now()
            versions.append(
                NoteVersion(
                    commit_sha=sha[:7],
                    timestamp=timestamp,
                    author=author,
                    message=message,
                )
            )
        return versions

    def get_file_at_version(self, file_path: str, commit_sha: str) -> str | None:
        """Get file content at a specific version.

        Args:
            file_path: The note path (without .md extension).
            commit_sha: The commit SHA (short or full).

        Returns:
            The file content at that version, or None if not found.
        """
        rel_path = f"{file_path}.md"
        try:
            return self._run_git("show", f"{commit_sha}:{rel_path}")
        except subprocess.CalledProcessError:
            return None

    def diff_versions(
        self,
        file_path: str,
        from_sha: str,
        to_sha: str,
    ) -> NoteDiff:
        """Generate diff between two versions of a note.

        Args:
            file_path: The note path (without .md extension).
            from_sha: The starting version SHA.
            to_sha: The ending version SHA.

        Returns:
            NoteDiff object with diff information.
        """
        rel_path = f"{file_path}.md"

        try:
            diff_text = self._run_git(
                "diff",
                from_sha,
                to_sha,
                "--",
                rel_path,
            )
        except subprocess.CalledProcessError:
            diff_text = ""

        # Count additions/deletions from diff output
        additions = 0
        deletions = 0
        for line in diff_text.split("\n"):
            if line.startswith("+") and not line.startswith("+++"):
                additions += 1
            elif line.startswith("-") and not line.startswith("---"):
                deletions += 1

        return NoteDiff(
            path=file_path,
            from_version=from_sha[:7] if len(from_sha) > 7 else from_sha,
            to_version=to_sha[:7] if len(to_sha) > 7 else to_sha,
            diff_text=diff_text,
            additions=additions,
            deletions=deletions,
        )

    def _run_git(self, *args: str) -> str:
        """Run a git command and return output.

        Args:
            *args: Git command arguments.

        Returns:
            The command stdout.

        Raises:
            subprocess.CalledProcessError: If the command fails.
        """
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

    def _get_head_sha(self) -> str:
        """Get the current HEAD commit SHA.

        Returns:
            The full commit SHA.
        """
        return self._run_git("rev-parse", "HEAD").strip()
