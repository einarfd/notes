"""CLI tools for notes administration."""

import argparse

from notes.services import NoteService


def rebuild_indexes() -> None:
    """Rebuild all indexes from stored notes."""
    print("Rebuilding indexes...")
    service = NoteService()
    result = service.rebuild_indexes()
    print(f"Done! Processed {result.notes_processed} notes.")


def main() -> None:
    """Main entry point for notes-admin CLI."""
    parser = argparse.ArgumentParser(
        prog="notes-admin",
        description="Notes administration tools",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("rebuild", help="Rebuild search and backlinks indexes")

    args = parser.parse_args()

    if args.command == "rebuild":
        rebuild_indexes()


if __name__ == "__main__":
    main()
