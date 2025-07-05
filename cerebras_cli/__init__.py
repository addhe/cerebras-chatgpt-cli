"""Cerebras CLI - Command-line interface for Cerebras AI models.

A powerful CLI tool for interacting with Cerebras AI models, featuring:
- Interactive REPL mode
- File operations and context management
- Extensible tools system
- Rich terminal UI
"""

__version__ = "1.0.0"
__author__ = "Addhe Warman Putra (Awan)"
__email__ = "addhe@example.com"

from cerebras_cli.core.client import CerebrasClient
from cerebras_cli.core.config import Config
from cerebras_cli.exceptions import CerebrasCliError

__all__ = [
    "CerebrasClient",
    "Config", 
    "CerebrasCliError",
]
