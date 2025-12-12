"""FastAPI web application."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from notes.web.admin import router as admin_router
from notes.web.routes import router as api_router
from notes.web.views import router as views_router

app = FastAPI(
    title="Notes",
    description="AI-friendly note-taking solution",
    version="0.1.0",
)

# Mount static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(api_router)
app.include_router(views_router)
app.include_router(admin_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


def main() -> None:
    """Run the web server."""
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="Run the Notes web server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    args = parser.parse_args()

    uvicorn.run(
        "notes.web.app:app",
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
    )


if __name__ == "__main__":
    main()
