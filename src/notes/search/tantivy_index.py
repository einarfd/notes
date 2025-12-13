"""Tantivy-based full-text search index."""

import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path

import tantivy

from notes.models.note import Note


def _parse_duration(duration: str) -> timedelta:
    """Parse a duration string like '7d', '2w', '1M', '1y' into a timedelta."""
    match = re.match(r"(\d+)([dwMy])", duration)
    if not match:
        raise ValueError(f"Invalid duration: {duration}")

    amount = int(match.group(1))
    unit = match.group(2)

    if unit == "d":
        return timedelta(days=amount)
    elif unit == "w":
        return timedelta(weeks=amount)
    elif unit == "M":
        return timedelta(days=amount * 30)  # Approximate month
    elif unit == "y":
        return timedelta(days=amount * 365)  # Approximate year
    else:
        raise ValueError(f"Unknown duration unit: {unit}")


def _preprocess_date_math(query: str) -> str:
    """Preprocess date math expressions in the query.

    Supports:
        - now: current timestamp
        - now-7d, now+1M: relative to now
        - 2024-01-15: short date format
        - 2024-01-15-7d, 2024-01-15+1M: relative to explicit date

    Duration units: d (days), w (weeks), M (months), y (years)
    """
    now = datetime.now()

    def replace_date_expr(match: re.Match[str]) -> str:
        expr = match.group(0)

        # Parse the base date
        if expr.startswith("now"):
            base_date = now
            remainder = expr[3:]
        else:
            # Try to parse YYYY-MM-DD format
            date_match = re.match(r"(\d{4}-\d{2}-\d{2})", expr)
            if date_match:
                base_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
                remainder = expr[len(date_match.group(1)) :]
            else:
                return expr  # Not a date expression we recognize

        # Apply arithmetic if present
        if remainder:
            arith_match = re.match(r"([+-])(\d+[dwMy])", remainder)
            if arith_match:
                op = arith_match.group(1)
                duration = _parse_duration(arith_match.group(2))
                base_date = base_date + duration if op == "+" else base_date - duration

        return base_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Pattern matches: now, now+/-duration, YYYY-MM-DD, YYYY-MM-DD+/-duration
    # Negative lookahead (?!T) prevents matching dates already in ISO format
    pattern = r"now(?:[+-]\d+[dwMy])?|\d{4}-\d{2}-\d{2}(?![T\d])(?:[+-]\d+[dwMy])?"
    return re.sub(pattern, replace_date_expr, query)


class SearchIndex:
    """Full-text search index using Tantivy."""

    def __init__(self, index_dir: Path) -> None:
        self.index_dir = index_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)

        # Define schema
        schema_builder = tantivy.SchemaBuilder()
        schema_builder.add_text_field("path", stored=True, tokenizer_name="raw")
        schema_builder.add_text_field("title", stored=True)
        schema_builder.add_text_field("content", stored=True)
        schema_builder.add_text_field("tags", stored=True, tokenizer_name="raw")
        schema_builder.add_date_field("created_at", stored=True, indexed=True)
        schema_builder.add_date_field("updated_at", stored=True, indexed=True)
        self.schema = schema_builder.build()

        # Open or create index (handle schema mismatch by recreating)
        try:
            self.index = tantivy.Index(self.schema, path=str(self.index_dir))
        except ValueError as e:
            if "schema" in str(e).lower():
                # Schema changed - delete old index and recreate
                shutil.rmtree(self.index_dir)
                self.index_dir.mkdir(parents=True, exist_ok=True)
                self.index = tantivy.Index(self.schema, path=str(self.index_dir))
            else:
                raise

    def index_note(self, note: Note) -> None:
        """Add or update a note in the index."""
        writer = self.index.writer()
        # Delete existing document with same path
        writer.delete_documents("path", note.path)
        # Add new document
        writer.add_document(
            tantivy.Document(
                path=note.path,
                title=note.title,
                content=note.content,
                tags=note.tags,  # Multi-value field: each tag indexed separately
                created_at=note.created_at,
                updated_at=note.updated_at,
            )
        )
        writer.commit()

    def remove_note(self, path: str) -> None:
        """Remove a note from the index."""
        writer = self.index.writer()
        writer.delete_documents("path", path)
        writer.commit()

    def clear(self) -> None:
        """Clear all documents from the index."""
        writer = self.index.writer()
        writer.delete_all_documents()
        writer.commit()

    def rebuild(self, notes: list[Note]) -> int:
        """Rebuild the index from a list of notes.

        Args:
            notes: List of notes to index

        Returns:
            Number of notes indexed
        """
        self.clear()
        for note in notes:
            self.index_note(note)
        return len(notes)

    def search(self, query: str, limit: int = 10) -> list[dict[str, str]]:
        """Search for notes matching the query."""
        self.index.reload()
        searcher = self.index.searcher()
        # Preprocess date math expressions (now, now-7d, 2024-01-01+1M, etc.)
        processed_query = _preprocess_date_math(query)
        # Field boosting: title > tags > content
        # Date fields still searchable via explicit syntax (e.g., created_at:[now-7d TO now])
        parsed_query = self.index.parse_query(
            processed_query,
            default_field_names=["title", "content", "tags"],
            field_boosts={"title": 2.0, "tags": 1.5, "content": 1.0},
        )

        search_result = searcher.search(parsed_query, limit=limit)
        results = []
        for score, doc_address in search_result.hits:
            doc = searcher.doc(doc_address)
            results.append(
                {
                    "path": doc["path"][0],
                    "title": doc["title"][0],
                    "score": str(score),
                }
            )
        return results
