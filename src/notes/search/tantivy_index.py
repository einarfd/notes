"""Tantivy-based full-text search index."""

from pathlib import Path

import tantivy

from notes.models.note import Note


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
        schema_builder.add_text_field("tags", stored=True)
        schema_builder.add_date_field("created_at", stored=True, indexed=True)
        schema_builder.add_date_field("updated_at", stored=True, indexed=True)
        self.schema = schema_builder.build()

        # Open or create index
        self.index = tantivy.Index(self.schema, path=str(self.index_dir))

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
                tags=" ".join(note.tags),
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

    def search(self, query: str, limit: int = 10) -> list[dict[str, str]]:
        """Search for notes matching the query."""
        self.index.reload()
        searcher = self.index.searcher()
        parsed_query = self.index.parse_query(
            query, ["title", "content", "tags", "created_at", "updated_at"]
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
