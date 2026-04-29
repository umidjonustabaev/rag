"""Static token verifier for MCP server authentication.

Verifies incoming requests by comparing the token to a single configured
server secret. Used when the server is configured with a static security token.
"""

import secrets
from datetime import datetime, timedelta

from fastmcp.server.auth.auth import AccessToken, TokenVerifier

from mcp_search.config import build_app_config

app_config = build_app_config()


class StaticKeyVerifier(TokenVerifier):
    """Verify tokens by matching against the server's single static secret."""

    async def verify_token(self, token: str) -> AccessToken | None:
        """Check the raw token against the configured security token.

        FastMCP strips the "Bearer " prefix before passing the token here.

        Args:
            token: The raw token string (without "Bearer ").

        Returns:
            An AccessToken with fixed client_id and long expiry if the token
            matches the server secret; None otherwise.
        """

        if secrets.compare_digest(token, app_config.server.security_token):
            return AccessToken(
                token=app_config.server.security_token,
                client_id="authorized_user",
                scopes=[],
                expires_at=int((datetime.now() + timedelta(days=365)).timestamp()),
            )

        return None
