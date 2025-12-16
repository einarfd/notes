"""Authentication providers for MCP server."""

from fastmcp.server.auth import AccessToken, AuthProvider


class ApiKeyAuthProvider(AuthProvider):
    """Bearer token authentication using API keys from config.

    This provider implements the same AuthProvider interface as OAuth providers,
    making it easy to migrate to OAuth later if needed.
    """

    def __init__(self, keys: dict[str, str]) -> None:
        """Initialize with API keys.

        Args:
            keys: Mapping of key name to token value.
        """
        super().__init__()
        # Invert mapping: token -> name for O(1) lookup
        self._token_to_name = {token: name for name, token in keys.items()}

    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify a bearer token.

        Args:
            token: The bearer token from the Authorization header.

        Returns:
            AccessToken with client info if valid, None if invalid.
        """
        name = self._token_to_name.get(token)
        if name is None:
            return None
        return AccessToken(
            token=token,
            client_id=name,
            scopes=["botnotes:read", "botnotes:write"],
        )
