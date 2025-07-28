"""Git integration plugin for Cerebras CLI."""

import git
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..plugins.base import Plugin, PluginInfo, PluginParameter, ToolResult


logger = logging.getLogger(__name__)


class GitPlugin(Plugin):
    """Plugin for Git operations."""
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="git",
            description="Git version control integration",
            version="1.0.0",
            author="Cerebras CLI Team",
            category="devops",
            dependencies=["gitpython"],
            enabled=True
        )
    
    def _setup_parameters(self) -> None:
        """Setup plugin parameters."""
        self.add_parameter(PluginParameter(
            name="repo_path",
            type=Path,
            description="Path to Git repository",
            required=False,
            default=Path.cwd()
        ))
        self.add_parameter(PluginParameter(
            name="branch",
            type=str,
            description="Git branch name",
            required=False
        ))
        self.add_parameter(PluginParameter(
            name="commit_message",
            type=str,
            description="Commit message",
            required=False
        ))
        self.add_parameter(PluginParameter(
            name="files",
            type=list,
            description="List of files to add",
            required=False,
            default=["."]
        ))
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute Git operations based on parameters."""
        try:
            # Get repository
            repo_path = kwargs.get("repo_path", Path.cwd())
            try:
                repo = git.Repo(repo_path)
            except git.exc.InvalidGitRepositoryError:
                return ToolResult(
                    success=False,
                    error=f"Not a Git repository: {repo_path}"
                )
            
            # Handle different Git operations
            if "status" in kwargs:
                return await self._git_status(repo)
            elif "commit" in kwargs:
                return await self._git_commit(repo, kwargs)
            elif "branch" in kwargs:
                return await self._git_branch(repo, kwargs)
            elif "checkout" in kwargs:
                return await self._git_checkout(repo, kwargs)
            elif "pull" in kwargs:
                return await self._git_pull(repo)
            elif "push" in kwargs:
                return await self._git_push(repo)
            else:
                return ToolResult(
                    success=False,
                    error="No Git operation specified. Use status, commit, branch, checkout, pull, or push"
                )
        
        except Exception as e:
            logger.exception("Git operation failed")
            return ToolResult(success=False, error=str(e))
    
    async def _git_status(self, repo: git.Repo) -> ToolResult:
        """Show Git status."""
        try:
            status = repo.git.status()
            return ToolResult(success=True, content=status)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def _git_commit(self, repo: git.Repo, kwargs: Dict[str, Any]) -> ToolResult:
        """Commit changes."""
        try:
            # Add files
            files = kwargs.get("files", ["."])
            repo.git.add(files)
            
            # Commit
            commit_message = kwargs.get("commit_message", "Update")
            repo.git.commit(m=commit_message)
            
            return ToolResult(success=True, content=f"Committed changes: {commit_message}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def _git_branch(self, repo: git.Repo, kwargs: Dict[str, Any]) -> ToolResult:
        """Create or list branches."""
        try:
            branch = kwargs.get("branch")
            if branch:
                # Create new branch
                repo.git.branch(branch)
                return ToolResult(success=True, content=f"Created branch: {branch}")
            else:
                # List branches
                branches = repo.git.branch()
                return ToolResult(success=True, content=branches)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def _git_checkout(self, repo: git.Repo, kwargs: Dict[str, Any]) -> ToolResult:
        """Checkout branch or file."""
        try:
            branch = kwargs.get("branch")
            if branch:
                # Checkout branch
                repo.git.checkout(branch)
                return ToolResult(success=True, content=f"Switched to branch: {branch}")
            else:
                # Checkout files
                files = kwargs.get("files", ["."])
                repo.git.checkout(files)
                return ToolResult(success=True, content=f"Checked out files: {files}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def _git_pull(self, repo: git.Repo) -> ToolResult:
        """Pull changes from remote."""
        try:
            result = repo.git.pull()
            return ToolResult(success=True, content=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def _git_push(self, repo: git.Repo) -> ToolResult:
        """Push changes to remote."""
        try:
            result = repo.git.push()
            return ToolResult(success=True, content=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


def register_plugin():
    """Register the Git plugin."""
    return GitPlugin
