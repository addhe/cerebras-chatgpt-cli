"""CLI commands for Cerebras CLI."""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from cerebras_cli.core.config import ConfigManager, Config
from cerebras_cli.exceptions import ConfigurationError

console = Console()


@click.group()
def config():
    """Configuration management commands."""
    pass


@config.command()
@click.pass_context
def show(ctx: click.Context) -> None:
    """Show current configuration."""
    config_obj: Config = ctx.obj['config']
    
    table = Table(title="Cerebras CLI Configuration")
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")
    table.add_column("Source", style="dim")
    
    # Add configuration rows
    table.add_row("Model", config_obj.model, "config/env")
    table.add_row("API Key", "***set***" if config_obj.api_key else "not set", "env/config")
    table.add_row("Base URL", config_obj.api.base_url, "config")
    table.add_row("Timeout", f"{config_obj.api.timeout}s", "config")
    table.add_row("Max Retries", str(config_obj.api.max_retries), "config")
    table.add_row("Character Delay", f"{config_obj.cli.char_delay}s", "config")
    table.add_row("Max History", str(config_obj.cli.max_history), "config")
    table.add_row("Theme", config_obj.cli.theme, "config")
    table.add_row("Auto Save", str(config_obj.cli.auto_save), "config")
    
    console.print(table)


@config.command()
@click.argument('key')
@click.argument('value')
@click.option('--global', 'use_global', is_flag=True, help='Set in global config')
@click.pass_context
def set(ctx: click.Context, key: str, value: str, use_global: bool) -> None:
    """Set a configuration value."""
    config_manager: ConfigManager = ctx.obj['config_manager']
    config_obj: Config = ctx.obj['config']
    
    # Map key to config attribute
    key_mapping = {
        'model': 'model',
        'api-key': 'api_key',
        'base-url': 'api.base_url',
        'timeout': 'api.timeout',
        'max-retries': 'api.max_retries',
        'retry-delay': 'api.retry_delay',
        'char-delay': 'cli.char_delay',
        'max-history': 'cli.max_history',
        'theme': 'cli.theme',
        'editor': 'cli.editor',
        'auto-save': 'cli.auto_save',
    }
    
    if key not in key_mapping:
        console.print(f"[red]Unknown configuration key: {key}[/red]")
        console.print("Available keys:", ", ".join(key_mapping.keys()))
        return
    
    try:
        # Set the value
        attr_path = key_mapping[key]
        if '.' in attr_path:
            obj_name, attr_name = attr_path.split('.')
            obj = getattr(config_obj, obj_name)
            
            # Type conversion
            current_value = getattr(obj, attr_name)
            if isinstance(current_value, bool):
                value = value.lower() in ('true', '1', 'yes', 'on')
            elif isinstance(current_value, int):
                value = int(value)
            elif isinstance(current_value, float):
                value = float(value)
            
            setattr(obj, attr_name, value)
        else:
            # Type conversion for top-level attributes
            if key == 'api-key':
                config_obj.api_key = value
            elif key == 'model':
                config_obj.model = value
        
        # Save configuration
        if use_global:
            config_manager.save_global_config(config_obj)
            console.print(f"[green]Set {key} = {value} in global config[/green]")
        else:
            config_manager.save_project_config(config_obj)
            console.print(f"[green]Set {key} = {value} in project config[/green]")
            
    except (ValueError, TypeError) as e:
        console.print(f"[red]Invalid value for {key}: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Error setting configuration: {e}[/red]")


@config.command()
@click.argument('key')
@click.pass_context
def get(ctx: click.Context, key: str) -> None:
    """Get a configuration value."""
    config_obj: Config = ctx.obj['config']
    
    key_mapping = {
        'model': config_obj.model,
        'api-key': config_obj.api_key,
        'base-url': config_obj.api.base_url,
        'timeout': config_obj.api.timeout,
        'max-retries': config_obj.api.max_retries,
        'retry-delay': config_obj.api.retry_delay,
        'char-delay': config_obj.cli.char_delay,
        'max-history': config_obj.cli.max_history,
        'theme': config_obj.cli.theme,
        'editor': config_obj.cli.editor,
        'auto-save': config_obj.cli.auto_save,
    }
    
    if key not in key_mapping:
        console.print(f"[red]Unknown configuration key: {key}[/red]")
        return
    
    value = key_mapping[key]
    if key == 'api-key' and value:
        value = "***set***"  # Don't show actual API key
    
    console.print(f"{key}: {value}")


@config.command()
@click.option('--global', 'use_global', is_flag=True, help='Reset global config')
@click.pass_context
def reset(ctx: click.Context, use_global: bool) -> None:
    """Reset configuration to defaults."""
    config_manager: ConfigManager = ctx.obj['config_manager']
    
    try:
        default_config = Config()
        
        if use_global:
            config_manager.save_global_config(default_config)
            console.print("[green]Global configuration reset to defaults[/green]")
        else:
            config_manager.save_project_config(default_config)
            console.print("[green]Project configuration reset to defaults[/green]")
            
    except Exception as e:
        console.print(f"[red]Error resetting configuration: {e}[/red]")


@click.group()
def models():
    """Model management commands."""
    pass


@models.command()
def list() -> None:
    """List available models."""
    table = Table(title="Available Cerebras Models")
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Context Window", style="yellow")
    table.add_column("Best For", style="green")
    
    models_info = [
        ("llama-4-scout-17b-16e-instruct", "Fast inference model", "8K tokens", "General tasks, quick responses"),
        ("llama-3.1-8b-instruct", "Lightweight model", "8K tokens", "Simple tasks, fast responses"),
        ("llama-3.1-70b-instruct", "Large reasoning model", "8K tokens", "Complex reasoning, analysis"),
    ]
    
    for model, desc, context, best_for in models_info:
        table.add_row(model, desc, context, best_for)
    
    console.print(table)
    console.print("\n[dim]Set model with: cerebras-cli config set model <model-name>[/dim]")


@click.group()
def tools():
    """Tools management commands."""
    pass


@tools.command()
@click.pass_context
def list(ctx: click.Context) -> None:
    """List available tools."""
    config_obj: Config = ctx.obj['config']
    
    table = Table(title="Available Tools")
    table.add_column("Tool", style="cyan", no_wrap=True)
    table.add_column("Status", style="white")
    table.add_column("Description", style="white")
    
    tools_info = [
        ("file_tools", "enabled" if "file_tools" in config_obj.tools.enabled_tools else "disabled", "File read/write operations"),
        ("shell_tools", "enabled" if "shell_tools" in config_obj.tools.enabled_tools else "disabled", "Shell command execution"),
        ("code_tools", "enabled" if "code_tools" in config_obj.tools.enabled_tools else "disabled", "Code analysis and generation"),
    ]
    
    for tool, status, desc in tools_info:
        status_color = "green" if status == "enabled" else "red"
        table.add_row(tool, f"[{status_color}]{status}[/{status_color}]", desc)
    
    console.print(table)


@click.command()
def setup() -> None:
    """Interactive setup wizard."""
    console.print(Panel.fit("🧠 Cerebras CLI Setup Wizard", border_style="blue"))
    
    # Check for API key
    api_key = click.prompt("Enter your Cerebras API key", hide_input=True, default="")
    
    if api_key:
        # Create config manager and save API key
        config_manager = ConfigManager()
        config = config_manager.load_config()
        config.api_key = api_key
        
        # Ask for other preferences
        model = click.prompt(
            "Select model", 
            default="llama-4-scout-17b-16e-instruct",
            type=click.Choice([
                "llama-4-scout-17b-16e-instruct",
                "llama-3.1-8b-instruct", 
                "llama-3.1-70b-instruct"
            ])
        )
        config.model = model
        
        char_delay = click.prompt("Character delay for typewriter effect (seconds)", default=0.02, type=float)
        config.cli.char_delay = char_delay
        
        theme = click.prompt("Theme", default="default", type=click.Choice(["default", "dark", "light"]))
        config.cli.theme = theme
        
        # Save configuration
        try:
            config_manager.save_global_config(config)
            console.print("[green]✅ Setup completed successfully![/green]")
            console.print("\n[dim]You can now run 'cerebras-cli' to start using the CLI[/dim]")
        except Exception as e:
            console.print(f"[red]Error saving configuration: {e}[/red]")
    else:
        console.print("[yellow]⚠️  Setup cancelled. You can set the API key later with:[/yellow]")
        console.print("   cerebras-cli config set api-key YOUR_KEY")


@click.command()
@click.pass_context
def doctor(ctx: click.Context) -> None:
    """Diagnose common issues."""
    console.print(Panel.fit("🔍 Cerebras CLI Doctor", border_style="blue"))
    
    config_obj: Config = ctx.obj['config']
    issues = []
    
    # Check API key
    if not config_obj.api_key:
        issues.append("❌ API key not set")
    else:
        console.print("✅ API key is set")
    
    # Check configuration files
    config_manager: ConfigManager = ctx.obj['config_manager']
    
    if config_manager.global_config_path.exists():
        console.print(f"✅ Global config found: {config_manager.global_config_path}")
    else:
        console.print(f"ℹ️  No global config file: {config_manager.global_config_path}")
    
    if config_manager.project_config_path.exists():
        console.print(f"✅ Project config found: {config_manager.project_config_path}")
    else:
        console.print(f"ℹ️  No project config file: {config_manager.project_config_path}")
    
    # Check network connectivity (basic)
    try:
        import urllib.request
        urllib.request.urlopen(config_obj.api.base_url, timeout=5)
        console.print("✅ Network connectivity to API")
    except Exception:
        issues.append("❌ Cannot reach API endpoint")
    
    if issues:
        console.print("\n[red]Issues found:[/red]")
        for issue in issues:
            console.print(f"  {issue}")
        console.print("\n[yellow]Run 'cerebras-cli setup' to fix configuration issues[/yellow]")
    else:
        console.print("\n[green]✅ All checks passed![/green]")


def setup_commands(main_cli) -> None:
    """Add all subcommands to the main CLI."""
    main_cli.add_command(config)
    main_cli.add_command(models)
    main_cli.add_command(tools)
    main_cli.add_command(setup)
    main_cli.add_command(doctor)
