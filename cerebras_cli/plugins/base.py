"""Base classes for plugins in Cerebras CLI."""

import abc
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, Union

from ..exceptions import CerebrasError
from ..tools.base import Tool, ToolParameter, ToolResult

logger = logging.getLogger(__name__)


class PluginError(CerebrasError):
    """Base exception for plugin-related errors."""
    pass


class PluginExecutionError(PluginError):
    """Raised when plugin execution fails."""
    pass


class PluginValidationError(PluginError):
    """Raised when plugin parameters are invalid."""
    pass


@dataclass
class PluginInfo:
    """Information about a plugin."""
    name: str
    description: str
    version: str
    author: str
    category: str
    dependencies: List[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class PluginParameter:
    """Represents a plugin parameter specification."""
    name: str
    type: Type
    description: str
    required: bool = True
    default: Any = None
    
    def validate(self, value: Any) -> Any:
        """Validate and convert parameter value."""
        if value is None:
            if self.required:
                raise PluginValidationError(f"Required parameter '{self.name}' is missing")
            return self.default
            
        # Basic type checking
        if not isinstance(value, self.type):
            try:
                return self.type(value)
            except (ValueError, TypeError) as e:
                raise PluginValidationError(
                    f"Parameter '{self.name}' must be of type {self.type.__name__}: {e}"
                )
        
        return value


class Plugin(abc.ABC):
    """Base class for all plugins."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._parameters: List[PluginParameter] = []
        self._setup_parameters()
    
    @property
    @abc.abstractmethod
    def info(self) -> PluginInfo:
        """Get plugin information."""
        pass
    
    @property
    def name(self) -> str:
        """Get plugin name."""
        return self.info.name
    
    @property
    def description(self) -> str:
        """Get plugin description."""
        return self.info.description
    
    @property
    def version(self) -> str:
        """Get plugin version."""
        return self.info.version
    
    @property
    def author(self) -> str:
        """Get plugin author."""
        return self.info.author
    
    @property
    def category(self) -> str:
        """Get plugin category."""
        return self.info.category
    
    @property
    def parameters(self) -> List[PluginParameter]:
        """Get plugin parameters."""
        return self._parameters.copy()
    
    def add_parameter(self, param: PluginParameter) -> None:
        """Add a parameter to the plugin."""
        self._parameters.append(param)
    
    @abc.abstractmethod
    def _setup_parameters(self) -> None:
        """Setup plugin parameters. Override in subclasses."""
        pass
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize parameters."""
        validated = {}
        
        for param in self._parameters:
            value = params.get(param.name)
            validated[param.name] = param.validate(value)
        
        # Check for unexpected parameters
        unexpected = set(params.keys()) - {p.name for p in self._parameters}
        if unexpected:
            logger.warning(f"Unexpected parameters for plugin {self.name}: {unexpected}")
        
        return validated
    
    @abc.abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the plugin with given parameters."""
        pass
    
    def execute_sync(self, **kwargs) -> ToolResult:
        """Execute the plugin synchronously."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we need to handle this differently
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.execute(**kwargs))
                    return future.result()
            else:
                return loop.run_until_complete(self.execute(**kwargs))
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def get_help(self) -> str:
        """Get help text for the plugin."""
        help_text = [
            f"Plugin: {self.name}",
            f"Category: {self.category}",
            f"Description: {self.description}",
            f"Version: {self.version}",
            f"Author: {self.author}",
            "",
            "Parameters:"
        ]
        
        for param in self._parameters:
            required_str = "required" if param.required else f"optional (default: {param.default})"
            help_text.append(f"  {param.name} ({param.type.__name__}, {required_str}): {param.description}")
        
        return "\n".join(help_text)
    
    def __str__(self) -> str:
        return f"{self.name} ({self.category})"
