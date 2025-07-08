"""File editing tool for the Cerebras CLI."""

import os
import tempfile
import subprocess
from typing import Dict, Any, Optional
from .base import Tool, ToolResult, ToolParameter


class FileEditTool(Tool):
    """Tool for editing files using external editor or direct modifications."""
    
    @property
    def name(self) -> str:
        return "file_edit"
    
    @property 
    def description(self) -> str:
        return "Edit files using external editor or apply direct modifications"
    
    @property
    def category(self) -> str:
        return "file"
    
    def _setup_parameters(self) -> None:
        """Setup tool parameters."""
        self.add_parameter(ToolParameter(
            name="path",
            type=str,
            description="Path to the file to edit",
            required=True
        ))
        self.add_parameter(ToolParameter(
            name="editor", 
            type=str,
            description="Editor to use (default: system default)",
            required=False
        ))
        self.add_parameter(ToolParameter(
            name="content",
            type=str,
            description="If provided, replace file content with this",
            required=False
        ))
        self.add_parameter(ToolParameter(
            name="line_range",
            type=str,
            description="Line range to edit (e.g., '10-20')",
            required=False
        ))
        self.add_parameter(ToolParameter(
            name="backup",
            type=bool,
            description="Create backup before editing",
            required=False,
            default=True
        ))
    
    def __init__(self):
        super().__init__()
        self.temp_files = []
    
    async def execute(self, 
                     path: str, 
                     editor: str = None, 
                     content: str = None,
                     line_range: Optional[str] = None,
                     backup: bool = True) -> ToolResult:
        """
        Edit a file.
        
        Args:
            path: Path to the file to edit
            editor: Editor to use (default: system default)
            content: If provided, replace file content with this
            line_range: Line range to edit (e.g., "10-20")
            backup: Create backup before editing
        """
        try:
            # Resolve path
            if not os.path.isabs(path):
                path = os.path.abspath(path)
            
            # Check if file exists
            if not os.path.exists(path):
                return ToolResult(
                    success=False,
                    error=f"File not found: {path}",
                    data=None
                )
            
            # Create backup if requested
            backup_path = None
            if backup:
                backup_path = f"{path}.backup"
                try:
                    with open(path, 'r', encoding='utf-8') as src:
                        with open(backup_path, 'w', encoding='utf-8') as dst:
                            dst.write(src.read())
                except Exception as e:
                    return ToolResult(
                        success=False,
                        error=f"Failed to create backup: {e}",
                        data=None
                    )
            
            # If content is provided, replace entire file
            if content is not None:
                try:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    return ToolResult(
                        success=True,
                        data={
                            'action': 'content_replaced',
                            'file': path,
                            'backup': backup_path,
                            'size': len(content)
                        }
                    )
                except Exception as e:
                    return ToolResult(
                        success=False,
                        error=f"Failed to write content: {e}",
                        data=None
                    )
            
            # If line range is specified, edit specific lines
            if line_range:
                return await self._edit_line_range(path, line_range, backup_path)
            
            # Otherwise, open in external editor
            return await self._open_in_editor(path, editor, backup_path)
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"File edit error: {e}",
                data=None
            )
    
    async def _edit_line_range(self, path: str, line_range: str, backup_path: Optional[str]) -> ToolResult:
        """Edit specific line range in file."""
        try:
            # Parse line range (e.g., "10-20" or "15")
            if '-' in line_range:
                start_str, end_str = line_range.split('-', 1)
                start_line = int(start_str.strip())
                end_line = int(end_str.strip())
            else:
                start_line = end_line = int(line_range.strip())
            
            # Read file
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Validate line numbers
            if start_line < 1 or end_line > len(lines) or start_line > end_line:
                return ToolResult(
                    success=False,
                    error=f"Invalid line range: {line_range} (file has {len(lines)} lines)",
                    data=None
                )
            
            # Extract the lines to edit
            lines_to_edit = lines[start_line-1:end_line]
            
            return ToolResult(
                success=True,
                data={
                    'action': 'line_range_extracted',
                    'file': path,
                    'backup': backup_path,
                    'line_range': f"{start_line}-{end_line}",
                    'content': ''.join(lines_to_edit),
                    'total_lines': len(lines)
                }
            )
            
        except ValueError:
            return ToolResult(
                success=False,
                error=f"Invalid line range format: {line_range}",
                data=None
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Line range edit error: {e}",
                data=None
            )
    
    async def _open_in_editor(self, path: str, editor: Optional[str], backup_path: Optional[str]) -> ToolResult:
        """Open file in external editor."""
        try:
            # Determine editor to use
            if not editor:
                editor = os.environ.get('EDITOR', 'nano')
            
            # Check if editor is available
            try:
                subprocess.run(['which', editor], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                # Fallback editors
                fallback_editors = ['nano', 'vi', 'vim', 'code', 'subl']
                editor = None
                for fallback in fallback_editors:
                    try:
                        subprocess.run(['which', fallback], check=True, capture_output=True)
                        editor = fallback
                        break
                    except subprocess.CalledProcessError:
                        continue
                
                if not editor:
                    return ToolResult(
                        success=False,
                        error="No suitable editor found. Please install nano, vim, or set EDITOR environment variable.",
                        data=None
                    )
            
            # Get file stats before editing
            stat_before = os.stat(path)
            
            # Open in editor (this will block until editor is closed)
            try:
                subprocess.run([editor, path], check=True)
            except subprocess.CalledProcessError as e:
                return ToolResult(
                    success=False,
                    error=f"Editor exited with error: {e}",
                    data=None
                )
            
            # Get file stats after editing
            stat_after = os.stat(path)
            
            # Check if file was modified
            was_modified = stat_before.st_mtime != stat_after.st_mtime
            
            return ToolResult(
                success=True,
                data={
                    'action': 'editor_opened',
                    'file': path,
                    'editor': editor,
                    'backup': backup_path,
                    'modified': was_modified,
                    'size_before': stat_before.st_size,
                    'size_after': stat_after.st_size
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Editor error: {e}",
                data=None
            )
    
    def cleanup(self):
        """Clean up any temporary files."""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass
        self.temp_files.clear()
