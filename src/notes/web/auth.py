"""Web UI authentication."""

import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from notes.config import get_config

security = HTTPBasic(auto_error=False)

# Type alias for credentials dependency
Credentials = Annotated[HTTPBasicCredentials | None, Depends(security)]


def verify_credentials(credentials: Credentials) -> str | None:
    """Verify HTTP Basic Auth credentials.

    Returns username if authenticated, None if auth is disabled.
    Raises 401 if auth is enabled but credentials are invalid.
    """
    config = get_config()

    # If no web auth configured, allow access
    if not config.web.username or not config.web.password:
        return None

    # Auth is configured - credentials required
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Basic"},
        )

    username_ok = secrets.compare_digest(
        credentials.username.encode(), config.web.username.encode()
    )
    password_ok = secrets.compare_digest(
        credentials.password.encode(), config.web.password.encode()
    )

    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username
