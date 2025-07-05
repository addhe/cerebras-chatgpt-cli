"""Shell command and system tools."""

import os
import asyncio
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

from .base import Tool, ToolParameter, ToolResult, ToolExecutionError


class ShellCommandTool(Tool):
    """Tool for executing shell commands."""
    
    @property
    def name(self) -> str:
        return "shell_exec"
    
    @property
    def description(self) -> str:
        return "Execute shell commands"
    
    @property
    def category(self) -> str:
        return "shell"
    
    def _setup_parameters(self) -> None:
        self.add_parameter(ToolParameter(
            name="command",
            type=str,
            description="Shell command to execute",
            required=True
        ))
        self.add_parameter(ToolParameter(
            name="cwd",
            type=str,
            description="Working directory for command execution",
            required=False,
            default=None
        ))
        self.add_parameter(ToolParameter(
            name="timeout",
            type=float,
            description="Command timeout in seconds",
            required=False,
            default=30.0
        ))
        self.add_parameter(ToolParameter(
            name="capture_output",
            type=bool,
            description="Capture command output",
            required=False,
            default=True
        ))
        self.add_parameter(ToolParameter(
            name="shell",
            type=bool,
            description="Execute through shell",
            required=False,
            default=True
        ))
    
    async def execute(self, command: str, cwd: Optional[str] = None, 
                     timeout: float = 30.0, capture_output: bool = True,
                     shell: bool = True) -> ToolResult:
        """Execute shell command."""
        try:
            # Resolve working directory
            work_dir = None
            if cwd:
                work_dir = Path(cwd).expanduser().resolve()
                if not work_dir.exists() or not work_dir.is_dir():
                    return ToolResult(
                        success=False,
                        error=f"Working directory not found: {work_dir}"
                    )
            
            # Prepare subprocess arguments
            kwargs = {
                'cwd': str(work_dir) if work_dir else None,
                'shell': shell,
            }
            
            if capture_output:
                kwargs.update({
                    'stdout': subprocess.PIPE,
                    'stderr': subprocess.PIPE,
                })
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                **kwargs
            ) if shell else await asyncio.create_subprocess_exec(
                *command.split(),
                **kwargs
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False,
                    error=f"Command timed out after {timeout} seconds"
                )
            
            return ToolResult(
                success=process.returncode == 0,
                data={
                    'stdout': stdout.decode('utf-8') if stdout else '',
                    'stderr': stderr.decode('utf-8') if stderr else '',
                    'returncode': process.returncode
                },
                error=stderr if process.returncode != 0 else None,
                metadata={
                    'command': command,
                    'cwd': str(work_dir) if work_dir else os.getcwd(),
                    'timeout': timeout,
                    'pid': process.pid
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to execute command: {e}"
            )


class DirectoryTool(Tool):
    """Tool for directory operations."""
    
    @property
    def name(self) -> str:
        return "directory"
    
    @property
    def description(self) -> str:
        return "Directory operations (create, remove, change)"
    
    @property
    def category(self) -> str:
        return "shell"
    
    def _setup_parameters(self) -> None:
        self.add_parameter(ToolParameter(
            name="operation",
            type=str,
            description="Operation: 'create', 'remove', 'change', 'current'",
            required=True
        ))
        self.add_parameter(ToolParameter(
            name="path",
            type=str,
            description="Directory path",
            required=False,
            default=None
        ))
        self.add_parameter(ToolParameter(
            name="recursive",
            type=bool,
            description="Recursive operation for create/remove",
            required=False,
            default=True
        ))
        self.add_parameter(ToolParameter(
            name="force",
            type=bool,
            description="Force operation (for remove)",
            required=False,
            default=False
        ))
    
    async def execute(self, operation: str, path: Optional[str] = None,
                     recursive: bool = True, force: bool = False) -> ToolResult:
        """Execute directory operation."""
        try:
            if operation == "current":
                return ToolResult(
                    success=True,
                    data=os.getcwd(),
                    metadata={'operation': 'current'}
                )
            
            if not path:
                return ToolResult(
                    success=False,
                    error="Path is required for this operation"
                )
            
            dir_path = Path(path).expanduser().resolve()
            
            if operation == "create":
                dir_path.mkdir(parents=recursive, exist_ok=True)
                return ToolResult(
                    success=True,
                    data=f"Directory created: {dir_path}",
                    metadata={
                        'operation': 'create',
                        'path': str(dir_path),
                        'recursive': recursive
                    }
                )
            
            elif operation == "remove":
                if not dir_path.exists():
                    return ToolResult(
                        success=False,
                        error=f"Directory not found: {dir_path}"
                    )
                
                if not dir_path.is_dir():
                    return ToolResult(
                        success=False,
                        error=f"Path is not a directory: {dir_path}"
                    )
                
                if force:
                    shutil.rmtree(dir_path)
                else:
                    # Only remove if empty
                    dir_path.rmdir()
                
                return ToolResult(
                    success=True,
                    data=f"Directory removed: {dir_path}",
                    metadata={
                        'operation': 'remove',
                        'path': str(dir_path),
                        'force': force
                    }
                )
            
            elif operation == "change":
                if not dir_path.exists():
                    return ToolResult(
                        success=False,
                        error=f"Directory not found: {dir_path}"
                    )
                
                if not dir_path.is_dir():
                    return ToolResult(
                        success=False,
                        error=f"Path is not a directory: {dir_path}"
                    )
                
                old_cwd = os.getcwd()
                os.chdir(dir_path)
                
                return ToolResult(
                    success=True,
                    data=f"Changed directory to: {dir_path}",
                    metadata={
                        'operation': 'change',
                        'old_path': old_cwd,
                        'new_path': str(dir_path)
                    }
                )
            
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown operation: {operation}. Use 'create', 'remove', 'change', or 'current'"
                )
                
        except PermissionError as e:
            return ToolResult(
                success=False,
                error=f"Permission denied: {e}"
            )
        except OSError as e:
            return ToolResult(
                success=False,
                error=f"Directory operation failed: {e}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to execute directory operation: {e}"
            )
