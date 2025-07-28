"""Plugin manager for Cerebras CLI."""

import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type

from ..plugins.base import Plugin, PluginInfo, PluginError
from ..tools.base import ToolRegistry


logger = logging.getLogger(__name__)


class PluginManager:
    """Manages plugin loading and registration."""
    
    def __init__(self, tool_registry: ToolRegistry):
        """Initialize plugin manager."""
        self.tool_registry = tool_registry
        self._plugins: Dict[str, Type[Plugin]] = {}
        self._plugin_instances: Dict[str, Plugin] = {}
        self._search_paths: List[Path] = []
        
        # Add default search paths
        self._setup_default_search_paths()
    
    def _setup_default_search_paths(self) -> None:
        """Set up default paths to search for plugins."""
        # User-specific plugins
        user_plugins = Path.home() / ".cerebras-cli" / "plugins"
        self.add_search_path(user_plugins)
        
        # System-wide plugins (if applicable)
        if os.name != 'nt':  # Not applicable on Windows
            system_plugins = Path("/usr/local/share/cerebras-cli/plugins")
            self.add_search_path(system_plugins)
    
    def add_search_path(self, path: Path) -> None:
        """Add a search path for plugins."""
        if path.exists() and path.is_dir():
            if path not in self._search_paths:
                self._search_paths.append(path)
                logger.debug(f"Added plugin search path: {path}")
        else:
            logger.warning(f"Plugin search path does not exist: {path}")
    
    def register_plugin(self, name: str, plugin_class: Type[Plugin]) -> None:
        """Register a plugin class."""
        if name in self._plugins:
            logger.warning(f"Plugin '{name}' already registered, overwriting")
        
        self._plugins[name] = plugin_class
        logger.debug(f"Registered plugin: {name}")
    
    def unregister_plugin(self, name: str) -> bool:
        """Unregister a plugin."""
        if name in self._plugins:
            del self._plugins[name]
            logger.debug(f"Unregistered plugin: {name}")
            return True
        return False
    
    def load_plugin_from_file(self, name: str, file_path: Path) -> Type[Plugin]:
        """Load a plugin from a specific file."""
        if not file_path.exists():
            raise PluginError(f"Plugin file not found: {file_path}")
        
        try:
            # Create module name
            module_name = f"cerebras_cli.plugins.{name}"
            
            # Load the module
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                raise PluginError(f"Could not load plugin from {file_path}")
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Find the plugin class
            if not hasattr(module, "register_plugin"):
                raise PluginError(f"Plugin module missing register_plugin function: {file_path}")
            
            plugin_class = module.register_plugin()
            if not issubclass(plugin_class, Plugin):
                raise PluginError(f"Plugin class must inherit from Plugin: {file_path}")
            
            # Register the plugin
            self.register_plugin(name, plugin_class)
            return plugin_class
            
        except Exception as e:
            logger.exception(f"Error loading plugin from {file_path}")
            raise PluginError(f"Failed to load plugin from {file_path}: {e}")
    
    def discover_plugins(self) -> None:
        """Discover and load plugins from search paths."""
        for search_path in self._search_paths:
            if not search_path.exists():
                continue
                
            logger.debug(f"Discovering plugins in {search_path}")
            
            for item in search_path.iterdir():
                if item.is_dir() and (item / "__init__.py").exists():
                    # Package directory
                    plugin_name = item.name
                    self.load_plugin(plugin_name, item)
                elif item.is_file() and item.suffix == ".py":
                    # Single module file
                    plugin_name = item.stem
                    self.load_plugin(plugin_name, item)
    
    def load_plugin(self, name: str, source: Union[str, Path]) -> Plugin:
        """Load and instantiate a plugin.
        
        Args:
            name: Name of the plugin
            source: Source of the plugin (path or PyPI package name)
            
        Returns:
            Instantiated plugin
        """
        if name in self._plugins:
            logger.debug(f"Using already registered plugin: {name}")
            plugin_class = self._plugins[name]
        else:
            # Try to load from local path
            if isinstance(source, Path):
                plugin_class = self.load_plugin_from_file(name, source)
            else:
                # Try to load from PyPI or other sources
                raise PluginError(f"Plugin '{name}' not found and loading from PyPI not implemented yet")
        
        # Create plugin instance
        if name in self._plugin_instances:
            return self._plugin_instances[name]
            
        try:
            plugin = plugin_class()
            self._plugin_instances[name] = plugin
            logger.debug(f"Loaded plugin: {name}")
            
            # Register plugin tools
            self._register_plugin_tools(plugin)
            
            return plugin
        except Exception as e:
            logger.exception(f"Error instantiating plugin: {name}")
            raise PluginError(f"Failed to instantiate plugin {name}: {e}")
    
    def _register_plugin_tools(self, plugin: Plugin) -> None:
        """Register tools provided by a plugin."""
        # This is a placeholder - actual implementation would depend on plugin type
        logger.debug(f"Registering tools for plugin: {plugin.name}")
        
        # Example: Register all tools defined in the plugin
        if hasattr(plugin, "get_tools"):
            for tool in plugin.get_tools():
                self.tool_registry.register(tool)
    
    def list_plugins(self) -> List[str]:
        """List all available plugins."""
        return list(self._plugins.keys())
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        if name in self._plugin_instances:
            return self._plugin_instances[name]
        return None
    
    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin."""
        if name in self._plugins:
            plugin = self._plugins[name]
            plugin.info.enabled = True
            logger.debug(f"Enabled plugin: {name}")
            return True
        return False
    
    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin."""
        if name in self._plugins:
            plugin = self._plugins[name]
            plugin.info.enabled = False
            logger.debug(f"Disabled plugin: {name}")
            return True
        return False
    
    def is_plugin_enabled(self, name: str) -> bool:
        """Check if a plugin is enabled."""
        if name in self._plugins:
            return self._plugins[name].info.enabled
        return False
    
    def get_plugin_info(self, name: str) -> Optional[PluginInfo]:
        """Get information about a plugin."""
        if name in self._plugins:
            return self._plugins[name].info
        return None
    
    def get_plugins_by_category(self, category: str) -> List[Plugin]:
        """Get all plugins in a category."""
        return [plugin for plugin in self._plugins.values() if plugin.category == category]
    
    async def execute_plugin(self, name: str, **kwargs) -> ToolResult:
        """Execute a plugin."""
        if name not in self._plugins:
            return ToolResult(success=False, error=f"Plugin '{name}' not found")
            
        if not self.is_plugin_enabled(name):
            return ToolResult(success=False, error=f"Plugin '{name}' is disabled")
            
        try:
            plugin = self.get_plugin(name)
            if not plugin:
                plugin = self.load_plugin(name, name)  # Try to load it
                
            if plugin:
                validated_params = plugin.validate_parameters(kwargs)
                return await plugin.execute(**validated_params)
            else:
                return ToolResult(success=False, error=f"Failed to load plugin '{name}'")
        except Exception as e:
            logger.exception(f"Error executing plugin {name}")
            return ToolResult(success=False, error=f"Plugin execution failed: {e}")
