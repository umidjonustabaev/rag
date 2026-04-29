"""MCP server setup and HTTP app factory.

Configures FastMCP with static auth, embeddings, vector store, and search
tools; exposes a Starlette app for HTTP transport.
"""

import logging

from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount

from mcp_search.auth import StaticKeyVerifier
from mcp_search.config import build_app_config
from mcp_search.tools import search_confluence

app_config = build_app_config()


class Server:
    """MCP server with Confluence, Jira, and product-specs search tools.

    Wires FastMCP to a static-key verifier, Gemini embeddings, a Postgres
    vector store, and the Search tool; registers the search methods as MCP tools.
    """

    def __init__(self) -> None:
        """Initialize logging, MCP app, embeddings, vector store, and tools."""
        self.logger = logging.getLogger(__name__)
        self.mcp_app = FastMCP(app_config.server.name, auth=StaticKeyVerifier())
        self.mcp_app.add_tool(search_confluence)

        # Healthcheck
        @self.mcp_app.custom_route("/healthcheck", methods=["GET"])
        def healthcheck(request: Request) -> JSONResponse:
            """Return server status

            Arguments:
                request (Request): HTTP request object
            """
            return JSONResponse(status_code=200, content={"status": "ok"})


def create_http_server() -> Starlette:
    """Build the MCP server and return its Starlette HTTP app.

    Returns:
        A Starlette app with MCP HTTP transport and lifespan handling,
        ready to be run by an ASGI server.
    """
    server = Server()
    mcp_asgi_app = server.mcp_app.http_app()
    return Starlette(routes=[Mount("/search", app=mcp_asgi_app)], lifespan=mcp_asgi_app.lifespan)
