"""Tools system for Cerebras CLI.

This module provides a plugin-like tools system that allows the CLI to perform
various operations like file manipulation, shell commands, code analysis, etc.
"""

from .base import Tool, ToolRegistry, ToolError
from .file_tools import FileReadTool, FileWriteTool, FileListTool
from .shell_tools import ShellCommandTool, DirectoryTool
from .code_tools import CodeAnalysisTool, PythonExecuteTool

__all__ = [
    'Tool',
    'ToolRegistry', 
    'ToolError',
    'FileReadTool',
    'FileWriteTool',
    'FileListTool',
    'ShellCommandTool',
    'DirectoryTool',
    'CodeAnalysisTool',
    'PythonExecuteTool',
]

# Default tool registry
default_registry = ToolRegistry()

# Register default tools
default_registry.register(FileReadTool())
default_registry.register(FileWriteTool())
default_registry.register(FileListTool())
default_registry.register(ShellCommandTool())
default_registry.register(DirectoryTool())
default_registry.register(CodeAnalysisTool())
default_registry.register(PythonExecuteTool())
