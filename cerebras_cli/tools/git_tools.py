from cerebras_cli.tools.base import Tool, ToolParameter, ToolResult
from pathlib import Path
import os
from typing import List, Optional, Dict, Any
from git import Repo, GitCommandError, InvalidGitRepositoryError
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

class GitTool(Tool):
    """Git operations tool for Cerebras CLI.
    
    Provides integration with git commands for version control operations.
    Automatically detects git repositories and handles common workflows.
    """
    
    def __init__(self):
        """Initialize git tool."""
        super().__init__()
        self.console = Console()
        
    @property
    def name(self) -> str:
        return "git"

    @property
    def description(self) -> str:
        return "Execute git operations and manage version control"

    @property
    def category(self) -> str:
        return "version_control"

    def _setup_parameters(self) -> None:
        """Setup tool parameters with supported git operations."""
        self.add_parameter(ToolParameter(
            name="action",
            type=str,
            description="Git action to perform (status, commit, push, pull, clone, add, log)",
            required=True
        ))
        self.add_parameter(ToolParameter(
            name="repository",
            type=str,
            description="Git repository URL or path",
            required=False
        ))
        self.add_parameter(ToolParameter(
            name="branch",
            type=str,
            description="Git branch name",
            required=False
        ))
        self.add_parameter(ToolParameter(
            name="message",
            type=str,
            description="Commit message",
            required=False
        ))
        self.add_parameter(ToolParameter(
            name="file_pattern",
            type=str,
            description="File pattern to filter operations",
            required=False
        ))
        self.add_parameter(ToolParameter(
            name="remote",
            type=str,
            description="Remote name for push/pull operations",
            required=False,
            default="origin"
        ))

    async def execute(self, action: str, repository: str = None, branch: str = None, 
                     message: str = None, file_pattern: str = None, remote: str = "origin") -> ToolResult:
        """Execute git operation based on action parameter.
        
        Args:
            action: Git operation to perform
            repository: Repository URL or path
            branch: Target branch
            message: Commit message
            file_pattern: File pattern filter
            remote: Remote name for push/pull operations
            
        Returns:
            ToolResult containing git operation output
            
        Raises:
            ToolError: If git operation fails
        """
        try:
            repo = self._get_repo()
            
            if action == "status":
                return self._handle_status(repo)
                
            elif action == "commit":
                if not message:
                    return ToolResult(
                        success=False,
                        error="Commit message required"
                    )
                return self._handle_commit(repo, message, file_pattern)
                
            elif action == "push":
                return self._handle_push(repo, remote, branch)
                
            elif action == "pull":
                return self._handle_pull(repo, remote, branch)
                
            elif action == "clone":
                if not repository:
                    return ToolResult(
                        success=False,
                        error="Repository URL required for clone"
                    )
                return self._handle_clone(repository, branch)
                
            elif action == "add":
                return self._handle_add(repo, file_pattern)
                
            elif action == "log":
                return self._handle_log(repo)
                
            else:
                return ToolResult(
                    success=False,
                    error=f"Unsupported git action: {action}. Supported actions: status, commit, push, pull, clone, add, log"
                )
                
        except InvalidGitRepositoryError:
            return ToolResult(
                success=False,
                error="Not a git repository. Initialize with 'git init' first"
            )
        except GitCommandError as e:
            return ToolResult(
                success=False,
                error=f"Git command failed: {e.stderr.strip()}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Git operation failed: {str(e)}"
            )

    def _get_repo(self) -> Repo:
        """Get git repository object for current directory."""
        try:
            return Repo(Path.cwd())
        except InvalidGitRepositoryError:
            # Try to find git repo in parent directories
            path = Path.cwd()
            while path != path.parent:
                path = path.parent
                try:
                    return Repo(path)
                except InvalidGitRepositoryError:
                    continue
            raise InvalidGitRepositoryError(f"Not a git repository: {Path.cwd()}")

    def _handle_status(self, repo: Repo) -> ToolResult:
        """Handle git status command."""
        # Get untracked files
        untracked = repo.untracked_files
        
        # Get modified files
        modified = [item.a_path for item in repo.index.diff(None)]
        
        # Get staged files
        staged = [item.a_path for item in repo.index.diff("HEAD")]
        
        # Get current branch
        branch = repo.active_branch.name if repo.active_branch else "detached"
        
        # Format output
        table = Table(title="Git Status")
        table.add_column("Status", style="cyan")
        table.add_column("Files", style="magenta")
        
        if untracked:
            table.add_row("Untracked", "\n".join(untracked))
        if modified:
            table.add_row("Modified", "\n".join(modified))
        if staged:
            table.add_row("Staged", "\n".join(staged))
        
        output = f"Current branch: {branch}\n"
        with self.console.capture() as capture:
            self.console.print(table)
        output += capture.get()
        
        return ToolResult(
            success=True,
            content=output,
            data={
                "branch": branch,
                "untracked": untracked,
                "modified": modified,
                "staged": staged
            }
        )

    def _handle_add(self, repo: Repo, file_pattern: str = None) -> ToolResult:
        """Handle git add command."""
        if not file_pattern:
            file_pattern = "."
            
        repo.git.add(file_pattern)
        
        return ToolResult(
            success=True,
            content=f"Added files matching '{file_pattern}' to staging area",
            data={"files": file_pattern}
        )

    def _handle_commit(self, repo: Repo, message: str, file_pattern: str = None) -> ToolResult:
        """Handle git commit command."""
        if file_pattern:
            repo.git.add(file_pattern)
            
        if not repo.index.diff("HEAD"):
            return ToolResult(
                success=False,
                error="Nothing to commit. No changes staged"
            )
            
        repo.git.commit("-m", message)
        
        return ToolResult(
            success=True,
            content=f"Committed changes with message: '{message}'",
            data={"message": message, "commit_hash": repo.head.commit.hexsha[:7]}
        )

    def _handle_push(self, repo: Repo, remote: str, branch: str) -> ToolResult:
        """Handle git push command."""
        if not branch:
            branch = repo.active_branch.name
            
        origin = repo.remote(remote)
        push_info = origin.push(branch)[0]
        
        if push_info.flags & push_info.ERROR:
            raise GitCommandError(f"Push failed: {push_info.summary}")
            
        return ToolResult(
            success=True,
            content=f"Pushed to {remote}/{branch}\n{push_info.summary}",
            data={"remote": remote, "branch": branch, "summary": push_info.summary}
        )

    def _handle_pull(self, repo: Repo, remote: str, branch: str) -> ToolResult:
        """Handle git pull command."""
        if not branch:
            branch = repo.active_branch.name
            
        origin = repo.remote(remote)
        pull_info = origin.pull(branch)[0]
        
        if pull_info.flags & pull_info.ERROR:
            raise GitCommandError(f"Pull failed: {pull_info.summary}")
            
        return ToolResult(
            success=True,
            content=f"Pulled from {remote}/{branch}\n{pull_info.summary}",
            data={"remote": remote, "branch": branch, "summary": pull_info.summary}
        )

    def _handle_clone(self, repository: str, branch: str = None) -> ToolResult:
        """Handle git clone command."""
        target_dir = Path(repository).name.split(".")[0]  # Remove .git if present
        
        if branch:
            repo = Repo.clone_from(repository, target_dir, branch=branch)
        else:
            repo = Repo.clone_from(repository, target_dir)
            
        return ToolResult(
            success=True,
            content=f"Cloned repository into {target_dir}",
            data={"repository": repository, "directory": str(target_dir), "branch": branch or "default"}
        )

    def _handle_log(self, repo: Repo) -> ToolResult:
        """Handle git log command."""
        commits = list(repo.iter_commits(max_count=10))
        
        table = Table(title="Git Log")
        table.add_column("Commit", style="cyan", width=8)
        table.add_column("Author", style="magenta")
        table.add_column("Date", style="green")
        table.add_column("Message", style="white")
        
        for commit in commits:
            table.add_row(
                commit.hexsha[:7],
                f"{commit.author.name} <{commit.author.email}>",
                commit.committed_datetime.strftime("%Y-%m-%d %H:%M"),
                commit.message.strip()
            )
        
        with self.console.capture() as capture:
            self.console.print(table)
            
        return ToolResult(
            success=True,
            content=capture.get(),
            data={"commits": [
                {
                    "hash": commit.hexsha,
                    "author": f"{commit.author.name} <{commit.author.email}>",
                    "date": commit.committed_datetime.isoformat(),
                    "message": commit.message.strip()
                } for commit in commits
            ]}
        )
