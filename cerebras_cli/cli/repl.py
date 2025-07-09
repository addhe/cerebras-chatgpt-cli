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
            # Check if automatic tool usage is needed
            tool_result = await self.detect_and_execute_tools(user_input)
            
            # Show typing indicator
            with self.console.status("[dim]Thinking...[/dim]"):
                start_time = time.time()
                
                # Prepare messages for AI (include tool results if any)
                messages = self.history.get_messages()
                if tool_result:
                    # Add tool result to context
                    tool_context = f"\n\n[Tool Result: {tool_result['summary']}]\n{tool_result['data']}\n"
                    # Modify the last user message to include tool results
                    if messages and messages[-1]['role'] == 'user':
                        messages[-1]['content'] += tool_context
                
                # Generate response
                if self.config.cli.char_delay > 0:
                    # Stream response with character delay
                    await self.stream_response_with_delay(messages)
                else:
                    # Generate complete response
                    response_data = await self.client.generate_completion(messages)
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

    async def detect_and_execute_tools(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Detect if user input requires tools and execute them automatically."""
        import re
        
        user_input_lower = user_input.lower()
        
        # File operation patterns - Ordered by specificity (most specific first)
        file_patterns = [
            # File writing patterns (highest priority for write operations)
            (r'buat.*file.*\.[\w]+', 'file_write', {}),
            (r'create.*file.*\.[\w]+', 'file_write', {}),
            (r'write.*to.*\.[\w]+', 'file_write', {}),
            (r'tulis.*ke.*\.[\w]+', 'file_write', {}),
            (r'simpan.*ke.*\.[\w]+', 'file_write', {}),
            (r'save.*to.*\.[\w]+', 'file_write', {}),
            (r'tambahkan.*ke.*\.[\w]+', 'file_write', {}),
            (r'add.*to.*\.[\w]+', 'file_write', {}),
            (r'buat.*file', 'file_write', {}),
            (r'create.*file', 'file_write', {}),
            (r'write.*file', 'file_write', {}),
            (r'tulis.*file', 'file_write', {}),
            
            # File editing patterns (highest priority for edit operations)
            (r'edit.*\.[\w]+', 'file_edit', {}),
            (r'ubah.*\.[\w]+', 'file_edit', {}),
            (r'modify.*\.[\w]+', 'file_edit', {}),
            (r'update.*\.[\w]+', 'file_edit', {}),
            (r'ganti.*isi.*\.[\w]+', 'file_edit', {}),
            (r'change.*content.*\.[\w]+', 'file_edit', {}),
            (r'edit.*isi.*\.[\w]+', 'file_edit', {}),
            
            # File reading patterns - SPECIFIC file extensions (high priority)
            (r'apa.*isi.*dari.*\.[\w]+', 'file_read', {}),
            (r'baca.*\.[\w]+', 'file_read', {}),
            (r'tampilkan.*isi.*\.[\w]+', 'file_read', {}),
            (r'lihat.*isi.*\.[\w]+', 'file_read', {}),
            (r'show.*content.*\.[\w]+', 'file_read', {}),
            (r'read.*\.[\w]+', 'file_read', {}),
            (r'open.*\.[\w]+', 'file_read', {}),
            (r'list.*isi.*dari.*\.[\w]+', 'file_read', {}),  # "list isi dari X.Y" = read file
            (r'dapat.*melihat.*isi.*\.[\w]+', 'file_read', {}),
            (r'can.*see.*content.*\.[\w]+', 'file_read', {}),
            (r'what.*in.*\.[\w]+', 'file_read', {}),
            (r'view.*\.[\w]+', 'file_read', {}),
            (r'cat.*\.[\w]+', 'file_read', {}),
            
            # Special cases for reading without explicit file extension
            (r'apa.*kamu.*dapat.*melihat.*isi', 'file_read', {}),
            (r'can.*you.*see.*content', 'file_read', {}),
            (r'show.*me.*the.*content', 'file_read', {}),
            (r'apa.*isi.*dari.*config', 'file_read', {}),  # config files
            (r'apa.*isi.*dari.*readme', 'file_read', {}),  # readme files
            
            # File editing patterns
            (r'edit.*\.[\w]+', 'file_edit', {}),
            (r'ubah.*\.[\w]+', 'file_edit', {}),
            (r'modify.*\.[\w]+', 'file_edit', {}),
            (r'update.*\.[\w]+', 'file_edit', {}),
            (r'change.*\.[\w]+', 'file_edit', {}),
            (r'ganti.*isi.*\.[\w]+', 'file_edit', {}),
            (r'edit file', 'file_edit', {}),
            (r'ubah file', 'file_edit', {}),
            
            # File listing patterns - for counting/listing files
            (r'berapa.*file.*\.py', 'file_list', {'pattern': '*.py', 'recursive': True}),
            (r'list.*file.*\.py', 'file_list', {'pattern': '*.py'}),
            (r'ada berapa.*file', 'file_list', {}),
            (r'count.*file', 'file_list', {}),
            (r'list.*file(?!\s*\.)', 'file_list', {}),  # "list files" but not "list file.txt"
            (r'show.*file(?!\s*\.)', 'file_list', {}),  # "show files" but not "show file.txt"
            (r'cari.*file', 'file_list', {'recursive': True}),
            
            # Directory content patterns (lowest priority for file operations)
            (r'list.*isi.*dari.*[^\.]+$', 'file_list', {}),  # "list isi dari folder"
            (r'apa.*isi.*dari.*[^\.]+$', 'file_list', {}),   # "apa isi dari directory"
        ]
        
        # Shell command patterns
        shell_patterns = [
            (r'execute|run|jalankan', 'shell_exec', {}),
            (r'command|perintah', 'shell_exec', {}),
        ]
        
        # Directory patterns
        directory_patterns = [
            (r'berapa.*folder|count.*director', 'file_list', {'recursive': True}),
            (r'list.*director|show.*director', 'file_list', {}),
        ]
        
        # Python execution patterns
        python_patterns = [
            (r'execute.*python|run.*python', 'python_exec', {}),
            (r'calculate|hitung|kalkulasi', 'python_exec', {}),
        ]
        
        all_patterns = file_patterns + shell_patterns + directory_patterns + python_patterns
        
        for pattern, tool_name, default_params in all_patterns:
            if re.search(pattern, user_input_lower):
                return await self._execute_detected_tool(user_input, tool_name, default_params)
        
        return None
    
    async def _execute_detected_tool(self, user_input: str, tool_name: str, default_params: Dict) -> Dict[str, Any]:
        """Execute a detected tool with smart parameter extraction."""
        try:
            params = default_params.copy()
            
            # Smart parameter extraction based on tool type
            if tool_name == 'file_list':
                params.update(self._extract_file_list_params(user_input))
            elif tool_name == 'shell_exec':
                params.update(self._extract_shell_params(user_input))
            elif tool_name == 'python_exec':
                params.update(self._extract_python_params(user_input))
            elif tool_name == 'file_read':
                params.update(self._extract_file_read_params(user_input))
            elif tool_name == 'file_write':
                params.update(self._extract_file_write_params(user_input))
            elif tool_name == 'file_edit':
                params.update(self._extract_file_edit_params(user_input))
            
            # Show what tool is being executed
            self.console.print(f"[dim]🔧 Auto-detecting: Using {tool_name} tool...[/dim]")
            
            # Execute the tool
            result = await self.tools_registry.execute_tool(tool_name, **params)
            
            if result.success:
                # Format the result for context
                if tool_name == 'file_list':
                    files = result.data
                    if isinstance(files, list):
                        summary = f"Found {len(files)} items"
                        if params.get('pattern'):
                            py_files = [f for f in files if f.get('name', '').endswith('.py')]
                            summary = f"Found {len(py_files)} Python files"
                            data = f"Python files: {[f.get('name') for f in py_files]}"
                        else:
                            data = f"Files: {[f.get('name') for f in files[:10]]}"  # Show first 10
                    else:
                        summary = "Listed directory contents"
                        data = str(result.data)
                else:
                    summary = f"Executed {tool_name}"
                    data = str(result.data)
                
                self.console.print(f"[green]✓ Tool result: {summary}[/green]")
                
                return {
                    'tool': tool_name,
                    'summary': summary,
                    'data': data,
                    'raw_result': result.data
                }
            else:
                self.console.print(f"[yellow]⚠ Tool failed: {result.error}[/yellow]")
                return None
                
        except Exception as e:
            self.console.print(f"[red]Error executing auto-tool: {e}[/red]")
            return None
    
    def _extract_file_list_params(self, user_input: str) -> Dict:
        """Extract parameters for file_list tool."""
        import re
        params = {}
        
        # Check for file extensions
        if re.search(r'\.py', user_input):
            params['pattern'] = '*.py'
        elif re.search(r'\.js', user_input):
            params['pattern'] = '*.js'
        elif re.search(r'\.txt', user_input):
            params['pattern'] = '*.txt'
        elif re.search(r'\.md', user_input):
            params['pattern'] = '*.md'
        
        # Check for recursive/subfolder mentions
        if re.search(r'subfolder|recursive|semua.*folder', user_input.lower()):
            params['recursive'] = True
        
        # Check for "current directory" references - don't set path for these
        current_dir_patterns = [
            r'directory ini',
            r'direktori ini', 
            r'folder ini',
            r'here',
            r'current directory',
            r'current folder',
            r'this directory',
            r'this folder'
        ]
        
        is_current_dir = any(re.search(pattern, user_input.lower()) for pattern in current_dir_patterns)
        if is_current_dir:
            # Don't set path - use current directory (default)
            return params
        
        # Check for specific paths including directory names
        path_patterns = [
            r'/[\w/]+',                    # Absolute paths like /tmp
            r'\.\/[\w/]+',                 # Relative paths like ./src  
            r'dari ([A-Za-z0-9_-]+)(?!\.[A-Za-z]+)',  # "dari folder_name" (not files)
            r'directory ([A-Za-z0-9_-]+)', # "directory folder_name"
            r'folder ([A-Za-z0-9_-]+)',    # "folder folder_name"
        ]
        
        for pattern in path_patterns:
            path_match = re.search(pattern, user_input)
            if path_match:
                if pattern.startswith(r'dari') or pattern.startswith(r'directory') or pattern.startswith(r'folder'):
                    # Extract just the folder name from "dari X" patterns
                    folder_name = path_match.group(1)
                    # Skip common words that indicate current directory
                    if folder_name.lower() not in ['ini', 'this', 'here', 'current']:
                        params['path'] = folder_name
                else:
                    # Extract full path for other patterns
                    params['path'] = path_match.group()
                break
        
        return params
    
    def _extract_shell_params(self, user_input: str) -> Dict:
        """Extract parameters for shell_exec tool."""
        # For now, let the AI handle shell commands
        return {}
    
    def _extract_python_params(self, user_input: str) -> Dict:
        """Extract parameters for python_exec tool."""
        # For now, let the AI handle Python code
        return {}
    
    def _extract_file_read_params(self, user_input: str) -> Dict:
        """Extract parameters for file_read tool."""
        import re
        import os
        params = {}
        
        # First, try to extract full paths (absolute or relative with folder)
        # Pattern to match file paths like "/path/to/file.ext", "./folder/file.ext", "folder/file.ext"
        path_patterns = [
            r'([~/]?[A-Za-z0-9_./\\-]+/[A-Za-z0-9_.-]+\.[A-Za-z0-9]+)',  # Full paths with folders
            r'([A-Za-z0-9_.-]+\.[A-Za-z0-9]+)\s+(?:di|in|from)\s+(?:folder\s+)?([~/]?[A-Za-z0-9_./\\-]+)',  # "file.txt di folder /path"
            r'(?:folder\s+)?([~/]?[A-Za-z0-9_./\\-]+)/([A-Za-z0-9_.-]+\.[A-Za-z0-9]+)',  # "folder /path/file.txt"
        ]
        
        for pattern in path_patterns:
            path_match = re.search(pattern, user_input, re.IGNORECASE)
            if path_match:
                if len(path_match.groups()) == 1:
                    # Full path matched
                    params['path'] = path_match.group(1)
                elif len(path_match.groups()) == 2:
                    # Filename and folder matched separately
                    filename, folder = path_match.groups()
                    if 'di folder' in user_input.lower() or 'in folder' in user_input.lower():
                        # "file.txt di folder /path" format
                        params['path'] = os.path.join(folder, filename)
                    else:
                        # "folder/file.txt" format
                        params['path'] = os.path.join(path_match.group(1), path_match.group(2))
                break
        
        # If no path found, look for standalone filenames
        if 'path' not in params:
            file_patterns = [
                r'([A-Za-z_][A-Za-z0-9_.-]*\.[A-Za-z0-9]+)',  # Standard filenames
                r'([A-Z_][A-Z0-9_]*\.md)',                     # ALL_CAPS.md files  
                r'((?:config|readme)\.[A-Za-z]+)',                        # config.* or readme.* files
                r'([Rr]eadme\.[A-Za-z]+)',                     # README files
            ]
            
            for pattern in file_patterns:
                file_match = re.search(pattern, user_input)
                if file_match:
                    params['path'] = file_match.group(1)
                    break
        
        # If still no file found, try extracting from common phrases
        if 'path' not in params:
            # Extract from "isi dari X" or "content of X"
            content_patterns = [
                r'isi dari ([A-Za-z0-9_.-]+)',
                r'content of ([A-Za-z0-9_.-]+)',
                r'melihat isi ([A-Za-z0-9_.-]+)',
                r'melihat isi dari ([A-Za-z0-9_.-]+)',
                r'baca ([A-Za-z0-9_.-]+)',
                r'read ([A-Za-z0-9_.-]+)',
                r'show me ([A-Za-z0-9_.-]+)',
                r'view ([A-Za-z0-9_.-]+)',
                r'see ([A-Za-z0-9_.-]+)',
            ]
            
            for pattern in content_patterns:
                match = re.search(pattern, user_input)
                if match:
                    filename = match.group(1)
                    # Add common extension if missing
                    if '.' not in filename:
                        # Try common extensions based on context or filename
                        if any(word in user_input.lower() for word in ['code', 'script', 'program']):
                            filename += '.py'
                        elif any(word in user_input.lower() for word in ['doc', 'guide', 'readme']):
                            filename += '.md'
                        elif 'config' in filename.lower():
                            filename += '.py'
                        elif 'readme' in filename.lower():
                            filename += '.md'
                        elif filename.lower() in ['license', 'changelog', 'authors']:
                            # Keep without extension for common files
                            pass
                        else:
                            # Default to .py for unknown files
                            filename += '.py'
                    params['path'] = filename
                    break
        
        return params
    
    def _extract_file_edit_params(self, user_input: str) -> Dict:
        """Extract parameters for file_edit tool."""
        import re
        import os
        params = {}
        
        # First, try to extract full paths (absolute or relative with folder)
        # Pattern to match file paths like "/path/to/file.ext", "./folder/file.ext", "folder/file.ext"
        path_patterns = [
            r'([~/]?[A-Za-z0-9_./\\-]+/[A-Za-z0-9_.-]+\.[A-Za-z0-9]+)',  # Full paths with folders
            r'([A-Za-z0-9_.-]+\.[A-Za-z0-9]+)\s+(?:di|in|from)\s+(?:folder\s+)?([~/]?[A-Za-z0-9_./\\-]+)',  # "file.txt di folder /path"
            r'(?:folder\s+)?([~/]?[A-Za-z0-9_./\\-]+)/([A-Za-z0-9_.-]+\.[A-Za-z0-9]+)',  # "folder /path/file.txt"
        ]
        
        for pattern in path_patterns:
            path_match = re.search(pattern, user_input, re.IGNORECASE)
            if path_match:
                if len(path_match.groups()) == 1:
                    # Full path matched
                    params['path'] = path_match.group(1)
                elif len(path_match.groups()) == 2:
                    # Filename and folder matched separately
                    filename, folder = path_match.groups()
                    if 'di folder' in user_input.lower() or 'in folder' in user_input.lower():
                        # "file.txt di folder /path" format
                        params['path'] = os.path.join(folder, filename)
                    else:
                        # "folder/file.txt" format
                        params['path'] = os.path.join(path_match.group(1), path_match.group(2))
                break
        
        # If no path found, look for standalone filenames
        if 'path' not in params:
            file_patterns = [
                r'([A-Za-z_][A-Za-z0-9_.-]*\.[A-Za-z0-9]+)',  # Standard filenames
                r'([A-Z_][A-Z0-9_]*\.md)',                     # ALL_CAPS.md files  
                r'((?:config|readme)\.[A-Za-z]+)',                        # config.* or readme.* files
                r'([Rr]eadme\.[A-Za-z]+)',                     # README files
            ]
            
            for pattern in file_patterns:
                file_match = re.search(pattern, user_input)
                if file_match:
                    params['path'] = file_match.group(1)
                    break
        
        # If still no file found, try extracting from common phrases
        if 'path' not in params:
            content_patterns = [
                r'edit ([A-Za-z0-9_.-]+)',
                r'ubah ([A-Za-z0-9_.-]+)',
                r'modify ([A-Za-z0-9_.-]+)',
                r'update ([A-Za-z0-9_.-]+)',
                r'ganti isi ([A-Za-z0-9_.-]+)',
                r'change ([A-Za-z0-9_.-]+)',
            ]
            
            for pattern in content_patterns:
                match = re.search(pattern, user_input)
                if match:
                    filename = match.group(1)
                    # Add common extension if missing
                    if '.' not in filename:
                        if any(word in user_input.lower() for word in ['code', 'script', 'program']):
                            filename += '.py'
                        elif any(word in user_input.lower() for word in ['doc', 'guide', 'readme']):
                            filename += '.md'
                        elif 'config' in filename.lower():
                            filename += '.py'
                        elif 'readme' in filename.lower():
                            filename += '.md'
                        else:
                            filename += '.py'
                    params['path'] = filename
                    break
        
        # Extract editor preference if specified
        editor_patterns = [
            r'(?:with|using|in)\s+(nano|vim|vi|code|vscode)',
            r'(?:pakai|gunakan)\s+(nano|vim|vi|code|vscode)',
        ]
        
        for pattern in editor_patterns:
            editor_match = re.search(pattern, user_input, re.IGNORECASE)
            if editor_match:
                params['editor'] = editor_match.group(1).lower()
                if params['editor'] in ['vscode', 'code']:
                    params['editor'] = 'code'
                break
        
        return params

    def _extract_file_write_params(self, user_input: str) -> Dict:
        """Extract parameters for file_write tool."""
        import re
        import os
        params = {}
        
        # First, try to extract full paths (absolute or relative with folder)
        path_patterns = [
            r'([~/]?[A-Za-z0-9_./\\-]+/[A-Za-z0-9_.-]+\.[A-Za-z0-9]+)',  # Full paths with folders
            r'([A-Za-z0-9_.-]+\.[A-Za-z0-9]+)\s+(?:di|in|to)\s+(?:folder\s+)?([~/]?[A-Za-z0-9_./\\-]+)',  # "file.txt di folder /path"
            r'(?:folder\s+)?([~/]?[A-Za-z0-9_./\\-]+)/([A-Za-z0-9_.-]+\.[A-Za-z0-9]+)',  # "folder /path/file.txt"
        ]
        
        for pattern in path_patterns:
            path_match = re.search(pattern, user_input, re.IGNORECASE)
            if path_match:
                if len(path_match.groups()) == 1:
                    # Full path matched
                    params['path'] = path_match.group(1)
                elif len(path_match.groups()) == 2:
                    # Filename and folder matched separately
                    filename, folder = path_match.groups()
                    if 'di folder' in user_input.lower() or 'in folder' in user_input.lower() or 'to folder' in user_input.lower():
                        # "file.txt di folder /path" format
                        params['path'] = os.path.join(folder, filename)
                    else:
                        # "folder/file.txt" format
                        params['path'] = os.path.join(path_match.group(1), path_match.group(2))
                break
        
        # If no path found, look for standalone filenames
        if 'path' not in params:
            file_patterns = [
                r'(?:buat|create|write|tulis|simpan|save).*?([A-Za-z_][A-Za-z0-9_.-]*\.[A-Za-z0-9]+)',  # "buat file test.py"
                r'(?:file|berkas)\s+([A-Za-z_][A-Za-z0-9_.-]*\.[A-Za-z0-9]+)',  # "file test.py"
                r'([A-Za-z_][A-Za-z0-9_.-]*\.[A-Za-z0-9]+)',  # standalone filename
            ]
            
            for pattern in file_patterns:
                file_match = re.search(pattern, user_input, re.IGNORECASE)
                if file_match:
                    params['path'] = file_match.group(1)
                    break
        
        # Extract content if specified
        content_patterns = [
            r'(?:isi|content|dengan|with)[\s:]+["\']([^"\']+)["\']',  # "isi 'hello world'"
            r'(?:isi|content|dengan|with)[\s:]+([^\n]+)',  # "isi hello world"
            r'tambahkan[\s:]+["\']([^"\']+)["\']',  # "tambahkan 'hello'"
            r'tambahkan[\s:]+([^\n]+)',  # "tambahkan hello"
            r'add[\s:]+["\']([^"\']+)["\']',  # "add 'content'"
            r'add[\s:]+([^\n]+)',  # "add content"
        ]
        
        for pattern in content_patterns:
            content_match = re.search(pattern, user_input, re.IGNORECASE)
            if content_match:
                params['content'] = content_match.group(1).strip()
                break
        
        # If no content specified, set empty content for file creation
        if 'content' not in params:
            if any(word in user_input.lower() for word in ['buat', 'create']):
                params['content'] = ""  # Empty file for creation
        
        # Check for backup preference
        if any(phrase in user_input.lower() for phrase in ['backup', 'cadangan']):
            params['backup'] = True
        
        return params