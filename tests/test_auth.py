"""Tests for authentication module."""

import pytest

from botnotes.auth import ApiKeyAuthProvider


class TestApiKeyAuthProvider:
    """Tests for ApiKeyAuthProvider."""

    @pytest.fixture
    def keys(self) -> dict[str, str]:
        """Sample API keys for testing."""
        return {
            "claude-desktop": "token-abc123",
            "cursor": "token-def456",
            "production": "token-ghi789",
        }

    @pytest.fixture
    def auth_provider(self, keys: dict[str, str]) -> ApiKeyAuthProvider:
        """Create auth provider with sample keys."""
        return ApiKeyAuthProvider(keys)

    @pytest.mark.asyncio
    async def test_valid_token_returns_access_token(
        self, auth_provider: ApiKeyAuthProvider
    ) -> None:
        """Valid token returns AccessToken with correct client_id."""
        result = await auth_provider.verify_token("token-abc123")

        assert result is not None
        assert result.client_id == "claude-desktop"
        assert result.token == "token-abc123"
        assert "botnotes:read" in result.scopes
        assert "botnotes:write" in result.scopes

    @pytest.mark.asyncio
    async def test_invalid_token_returns_none(
        self, auth_provider: ApiKeyAuthProvider
    ) -> None:
        """Invalid token returns None."""
        result = await auth_provider.verify_token("invalid-token")
        assert result is None

    @pytest.mark.asyncio
    async def test_empty_token_returns_none(
        self, auth_provider: ApiKeyAuthProvider
    ) -> None:
        """Empty token returns None."""
        result = await auth_provider.verify_token("")
        assert result is None

    @pytest.mark.asyncio
    async def test_multiple_keys_work(
        self, auth_provider: ApiKeyAuthProvider
    ) -> None:
        """All configured keys work correctly."""
        result1 = await auth_provider.verify_token("token-abc123")
        result2 = await auth_provider.verify_token("token-def456")
        result3 = await auth_provider.verify_token("token-ghi789")

        assert result1 is not None and result1.client_id == "claude-desktop"
        assert result2 is not None and result2.client_id == "cursor"
        assert result3 is not None and result3.client_id == "production"

    def test_empty_keys_dict(self) -> None:
        """Auth provider works with empty keys dict."""
        ApiKeyAuthProvider({})  # Should not raise

    @pytest.mark.asyncio
    async def test_empty_keys_rejects_all(self) -> None:
        """Empty keys dict rejects all tokens."""
        provider = ApiKeyAuthProvider({})
        result = await provider.verify_token("any-token")
        assert result is None
