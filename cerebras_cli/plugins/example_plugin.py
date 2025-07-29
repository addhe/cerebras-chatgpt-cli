"""Example plugin for Cerebras CLI."""

from ..plugins.base import Plugin, PluginInfo, PluginParameter
from ..tools.base import Tool, ToolResult


class GreetingTool(Tool):
    @property
    def name(self) -> str:
        return "greeting"
    
    @property
    def description(self) -> str:
        return "Generate a friendly greeting"
    
    @property
    def category(self) -> str:
        return "example"
    
    def _setup_parameters(self) -> None:
        self.add_parameter(PluginParameter(
            name="name",
            type=str,
            description="Name to include in greeting",
            required=False,
            default="World"
        ))
    
    async def execute(self, name: str) -> ToolResult:
        return ToolResult(
            success=True,
            content=f"Hello, {name}! Welcome to Cerebras CLI plugins."
        )


class ExamplePlugin(Plugin):
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="example",
            description="Example plugin with greeting tool",
            version="1.0.0",
            author="Cerebras CLI Team",
            category="example",
            dependencies=[],
            enabled=True
        )
    
    def _setup_parameters(self) -> None:
        pass
    
    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=False, error="Example plugin requires a specific tool")
    
    def get_tools(self):
        return [GreetingTool()]


def register_plugin():
    return ExamplePlugin()
