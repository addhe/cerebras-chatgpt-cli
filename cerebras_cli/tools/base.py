"""Base classes and interfaces for the tools system."""

import abc
import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, Union

from ..exceptions import CerebrasError

logger = logging.getLogger(__name__)


class ToolError(CerebrasError):
    """Base exception for tool-related errors."""
    pass


class ToolExecutionError(ToolError):
    """Raised when tool execution fails."""
    pass


class ToolValidationError(ToolError):
    """Raised when tool parameters are invalid."""
    pass


@dataclass
class ToolParameter:
    """Represents a tool parameter specification."""
    name: str
    type: Type
    description: str
    required: bool = True
    default: Any = None
    
    def validate(self, value: Any) -> Any:
        """Validate and convert parameter value."""
        if value is None:
            if self.required:
                raise ToolValidationError(f"Required parameter '{self.name}' is missing")
            return self.default
            
        # Basic type checking
        if not isinstance(value, self.type):
            try:
                return self.type(value)
            except (ValueError, TypeError) as e:
                raise ToolValidationError(
                    f"Parameter '{self.name}' must be of type {self.type.__name__}: {e}"
                )
        
        return value


@dataclass
class ToolResult:
    """Represents the result of a tool execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'metadata': self.metadata
        }
    
    def to_json(self) -> str:
        """Convert result to JSON string."""
        return json.dumps(self.to_dict(), default=str, indent=2)


class Tool(abc.ABC):
    """Base class for all tools."""
    
    def __init__(self):
        self._parameters: List[ToolParameter] = []
        self._setup_parameters()
    
    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Tool name identifier."""
        pass
    
    @property
    @abc.abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass
    
    @property
    @abc.abstractmethod
    def category(self) -> str:
        """Tool category (e.g., 'file', 'shell', 'code')."""
        pass
    
    @property
    def parameters(self) -> List[ToolParameter]:
        """Get tool parameters."""
        return self._parameters.copy()
    
    def add_parameter(self, param: ToolParameter) -> None:
        """Add a parameter to the tool."""
        self._parameters.append(param)
    
    @abc.abstractmethod
    def _setup_parameters(self) -> None:
        """Setup tool parameters. Override in subclasses."""
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
            logger.warning(f"Unexpected parameters for tool {self.name}: {unexpected}")
        
        return validated
    
    @abc.abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
    
    def execute_sync(self, **kwargs) -> ToolResult:
        """Execute the tool synchronously."""
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
        """Get help text for the tool."""
        help_text = [
            f"Tool: {self.name}",
            f"Category: {self.category}",
            f"Description: {self.description}",
            "",
            "Parameters:"
        ]
        
        for param in self._parameters:
            required_str = "required" if param.required else f"optional (default: {param.default})"
            help_text.append(f"  {param.name} ({param.type.__name__}, {required_str}): {param.description}")
        
        return "\n".join(help_text)
    
    def __str__(self) -> str:
        return f"{self.name} ({self.category})"


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._categories: Dict[str, List[str]] = {}
    
    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        
        # Update categories
        if tool.category not in self._categories:
            self._categories[tool.category] = []
        if tool.name not in self._categories[tool.category]:
            self._categories[tool.category].append(tool.name)
        
        logger.debug(f"Registered tool: {tool.name}")
    
    def unregister(self, name: str) -> bool:
        """Unregister a tool by name."""
        if name in self._tools:
            tool = self._tools[name]
            del self._tools[name]
            
            # Update categories
            if tool.category in self._categories:
                if name in self._categories[tool.category]:
                    self._categories[tool.category].remove(name)
                if not self._categories[tool.category]:
                    del self._categories[tool.category]
            
            logger.debug(f"Unregistered tool: {name}")
            return True
        return False
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self, category: Optional[str] = None) -> List[str]:
        """List available tools, optionally filtered by category."""
        if category:
            return self._categories.get(category, [])
        return list(self._tools.keys())
    
    def list_categories(self) -> List[str]:
        """List available categories."""
        return list(self._categories.keys())
    
    def get_tools_by_category(self, category: str) -> List[Tool]:
        """Get all tools in a category."""
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]
    
    async def execute_tool(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' not found"
            )
        
        try:
            validated_params = tool.validate_parameters(kwargs)
            return await tool.execute(**validated_params)
        except Exception as e:
            logger.exception(f"Error executing tool {name}")
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {e}"
            )
    
    def get_help(self, name: Optional[str] = None) -> str:
        """Get help for a specific tool or all tools."""
        if name:
            tool = self.get_tool(name)
            if tool:
                return tool.get_help()
            return f"Tool '{name}' not found"
        
        # List all tools by category
        help_text = ["Available Tools:", ""]
        
        for category in sorted(self._categories.keys()):
            help_text.append(f"{category.upper()} TOOLS:")
            for tool_name in sorted(self._categories[category]):
                tool = self._tools[tool_name]
                help_text.append(f"  {tool_name}: {tool.description}")
            help_text.append("")
        
        help_text.append("Use 'help <tool_name>' for detailed help on a specific tool.")
        return "\n".join(help_text)
