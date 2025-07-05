"""Configuration management for Cerebras CLI."""

import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from cerebras_cli.exceptions import ConfigurationError


@dataclass
class APIConfig:
    """API configuration settings."""
    base_url: str = "https://api.cerebras.ai"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    
@dataclass
class CLIConfig:
    """CLI behavior configuration."""
    char_delay: float = 0.0  # No delay by default (was 0.02)
    max_history: int = 100
    auto_save: bool = True
    theme: str = "default"
    editor: str = "nano"


@dataclass
class ToolsConfig:
    """Tools configuration."""
    enabled_tools: List[str] = field(default_factory=lambda: [
        "file_tools", "shell_tools", "code_tools"
    ])
    confirm_destructive: bool = True
    sandbox_mode: bool = False


@dataclass
class Config:
    """Main configuration container."""
    api: APIConfig = field(default_factory=APIConfig)
    cli: CLIConfig = field(default_factory=CLIConfig)
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    api_key: Optional[str] = None
    model: str = "llama-4-scout-17b-16e-instruct"
    
    def __post_init__(self):
        """Load configuration from environment variables."""
        self._load_from_environment()
    
    def _load_from_environment(self):
        """Load configuration from environment variables."""
        # API key
        if env_api_key := os.getenv('CEREBRAS_API_KEY'):
            self.api_key = env_api_key
        
        # Model
        if env_model := os.getenv('CEREBRAS_MODEL'):
            self.model = env_model
        
        # Character delay
        if env_char_delay := os.getenv('CEREBRAS_CHAR_DELAY'):
            try:
                self.cli.char_delay = float(env_char_delay)
            except ValueError:
                pass
        
        # API timeout
        if env_timeout := os.getenv('CEREBRAS_TIMEOUT'):
            try:
                self.api.timeout = int(env_timeout)
            except ValueError:
                pass
    
    @classmethod
    def load_from_file(cls, config_path: Path) -> "Config":
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            # Create config with nested objects
            config = cls()
            
            if 'api' in data:
                config.api = APIConfig(**data['api'])
            if 'cli' in data:
                config.cli = CLIConfig(**data['cli'])
            if 'tools' in data:
                config.tools = ToolsConfig(**data['tools'])
            if 'api_key' in data:
                config.api_key = data['api_key']
            if 'model' in data:
                config.model = data['model']
                
            return config
            
        except FileNotFoundError:
            return cls()  # Return default config
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading config: {e}")
    
    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to YAML file."""
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'api': {
                    'base_url': self.api.base_url,
                    'timeout': self.api.timeout,
                    'max_retries': self.api.max_retries,
                    'retry_delay': self.api.retry_delay,
                },
                'cli': {
                    'char_delay': self.cli.char_delay,
                    'max_history': self.cli.max_history,
                    'auto_save': self.cli.auto_save,
                    'theme': self.cli.theme,
                    'editor': self.cli.editor,
                },
                'tools': {
                    'enabled_tools': self.tools.enabled_tools,
                    'confirm_destructive': self.tools.confirm_destructive,
                    'sandbox_mode': self.tools.sandbox_mode,
                },
                'model': self.model,
            }
            
            # Only save API key if it's set and not from environment
            if self.api_key and not os.getenv("CEREBRAS_API_KEY"):
                data['api_key'] = self.api_key
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(data, f, default_flow_style=False, indent=2)
                
        except Exception as e:
            raise ConfigurationError(f"Error saving config: {e}")
    
    def update_from_env(self) -> None:
        """Update configuration from environment variables."""
        # API key from environment (highest priority)
        if env_api_key := os.getenv("CEREBRAS_API_KEY"):
            self.api_key = env_api_key
        
        # Model from environment
        if env_model := os.getenv("CEREBRAS_MODEL"):
            self.model = env_model
        
        # API configuration
        if env_base_url := os.getenv("CEREBRAS_BASE_URL"):
            self.api.base_url = env_base_url
        
        if env_timeout := os.getenv("CEREBRAS_TIMEOUT"):
            try:
                self.api.timeout = int(env_timeout)
            except ValueError:
                pass  # Ignore invalid values
        
        # CLI configuration
        if env_char_delay := os.getenv("CEREBRAS_CHAR_DELAY"):
            try:
                self.cli.char_delay = float(env_char_delay)
            except ValueError:
                pass
                
        if env_theme := os.getenv("CEREBRAS_THEME"):
            self.cli.theme = env_theme


class ConfigManager:
    """Manages configuration loading and saving."""
    
    def __init__(self, config_dir: Optional[Path] = None) -> None:
        """Initialize config manager.
        
        Args:
            config_dir: Custom configuration directory. If None, uses default.
        """
        self.config_dir = config_dir or self._get_default_config_dir()
        self.global_config_path = self.config_dir / "config.yaml"
        self.project_config_path = Path.cwd() / ".cerebras-cli" / "config.yaml"
    
    def _get_default_config_dir(self) -> Path:
        """Get default configuration directory."""
        if config_dir := os.getenv("CEREBRAS_CLI_CONFIG_DIR"):
            return Path(config_dir)
        
        # Use platform-appropriate config directory
        if os.name == 'nt':  # Windows
            config_base = Path(os.getenv("APPDATA", Path.home()))
        else:  # Unix-like systems
            config_base = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
        
        return config_base / "cerebras-cli"
    
    def load_config(self) -> Config:
        """Load configuration with proper precedence.
        
        Precedence (highest to lowest):
        1. Environment variables
        2. Project config (.cerebras-cli/config.yaml)
        3. Global config (~/.cerebras-cli/config.yaml)
        4. Default values
        """
        # Start with global config
        config = Config.load_from_file(self.global_config_path)
        
        # Override with project config if it exists
        if self.project_config_path.exists():
            project_config = Config.load_from_file(self.project_config_path)
            # Merge project config into global config
            config = self._merge_configs(config, project_config)
        
        # Override with environment variables
        config.update_from_env()
        
        return config
    
    def save_global_config(self, config: Config) -> None:
        """Save global configuration."""
        config.save_to_file(self.global_config_path)
    
    def save_project_config(self, config: Config) -> None:
        """Save project-specific configuration."""
        config.save_to_file(self.project_config_path)
    
    def _merge_configs(self, base: Config, override: Config) -> Config:
        """Merge two configurations, with override taking precedence."""
        merged = Config()
        
        # Merge API config
        merged.api.base_url = override.api.base_url if override.api.base_url != APIConfig().base_url else base.api.base_url
        merged.api.timeout = override.api.timeout if override.api.timeout != APIConfig().timeout else base.api.timeout
        merged.api.max_retries = override.api.max_retries if override.api.max_retries != APIConfig().max_retries else base.api.max_retries
        merged.api.retry_delay = override.api.retry_delay if override.api.retry_delay != APIConfig().retry_delay else base.api.retry_delay
        
        # Merge CLI config
        merged.cli.char_delay = override.cli.char_delay if override.cli.char_delay != CLIConfig().char_delay else base.cli.char_delay
        merged.cli.max_history = override.cli.max_history if override.cli.max_history != CLIConfig().max_history else base.cli.max_history
        merged.cli.auto_save = override.cli.auto_save if override.cli.auto_save != CLIConfig().auto_save else base.cli.auto_save
        merged.cli.theme = override.cli.theme if override.cli.theme != CLIConfig().theme else base.cli.theme
        merged.cli.editor = override.cli.editor if override.cli.editor != CLIConfig().editor else base.cli.editor
        
        # Merge tools config
        merged.tools.enabled_tools = override.tools.enabled_tools if override.tools.enabled_tools != ToolsConfig().enabled_tools else base.tools.enabled_tools
        merged.tools.confirm_destructive = override.tools.confirm_destructive if override.tools.confirm_destructive != ToolsConfig().confirm_destructive else base.tools.confirm_destructive
        merged.tools.sandbox_mode = override.tools.sandbox_mode if override.tools.sandbox_mode != ToolsConfig().sandbox_mode else base.tools.sandbox_mode
        
        # Override simple fields
        merged.api_key = override.api_key or base.api_key
        merged.model = override.model if override.model != Config().model else base.model
        
        return merged
