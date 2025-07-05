"""Main CLI entry point for Cerebras CLI."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from cerebras_cli.core.config import ConfigManager
from cerebras_cli.core.client import CerebrasClient
from cerebras_cli.cli.repl import REPL
from cerebras_cli.cli.commands import setup_commands
from cerebras_cli.exceptions import CerebrasCliError, AuthenticationError, ConfigurationError


console = Console()


def print_banner() -> None:
    """Print welcome banner."""
    banner_text = Text()
    banner_text.append("🧠 Cerebras CLI", style="bold blue")
    banner_text.append(" v1.0.0\n", style="dim")
    banner_text.append("AI-powered command-line interface\n", style="white")
    banner_text.append("Made by Addhe Warman Putra (Awan)", style="dim")
    
    panel = Panel(
        banner_text,
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)


@click.group(invoke_without_command=True)
@click.option('--config-dir', type=click.Path(path_type=Path), help='Custom configuration directory')
@click.option('--model', help='Model to use for completions')
@click.option('--api-key', help='Cerebras API key')
@click.option('--non-interactive', '-n', is_flag=True, help='Run in non-interactive mode')
@click.option('--prompt', '-p', help='Single prompt to process (non-interactive mode)')
@click.option('--include-file', '-f', multiple=True, help='Include file content in context')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(
    ctx: click.Context,
    config_dir: Optional[Path],
    model: Optional[str],
    api_key: Optional[str],
    non_interactive: bool,
    prompt: Optional[str],
    include_file: tuple,
    verbose: bool
) -> None:
    """Cerebras CLI - AI-powered command-line interface.
    
    Start an interactive session by running without arguments, or use
    specific commands for targeted operations.
    
    Examples:
        cerebras-cli                    # Start interactive mode
        cerebras-cli -p "Hello"         # Single prompt
        cerebras-cli -f file.py -p "Review this code"  # Include file
        cerebras-cli config show        # Show configuration
    """
    # Store context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config_dir'] = config_dir
    
    try:
        # Load configuration
        config_manager = ConfigManager(config_dir)
        config = config_manager.load_config()
        
        # Override with command-line arguments
        if model:
            config.model = model
        if api_key:
            config.api_key = api_key
        
        ctx.obj['config'] = config
        ctx.obj['config_manager'] = config_manager
        
        # If no command specified, run interactive mode or single prompt
        if ctx.invoked_subcommand is None:
            if prompt:
                # Non-interactive mode with single prompt
                asyncio.run(run_single_prompt(config, prompt, include_file, verbose))
            else:
                # Interactive REPL mode
                if not non_interactive:
                    print_banner()
                asyncio.run(run_interactive(config, verbose))
                
    except AuthenticationError as e:
        console.print(f"[red]Authentication Error:[/red] {e}")
        console.print("\n[yellow]Please set your API key using one of these methods:[/yellow]")
        console.print("1. Environment variable: export CEREBRAS_API_KEY=your_key")
        console.print("2. Config file: cerebras-cli config set api-key your_key")
        console.print("3. Command line: cerebras-cli --api-key your_key")
        sys.exit(1)
    except ConfigurationError as e:
        console.print(f"[red]Configuration Error:[/red] {e}")
        sys.exit(1)
    except CerebrasCliError as e:
        console.print(f"[red]Error:[/red] {e}")
        if verbose and e.details:
            console.print(f"[dim]Details: {e.details}[/dim]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        if verbose:
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


async def run_single_prompt(
    config,
    prompt: str,
    include_files: tuple,
    verbose: bool
) -> None:
    """Run a single prompt in non-interactive mode."""
    try:
        # Build context from included files
        context_parts = []
        
        for file_path in include_files:
            try:
                path = Path(file_path)
                if path.exists() and path.is_file():
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    context_parts.append(f"File: {path}\n```\n{content}\n```\n")
                else:
                    console.print(f"[yellow]Warning: File not found: {file_path}[/yellow]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read {file_path}: {e}[/yellow]")
        
        # Combine context and prompt
        full_prompt = "\n".join(context_parts) + prompt if context_parts else prompt
        
        # Create messages
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": full_prompt}
        ]
        
        # Generate response
        async with CerebrasClient(config) as client:
            if verbose:
                console.print(f"[dim]Model: {config.model}[/dim]")
                console.print(f"[dim]Prompt length: {len(full_prompt)} characters[/dim]")
                console.print()
            
            response_data = await client.generate_completion(messages)
            
            # Extract and print response
            content = response_data['choices'][0]['message']['content']
            console.print(content)
            
            if verbose:
                usage = response_data.get('usage', {})
                console.print(f"\n[dim]Tokens used: {usage.get('total_tokens', 'N/A')}[/dim]")
                
    except Exception as e:
        raise CerebrasCliError(f"Failed to process prompt: {e}")


async def run_interactive(config, verbose: bool) -> None:
    """Run interactive REPL mode."""
    try:
        async with CerebrasClient(config) as client:
            repl = REPL(client, config, verbose)
            await repl.run()
    except Exception as e:
        raise CerebrasCliError(f"Failed to start interactive mode: {e}")


# Setup subcommands
setup_commands(cli)


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
