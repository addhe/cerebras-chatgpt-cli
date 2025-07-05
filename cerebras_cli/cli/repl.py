"""REPL (Read-Eval-Print Loop) implementation for Cerebras CLI."""

import asyncio
import time
from pathlib import Path
from typing import List, Dict, Optional, Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.text import Text

from cerebras_cli.core.client import CerebrasClient, ResponseProcessor
from cerebras_cli.core.config import Config
from cerebras_cli.exceptions import CerebrasCliError
from cerebras_cli.tools import default_registry


def get_lexer_for_file(file_path: str) -> str:
    """Get appropriate lexer name for file syntax highlighting."""
    ext = Path(file_path).suffix.lower()
    lexer_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.html': 'html',
        '.css': 'css',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.xml': 'xml',
        '.md': 'markdown',
        '.sh': 'bash',
        '.sql': 'sql',
        '.go': 'go',
        '.rs': 'rust',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
    }
    return lexer_map.get(ext, 'text')


class ConversationHistory:
    """Manages conversation history."""
    
    def __init__(self, max_history: int = 100) -> None:
        self.messages: List[Dict[str, str]] = []
        self.max_history = max_history
        self.system_message = {"role": "system", "content": "You are a helpful AI assistant."}
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to history."""
        self.messages.append({"role": role, "content": content})
        
        # Keep only recent messages if history gets too long
        if len(self.messages) > self.max_history:
            # Keep system message and recent messages
            self.messages = [self.system_message] + self.messages[-(self.max_history-1):]
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Get all messages including system message."""
        return [self.system_message] + self.messages
    
    def clear(self) -> None:
        """Clear conversation history."""
        self.messages.clear()
    
    def save_to_file(self, file_path: Path) -> None:
        """Save conversation to file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# Cerebras CLI Conversation\n\n")
            for msg in self.messages:
                f.write(f"## {msg['role'].title()}\n\n")
                f.write(f"{msg['content']}\n\n")
    
    def load_from_file(self, file_path: Path) -> None:
        """Load conversation from file (basic implementation)."""
        # This is a simplified implementation
        # In production, you'd want more sophisticated parsing
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple parsing - this can be improved
        sections = content.split("## ")
        for section in sections[1:]:  # Skip header
            lines = section.strip().split('\n', 1)
            if len(lines) >= 2:
                role = lines[0].lower()
                message_content = lines[1].strip()
                if role in ['user', 'assistant']:
                    self.add_message(role, message_content)


class REPL:
    """Interactive REPL for Cerebras CLI."""
    
    def __init__(self, client: CerebrasClient, config: Config, verbose: bool = False) -> None:
        self.client = client
        self.config = config
        self.verbose = verbose
        self.console = Console()
        self.history = ConversationHistory(config.cli.max_history)
        self.running = True
        self.tools_registry = default_registry
    
    async def run(self) -> None:
        """Start the interactive REPL."""
        self.console.print("[green]🚀 Starting interactive mode...[/green]")
        self.console.print("[dim]Type '/help' for commands, '/exit' to quit, or Ctrl+C to interrupt[/dim]")
        self.console.print()
        
        while self.running:
            try:
                # Get user input
                user_input = Prompt.ask("[bold blue]>[/bold blue]").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    await self.handle_command(user_input)
                    continue
                
                # Handle file includes
                if user_input.startswith('@'):
                    user_input = await self.handle_file_include(user_input)
                    if not user_input:
                        continue
                
                # Process regular input
                await self.process_input(user_input)
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use '/exit' to quit or Ctrl+C again to force quit[/yellow]")
                try:
                    # Give user a moment to type /exit
                    await asyncio.sleep(1)
                except KeyboardInterrupt:
                    self.console.print("\n[red]Forced quit[/red]")
                    break
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                if self.verbose:
                    import traceback
                    self.console.print(f"[dim]{traceback.format_exc()}[/dim]")
    
    async def process_input(self, user_input: str) -> None:
        """Process user input and generate response."""
        # Add user message to history
        self.history.add_message("user", user_input)
        
        try:
            # Show typing indicator
            with self.console.status("[dim]Thinking...[/dim]"):
                start_time = time.time()
                
                # Generate response
                if self.config.cli.char_delay > 0:
                    # Stream response with character delay
                    await self.stream_response_with_delay(self.history.get_messages())
                else:
                    # Generate complete response
                    response_data = await self.client.generate_completion(self.history.get_messages())
                    content = response_data['choices'][0]['message']['content']
                    
                    # Display response
                    self.display_response(content)
                    
                    # Add to history
                    self.history.add_message("assistant", content)
                    
                    # Show usage info if verbose
                    if self.verbose:
                        usage = response_data.get('usage', {})
                        total_time = time.time() - start_time
                        self.show_usage_info(usage, total_time)
                        
        except Exception as e:
            self.console.print(f"[red]Failed to generate response: {e}[/red]")
    
    async def stream_response_with_delay(self, messages: List[Dict[str, str]]) -> None:
        """Stream response with character delay for typewriter effect."""
        try:
            response_content = ""
            
            async for chunk in self.client.stream_completion(messages):
                response_content += chunk
                
                # Print with character delay
                for char in chunk:
                    print(char, end="", flush=True)
                    if self.config.cli.char_delay > 0:
                        await asyncio.sleep(self.config.cli.char_delay)
            
            print()  # New line after response
            
            # Add complete response to history
            if response_content:
                self.history.add_message("assistant", response_content)
                
        except Exception as e:
            self.console.print(f"\n[red]Streaming failed: {e}[/red]")
    
    def display_response(self, content: str) -> None:
        """Display AI response with formatting."""
        # Try to render as markdown if it looks like markdown
        if any(marker in content for marker in ['```', '**', '*', '#', '|']):
            try:
                markdown = Markdown(content)
                self.console.print(markdown)
                return
            except Exception:
                pass  # Fall back to plain text
        
        # Display as plain text with syntax highlighting for code blocks
        self.console.print(content)
    
    def show_usage_info(self, usage: Dict[str, Any], total_time: float) -> None:
        """Show token usage and timing information."""
        total_tokens = usage.get('total_tokens', 0)
        tokens_per_second = total_tokens / max(total_time, 0.001)
        
        info_text = f"[dim]Tokens: {total_tokens} | Time: {total_time:.2f}s | Speed: {tokens_per_second:.1f} tokens/s[/dim]"
        self.console.print(info_text)
    
    async def handle_command(self, command: str) -> None:
        """Handle slash commands."""
        parts = command[1:].split()  # Remove leading '/'
        cmd = parts[0].lower() if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd in ['exit', 'quit']:
            self.console.print("[green]Goodbye! 👋[/green]")
            self.running = False
        
        elif cmd == 'help':
            self.show_help()
        
        elif cmd == 'clear':
            self.console.clear()
            self.history.clear()
            self.console.print("[green]Screen and history cleared[/green]")
        
        elif cmd == 'history':
            self.show_history()
        
        elif cmd == 'save':
            if args:
                await self.save_conversation(args[0])
            else:
                self.console.print("[red]Usage: /save <filename>[/red]")
        
        elif cmd == 'load':
            if args:
                await self.load_conversation(args[0])
            else:
                self.console.print("[red]Usage: /load <filename>[/red]")
        
        elif cmd == 'config':
            self.show_config()
        
        elif cmd == 'models':
            self.show_models()
        
        elif cmd == 'tokens':
            self.show_token_usage()
        
        elif cmd == 'tools':
            if args:
                await self.handle_tool_command(args)
            else:
                self.show_tools()
        
        elif cmd == 'tool':
            if len(args) >= 1:
                await self.execute_tool(args[0], args[1:])
            else:
                self.console.print("[red]Usage: /tool <tool_name> [args...][/red]")
        
        else:
            self.console.print(f"[red]Unknown command: {cmd}[/red]")
            self.console.print("[dim]Type '/help' for available commands[/dim]")
    
    async def handle_file_include(self, user_input: str) -> str:
        """Handle @filename includes."""
        if not user_input.startswith('@'):
            return user_input
        
        # Extract filename and optional additional text
        parts = user_input[1:].split(' ', 1)  # Remove @ and split
        filename = parts[0]
        additional_text = parts[1] if len(parts) > 1 else ""
        
        try:
            file_path = Path(filename)
            if not file_path.exists():
                self.console.print(f"[red]File not found: {filename}[/red]")
                return ""
            
            if not file_path.is_file():
                self.console.print(f"[red]Not a file: {filename}[/red]")
                return ""
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Show file info
            self.console.print(f"[dim]Including file: {filename} ({len(content)} characters)[/dim]")
            
            # Combine file content with additional text
            context = f"File: {filename}\n```\n{content}\n```"
            if additional_text:
                context += f"\n\n{additional_text}"
            
            return context
            
        except Exception as e:
            self.console.print(f"[red]Error reading file {filename}: {e}[/red]")
            return ""
    
    def show_help(self) -> None:
        """Show help information."""
        help_text = """
[bold blue]Cerebras CLI Commands[/bold blue]

[yellow]Slash Commands:[/yellow]
  /help                 Show this help message
  /exit, /quit          Exit the CLI
  /clear                Clear screen and conversation history
  /history              Show conversation history
  /save <filename>      Save conversation to file
  /load <filename>      Load conversation from file
  /config               Show current configuration
  /models               Show available models
  /tokens               Show token usage statistics
  /tools                List available tools
  /tools <tool_name>    Execute a tool directly (e.g., /tools file_list pattern=*.py)
  /tool <name> [args]   Execute a specific tool

[yellow]File Operations:[/yellow]
  @filename             Include file content in your message
  @file.py What does this do?   Include file and ask about it

[yellow]Automatic Tools:[/yellow]
  🤖 AI automatically detects when you need tools!
  Examples:
    "How many .py files are here?"     → auto uses file_list tool
    "List files in current directory"  → auto uses file_list tool
    "Show me files recursively"        → auto uses file_list with recursive=true

[yellow]Tips:[/yellow]
  - Use Ctrl+C to interrupt generation
  - Multi-line input: End with empty line
  - Markdown formatting is supported in responses
  - Files are automatically detected and syntax highlighted
  - 🔧 Watch for "Auto-detecting" messages when tools are used automatically
        """
        
        panel = Panel(help_text.strip(), border_style="blue", title="Help")
        self.console.print(panel)
    
    def show_history(self) -> None:
        """Show conversation history."""
        if not self.history.messages:
            self.console.print("[yellow]No conversation history[/yellow]")
            return
        
        self.console.print(f"[bold]Conversation History ({len(self.history.messages)} messages)[/bold]")
        self.console.print()
        
        for i, msg in enumerate(self.history.messages[-10:], 1):  # Show last 10
            role = msg['role']
            content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            
            color = "blue" if role == "user" else "green"
            self.console.print(f"[{color}]{i}. {role.title()}:[/{color}] {content}")
    
    async def save_conversation(self, filename: str) -> None:
        """Save conversation to file."""
        try:
            file_path = Path(filename)
            self.history.save_to_file(file_path)
            self.console.print(f"[green]Conversation saved to {filename}[/green]")
        except Exception as e:
            self.console.print(f"[red]Error saving conversation: {e}[/red]")
    
    async def load_conversation(self, filename: str) -> None:
        """Load conversation from file."""
        try:
            file_path = Path(filename)
            if not file_path.exists():
                self.console.print(f"[red]File not found: {filename}[/red]")
                return
            
            self.history.load_from_file(file_path)
            self.console.print(f"[green]Conversation loaded from {filename}[/green]")
        except Exception as e:
            self.console.print(f"[red]Error loading conversation: {e}[/red]")
    
    def show_config(self) -> None:
        """Show current configuration."""
        config_text = f"""
[bold]Current Configuration[/bold]

[yellow]Model:[/yellow] {self.config.model}
[yellow]API Base URL:[/yellow] {self.config.api.base_url}
[yellow]Timeout:[/yellow] {self.config.api.timeout}s
[yellow]Max Retries:[/yellow] {self.config.api.max_retries}
[yellow]Character Delay:[/yellow] {self.config.cli.char_delay}s
[yellow]Max History:[/yellow] {self.config.cli.max_history}
[yellow]Theme:[/yellow] {self.config.cli.theme}
[yellow]API Key:[/yellow] {'Set' if self.config.api_key else 'Not set'}
        """
        
        panel = Panel(config_text.strip(), border_style="yellow", title="Configuration")
        self.console.print(panel)
    
    def show_models(self) -> None:
        """Show available models."""
        models_text = """
[bold]Available Models[/bold]

[green]• llama-4-scout-17b-16e-instruct[/green] (default)
  Fast inference, good for general tasks

[blue]• llama-3.1-8b-instruct[/blue]
  Lightweight model for quick responses

[yellow]• llama-3.1-70b-instruct[/yellow]
  Larger model for complex reasoning

To change model: set CEREBRAS_MODEL environment variable
or use --model flag when starting CLI
        """
        
        panel = Panel(models_text.strip(), border_style="green", title="Models")
        self.console.print(panel)
    
    def show_token_usage(self) -> None:
        """Show token usage statistics."""
        # This would need to be implemented with actual tracking
        self.console.print("[yellow]Token usage tracking not yet implemented[/yellow]")
        self.console.print("[dim]This feature will show your token consumption per session[/dim]")
    
    def show_tools(self) -> None:
        """Show available tools."""
        tools_text = self.tools_registry.get_help()
        panel = Panel(tools_text, border_style="cyan", title="Available Tools")
        self.console.print(panel)
    
    async def handle_tool_command(self, args: List[str]) -> None:
        """Handle tool subcommands."""
        if not args:
            self.show_tools()
            return
        
        subcommand = args[0].lower()
        
        if subcommand == "list":
            self.show_tools()
        elif subcommand == "help" and len(args) > 1:
            tool_name = args[1]
            help_text = self.tools_registry.get_help(tool_name)
            self.console.print(help_text)
        elif subcommand == "categories":
            categories = self.tools_registry.list_categories()
            self.console.print(f"[cyan]Available categories:[/cyan] {', '.join(categories)}")
        else:
            self.console.print(f"[red]Unknown tools subcommand: {subcommand}[/red]")
            self.console.print("[dim]Usage: /tools [list|help <tool>|categories][/dim]")
    
    async def execute_tool(self, tool_name: str, args: List[str]) -> None:
        """Execute a tool with arguments."""
        try:
            # Parse tool arguments (simple key=value parsing)
            kwargs = {}
            for arg in args:
                if '=' in arg:
                    key, value = arg.split('=', 1)
                    # Try to parse as different types
                    if value.lower() in ('true', 'false'):
                        kwargs[key] = value.lower() == 'true'
                    elif value.isdigit():
                        kwargs[key] = int(value)
                    else:
                        try:
                            kwargs[key] = float(value)
                        except ValueError:
                            kwargs[key] = value
                else:
                    # Positional argument (use as 'input' or 'text')
                    if 'input' not in kwargs and 'text' not in kwargs:
                        kwargs['input'] = arg
            
            # Execute tool
            with self.console.status(f"[dim]Executing tool: {tool_name}...[/dim]"):
                result = await self.tools_registry.execute_tool(tool_name, **kwargs)
            
            # Display result
            if result.success:
                self.console.print(f"[green]✓ Tool '{tool_name}' executed successfully[/green]")
                
                if result.data:
                    if isinstance(result.data, str):
                        # Display as text/code if it looks like code
                        if tool_name in ['file_read'] and result.metadata.get('mime_type', '').startswith('text/'):
                            file_path = result.metadata.get('path', 'file')
                            syntax = Syntax(result.data, get_lexer_for_file(file_path), theme="monokai")
                            self.console.print(syntax)
                        else:
                            self.console.print(result.data)
                    elif isinstance(result.data, (list, dict)):
                        # Display structured data
                        import json
                        formatted_data = json.dumps(result.data, indent=2, default=str)
                        syntax = Syntax(formatted_data, "json", theme="monokai")
                        self.console.print(syntax)
                    else:
                        self.console.print(str(result.data))
                
                if result.metadata and self.verbose:
                    self.console.print(f"[dim]Metadata: {result.metadata}[/dim]")
            else:
                self.console.print(f"[red]✗ Tool '{tool_name}' failed: {result.error}[/red]")
                
        except Exception as e:
            self.console.print(f"[red]Error executing tool: {e}[/red]")
            if self.verbose:
                import traceback
                self.console.print(f"[dim]{traceback.format_exc()}[/dim]")
