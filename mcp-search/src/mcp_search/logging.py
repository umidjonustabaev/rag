"""Logging configuration module for the MCP Search application.

This module provides functions to set up and configure logging for the
application, including handlers, formatters, and log levels.
"""

import logging
import sys

from mcp_search.config import Config


def setup_logging(config: Config) -> None:
    """Set up logging configuration for the application.

    Configures loggers, handlers, and formatters based on the application settings.
    """

    root_logger = logging.getLogger()
    root_logger.setLevel(config.logging.level)
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(config.logging.level)
    console_handler.setFormatter(
        logging.Formatter(fmt=config.logging.format, datefmt=config.logging.datefmt)
    )
    root_logger.addHandler(console_handler)
