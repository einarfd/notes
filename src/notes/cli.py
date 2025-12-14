"""CLI tools for notes administration."""

import argparse
import secrets
from pathlib import Path

from notes.backup import clear_notes, export_notes, import_notes
from notes.config import Config, get_config
from notes.services import NoteService


def rebuild_indexes() -> None:
    """Rebuild all indexes from stored notes."""
    print("Rebuilding indexes...")
    service = NoteService()
    result = service.rebuild_indexes()
    print(f"Done! Processed {result.notes_processed} notes.")


def export_backup(output: str | None) -> None:
    """Export all notes to a tar.gz archive."""
    config = get_config()
    output_path = Path(output) if output else None

    print("Exporting notes...")
    result = export_notes(config.notes_dir, output_path)
    print(f"Done! Exported {result.notes_count} notes to {result.path}")


def import_backup(archive: str, replace: bool) -> None:
    """Import notes from a tar.gz archive."""
    config = get_config()
    archive_path = Path(archive)

    if replace:
        print("Importing notes (replacing existing)...")
    else:
        print("Importing notes (merging with existing)...")

    result = import_notes(config.notes_dir, archive_path, replace=replace)

    print(f"Done! Imported {result.imported_count} notes.")
    if result.skipped_count > 0:
        print(f"Skipped {result.skipped_count} existing notes (use --replace to overwrite).")

    # Rebuild indexes after import
    print("Rebuilding indexes...")
    service = NoteService()
    rebuild_result = service.rebuild_indexes()
    print(f"Indexed {rebuild_result.notes_processed} notes.")


def clear_all(force: bool) -> None:
    """Clear all notes."""
    config = get_config()

    if not force:
        print("WARNING: This will delete ALL notes permanently!")
        response = input("Type 'yes' to confirm: ")
        if response.strip().lower() != "yes":
            print("Aborted.")
            return

    print("Clearing all notes...")
    count = clear_notes(config.notes_dir)
    print(f"Deleted {count} notes.")

    # Rebuild indexes (they'll be empty)
    print("Rebuilding indexes...")
    service = NoteService()
    service.rebuild_indexes()
    print("Done!")


def serve(host: str | None, port: int | None) -> None:
    """Run MCP server in HTTP mode."""
    import asyncio

    from notes.auth import ApiKeyAuthProvider
    from notes.server import mcp

    config = Config.load()

    # HTTP mode requires auth - fail early with clear message
    config.validate_for_http()

    if host:
        config.server.host = host
    if port:
        config.server.port = port

    print(f"Starting MCP server on http://{config.server.host}:{config.server.port}")
    print(f"Auth enabled with {len(config.auth.keys)} API key(s):")
    for name in config.auth.keys:
        print(f"  - {name}")

    # Configure auth on the server
    mcp._auth = ApiKeyAuthProvider(config.auth.keys)  # type: ignore[attr-defined]

    # Run HTTP server
    asyncio.run(
        mcp.run_http_async(
            transport="http",
            host=config.server.host,
            port=config.server.port,
        )
    )


def auth_list() -> None:
    """List configured API key names."""
    config = Config.load()
    if not config.auth.keys:
        print("No API keys configured.")
        print("Add one with: notes-admin auth add <name>")
        return

    print("Configured API keys:")
    for name in sorted(config.auth.keys):
        print(f"  - {name}")


def auth_add(name: str) -> None:
    """Add a new API key."""
    config = Config.load()

    if name in config.auth.keys:
        print(f"Error: Key '{name}' already exists.")
        print("Use 'notes-admin auth remove' first to replace it.")
        return

    # Generate secure token
    token = secrets.token_urlsafe(32)
    config.auth.keys[name] = token
    config.save()

    print(f"Added API key '{name}'")
    print(f"Token: {token}")


def auth_remove(name: str) -> None:
    """Remove an API key."""
    config = Config.load()

    if name not in config.auth.keys:
        print(f"Error: Key '{name}' not found.")
        return

    del config.auth.keys[name]
    config.save()
    print(f"Removed API key '{name}'")


def web_set_password(username: str | None) -> None:
    """Set web UI credentials."""
    import getpass

    config = Config.load()

    if not username:
        username = input("Username: ").strip()

    if not username:
        print("Error: Username cannot be empty.")
        return

    password = getpass.getpass("Password: ")

    if not password:
        print("Error: Password cannot be empty.")
        return

    config.web.username = username
    config.web.password = password
    config.save()

    print(f"Web auth configured for user '{username}'")


def web_clear_password() -> None:
    """Remove web UI credentials."""
    config = Config.load()
    config.web.username = None
    config.web.password = None
    config.save()
    print("Web auth disabled")


def main() -> None:
    """Main entry point for notes-admin CLI."""
    parser = argparse.ArgumentParser(
        prog="notes-admin",
        description="Notes administration tools",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Rebuild command
    subparsers.add_parser("rebuild", help="Rebuild search and backlinks indexes")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export notes to a tar.gz archive")
    export_parser.add_argument(
        "output",
        nargs="?",
        help="Output file path (default: notes-backup-YYYY-MM-DD.tar.gz)",
    )

    # Import command
    import_parser = subparsers.add_parser("import", help="Import notes from a tar.gz archive")
    import_parser.add_argument("archive", help="Path to the archive file")
    import_parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace existing notes instead of merging",
    )

    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Delete all notes")
    clear_parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt",
    )

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Run MCP server in HTTP mode")
    serve_parser.add_argument(
        "--host",
        help="Host to bind to (default: from config or 127.0.0.1)",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        help="Port to listen on (default: from config or 8080)",
    )

    # Auth commands
    auth_parser = subparsers.add_parser("auth", help="Manage API keys")
    auth_subparsers = auth_parser.add_subparsers(dest="auth_command", required=True)

    auth_subparsers.add_parser("list", help="List configured API keys")

    auth_add_parser = auth_subparsers.add_parser("add", help="Add a new API key")
    auth_add_parser.add_argument("name", help="Name for the API key")

    auth_remove_parser = auth_subparsers.add_parser("remove", help="Remove an API key")
    auth_remove_parser.add_argument("name", help="Name of the key to remove")

    # Web auth commands
    web_parser = subparsers.add_parser("web", help="Manage web UI authentication")
    web_subparsers = web_parser.add_subparsers(dest="web_command", required=True)

    set_pw_parser = web_subparsers.add_parser("set-password", help="Set web UI credentials")
    set_pw_parser.add_argument("username", nargs="?", help="Username (prompts if not given)")

    web_subparsers.add_parser("clear-password", help="Disable web UI authentication")

    args = parser.parse_args()

    if args.command == "rebuild":
        rebuild_indexes()
    elif args.command == "export":
        export_backup(args.output)
    elif args.command == "import":
        import_backup(args.archive, args.replace)
    elif args.command == "clear":
        clear_all(args.force)
    elif args.command == "serve":
        serve(args.host, args.port)
    elif args.command == "auth":
        if args.auth_command == "list":
            auth_list()
        elif args.auth_command == "add":
            auth_add(args.name)
        elif args.auth_command == "remove":
            auth_remove(args.name)
    elif args.command == "web":
        if args.web_command == "set-password":
            web_set_password(args.username)
        elif args.web_command == "clear-password":
            web_clear_password()


if __name__ == "__main__":
    main()
