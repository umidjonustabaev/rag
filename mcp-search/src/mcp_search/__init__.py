import uvicorn
from mcp_search.config import build_app_config
from mcp_search.logging import setup_logging
from mcp_search.server import create_http_server

app_config = build_app_config()

def main() -> None:
    setup_logging(app_config)

    port = app_config.server.port
    host = app_config.server.host
    app = create_http_server()

    uvicorn.run(app, host=host, port=port)