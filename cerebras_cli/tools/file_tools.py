"""File manipulation tools."""

import os
import asyncio
import aiofiles
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, Optional

from .base import Tool, ToolParameter, ToolResult, ToolExecutionError


class FileReadTool(Tool):
    """Tool for reading file contents."""
    
    @property
    def name(self) -> str:
        return "file_read"
    
    @property
    def description(self) -> str:
        return "Read contents of a file"
    
    @property
    def category(self) -> str:
        return "file"
    
    def _setup_parameters(self) -> None:
        self.add_parameter(ToolParameter(
            name="path",
            type=str,
            description="Path to the file to read",
            required=True
        ))
        self.add_parameter(ToolParameter(
            name="encoding",
            type=str,
            description="File encoding",
            required=False,
            default="utf-8"
        ))
        self.add_parameter(ToolParameter(
            name="max_size",
            type=int,
            description="Maximum file size in bytes (default: 10MB)",
            required=False,
            default=10 * 1024 * 1024
        ))
    
    async def execute(self, path: str, encoding: str = "utf-8", max_size: int = 10 * 1024 * 1024) -> ToolResult:
        """Read file contents."""
        try:
            file_path = Path(path).expanduser().resolve()
            
            if not file_path.exists():
                return ToolResult(
                    success=False,
                    error=f"File not found: {file_path}"
                )
            
            if not file_path.is_file():
                return ToolResult(
                    success=False,
                    error=f"Path is not a file: {file_path}"
                )
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > max_size:
                return ToolResult(
                    success=False,
                    error=f"File too large: {file_size} bytes (max: {max_size})"
                )
            
            # Read file
            async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                content = await f.read()
            
            # Get file metadata
            stat = file_path.stat()
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            return ToolResult(
                success=True,
                data=content,
                metadata={
                    'path': str(file_path),
                    'size': file_size,
                    'mime_type': mime_type,
                    'modified': stat.st_mtime,
                    'encoding': encoding
                }
            )
            
        except UnicodeDecodeError as e:
            return ToolResult(
                success=False,
                error=f"Failed to decode file with encoding {encoding}: {e}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to read file: {e}"
            )


class FileWriteTool(Tool):
    """Tool for writing file contents."""
    
    @property
    def name(self) -> str:
        return "file_write"
    
    @property
    def description(self) -> str:
        return "Write content to a file"
    
    @property
    def category(self) -> str:
        return "file"
    
    def _setup_parameters(self) -> None:
        self.add_parameter(ToolParameter(
            name="path",
            type=str,
            description="Path to the file to write",
            required=True
        ))
        self.add_parameter(ToolParameter(
            name="content",
            type=str,
            description="Content to write to the file",
            required=True
        ))
        self.add_parameter(ToolParameter(
            name="encoding",
            type=str,
            description="File encoding",
            required=False,
            default="utf-8"
        ))
        self.add_parameter(ToolParameter(
            name="create_dirs",
            type=bool,
            description="Create parent directories if they don't exist",
            required=False,
            default=True
        ))
        self.add_parameter(ToolParameter(
            name="backup",
            type=bool,
            description="Create backup if file exists",
            required=False,
            default=False
        ))
    
    async def execute(self, path: str, content: str, encoding: str = "utf-8", 
                     create_dirs: bool = True, backup: bool = False) -> ToolResult:
        """Write content to file."""
        try:
            file_path = Path(path).expanduser().resolve()
            
            # Create parent directories if needed
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup if requested and file exists
            backup_path = None
            if backup and file_path.exists():
                backup_path = file_path.with_suffix(file_path.suffix + '.bak')
                import shutil
                shutil.copy2(file_path, backup_path)
            
            # Write content
            async with aiofiles.open(file_path, 'w', encoding=encoding) as f:
                await f.write(content)
            
            # Get file metadata
            stat = file_path.stat()
            
            return ToolResult(
                success=True,
                data=f"File written successfully: {file_path}",
                metadata={
                    'path': str(file_path),
                    'size': stat.st_size,
                    'encoding': encoding,
                    'backup_path': str(backup_path) if backup_path else None
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to write file: {e}"
            )


class FileListTool(Tool):
    """Tool for listing directory contents."""
    
    @property
    def name(self) -> str:
        return "file_list"
    
    @property
    def description(self) -> str:
        return "List files and directories in a path"
    
    @property
    def category(self) -> str:
        return "file"
    
    def _setup_parameters(self) -> None:
        self.add_parameter(ToolParameter(
            name="path",
            type=str,
            description="Path to list (default: current directory)",
            required=False,
            default="."
        ))
        self.add_parameter(ToolParameter(
            name="recursive",
            type=bool,
            description="List recursively",
            required=False,
            default=False
        ))
        self.add_parameter(ToolParameter(
            name="show_hidden",
            type=bool,
            description="Show hidden files and directories",
            required=False,
            default=False
        ))
        self.add_parameter(ToolParameter(
            name="pattern",
            type=str,
            description="Glob pattern to filter files",
            required=False,
            default=None
        ))
        self.add_parameter(ToolParameter(
            name="max_depth",
            type=int,
            description="Maximum recursion depth",
            required=False,
            default=10
        ))
    
    async def execute(self, path: str = ".", recursive: bool = False, 
                     show_hidden: bool = False, pattern: Optional[str] = None,
                     max_depth: int = 10) -> ToolResult:
        """List directory contents."""
        try:
            dir_path = Path(path).expanduser().resolve()
            
            if not dir_path.exists():
                return ToolResult(
                    success=False,
                    error=f"Path not found: {dir_path}"
                )
            
            if not dir_path.is_dir():
                return ToolResult(
                    success=False,
                    error=f"Path is not a directory: {dir_path}"
                )
            
            # List files
            files = []
            
            if recursive:
                # Use rglob for recursive listing
                glob_pattern = pattern or "**/*"
                paths = dir_path.rglob(glob_pattern)
                
                for item_path in paths:
                    # Check depth
                    try:
                        relative = item_path.relative_to(dir_path)
                        depth = len(relative.parts)
                        if depth > max_depth:
                            continue
                    except ValueError:
                        continue
                    
                    # Check hidden files
                    if not show_hidden and any(part.startswith('.') for part in relative.parts):
                        continue
                    
                    files.append(self._get_file_info(item_path, dir_path))
            else:
                # Non-recursive listing
                if pattern:
                    paths = dir_path.glob(pattern)
                else:
                    paths = dir_path.iterdir()
                
                for item_path in sorted(paths):
                    # Check hidden files
                    if not show_hidden and item_path.name.startswith('.'):
                        continue
                    
                    files.append(self._get_file_info(item_path, dir_path))
            
            # Sort files by type (directories first) then by name
            files.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
            
            return ToolResult(
                success=True,
                data=files,
                metadata={
                    'path': str(dir_path),
                    'count': len(files),
                    'recursive': recursive,
                    'pattern': pattern
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to list directory: {e}"
            )
    
    def _get_file_info(self, path: Path, base_path: Path) -> Dict[str, Any]:
        """Get file information."""
        try:
            stat = path.stat()
            relative_path = path.relative_to(base_path)
            mime_type, _ = mimetypes.guess_type(str(path))
            
            return {
                'name': path.name,
                'path': str(relative_path),
                'full_path': str(path),
                'is_dir': path.is_dir(),
                'is_file': path.is_file(),
                'is_link': path.is_symlink(),
                'size': stat.st_size if path.is_file() else None,
                'modified': stat.st_mtime,
                'permissions': oct(stat.st_mode)[-3:],
                'mime_type': mime_type if path.is_file() else None
            }
        except Exception as e:
            return {
                'name': path.name,
                'path': str(path.relative_to(base_path)),
                'full_path': str(path),
                'error': str(e)
            }
