# 🧠 Cerebras CLI - AI-Powered Command-Line Interface

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A powerful, modern command-line interface for interacting with Cerebras AI models. Inspired by Gemini CLI and built with Python, this tool provides an intuitive and extensible platform for AI-assisted development workflows.

## ✨ Features

### 🎯 Core Capabilities
- **Interactive REPL Mode**: Real-time conversation with AI models
- **Rich Terminal UI**: Beautiful, syntax-highlighted interface powered by Rich
- **File Operations**: Include files in context with `@filename` syntax
- **Command System**: Powerful slash commands for session management
- **Configuration Management**: Hierarchical configuration with YAML support
- **Async Architecture**: High-performance async operations throughout

### 🛠️ Advanced Features
- **🤖 Automatic Tool Detection**: AI automatically detects when tools are needed and executes them
- **Tools System**: Extensible framework with 7 built-in tools across 3 categories
- **Smart Parameter Extraction**: Auto-parses paths, patterns, and flags from natural language
- **Multi-Language Support**: Works with both Indonesian and English queries
- **Context Management**: Smart file discovery and project understanding
- **Conversation Persistence**: Save and restore chat sessions
- **Multiple Models**: Support for various Cerebras model variants
- **Streaming Responses**: Real-time response streaming with typewriter effect
- **Error Handling**: Graceful error recovery and detailed debugging

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/addheputra/cerebras-chatgpt-cli.git
cd cerebras-chatgpt-cli

# Install dependencies
pip install -r requirements.txt

# Run setup
python -m cerebras_cli.cli.main setup
```

### Quick Setup

1. **Get your Cerebras API key** from [Cerebras Platform](https://cloud.cerebras.ai)

2. **Set your API key**:
   ```bash
   export CEREBRAS_API_KEY="your_api_key_here"
   ```

3. **Start the CLI**:
   ```bash
   # Enhanced CLI (recommended)
   python -m cerebras_cli.cli.main

   # Legacy mode
   python src/main.py

   # Interactive setup
   python -m cerebras_cli.cli.main setup
   ```

## 💡 Usage Examples

### Interactive Mode
```bash
$ python -m cerebras_cli.cli.main
🧠 Cerebras CLI v1.0.0
Type /help for commands, Ctrl+C to exit

> Hello! Can you help me understand Python decorators?

[AI provides detailed explanation]

> @my_code.py Can you review this code and suggest improvements?

[AI analyzes the included file and provides feedback]

> /save code-review-session.md
[Conversation saved successfully]
```

### Configuration
```bash
# Show current config
python -m cerebras_cli.cli.main config show

# Set configuration
python -m cerebras_cli.cli.main config set model llama-3.1-70b-instruct

# Health check
python -m cerebras_cli.cli.main doctor
```

## 📋 Commands Reference

### Slash Commands (Interactive Mode)

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/exit`, `/quit` | Exit the CLI |
| `/clear` | Clear screen and conversation history |
| `/history` | Show conversation history |
| `/save <filename>` | Save conversation to file |
| `/load <filename>` | Load conversation from file |
| `/config` | Show current configuration |
| `/models` | Show available models |
| `/tools` | List available tools |
| `/tool <name> [args]` | Execute a specific tool |

### File Operations

| Syntax | Description |
|--------|-------------|
| `@filename` | Include file content in your message |
| `@*.py` | Include all Python files (use with caution) |

### Tools System

The CLI includes a comprehensive tools system for various operations:

| Tool | Category | Description |
|------|----------|-------------|
| `file_read` | File | Read file contents with syntax highlighting |
| `file_write` | File | Write content to files with backup options |
| `file_list` | File | List directory contents with filtering |
| `shell_exec` | Shell | Execute system commands safely |
| `directory` | Shell | Directory operations (create, remove, etc.) |
| `code_analyze` | Code | Analyze Python code structure |
| `python_exec` | Code | Execute Python code in sandbox |

**Examples:**
```bash
# Read a Python file
/tool file_read path=src/main.py

# Execute a shell command
/tool shell_exec command="git status"

# Analyze code structure
/tool code_analyze code="def hello(): return 'world'"

# Execute Python code safely
/tool python_exec code="print('Hello, World!')"
```

### 🤖 Automatic Tool Detection

**Revolutionary Feature**: The AI automatically detects when tools are needed and executes them!

**Natural Language Examples:**
```bash
# File Operations (AUTO-DETECTED)
> ada berapa file .py di folder ini?
🔧 Auto-detecting: Using file_list tool...
✓ Tool result: Found 26 Python files

> list files in current directory
🔧 Auto-detecting: Using file_list tool...  
✓ Tool result: Found 18 items

> ada berapa file di folder /tmp ?
🔧 Auto-detecting: Using file_list tool...
✓ Tool result: Found 12 items

# Supported Patterns:
- "berapa file .py" → auto file_list with *.py pattern
- "list files" → auto file_list
- "show files recursively" → auto file_list recursive
- "cari file" → auto file_list with search
- "count files" → auto file_list with counting
```

**Multi-Language Support:**
- 🇮🇩 **Indonesian**: "ada berapa file", "cari file", "tampilkan file"
- 🇺🇸 **English**: "how many files", "list files", "show files"

**Smart Parameter Extraction:**
- **Paths**: `/tmp`, `./src` → automatically sets path parameter
- **Patterns**: `.py`, `.js`, `.txt` → automatically sets pattern filter
- **Flags**: "recursive", "subfolder" → automatically enables recursive mode

See [Tools Documentation](docs/tools.md) for complete details.

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CEREBRAS_API_KEY` | Your Cerebras API key | *Required* |
| `CEREBRAS_MODEL` | Model to use | `llama-4-scout-17b-16e-instruct` |
| `CEREBRAS_CHAR_DELAY` | Typewriter delay (seconds) | `0.0` (no delay) |

**Note:** To enable typewriter effect (character-by-character output), set `CEREBRAS_CHAR_DELAY` to a small value like `0.02`:

```bash
export CEREBRAS_CHAR_DELAY=0.02
```

Or configure it in your config file:
```yaml
cli:
  char_delay: 0.02  # Enable typewriter effect
```

### Configuration Files

Example global config (`~/.cerebras-cli/config.yaml`):

```yaml
api:
  timeout: 30
  max_retries: 3

cli:
  char_delay: 0.0  # Set to 0.02 for typewriter effect
  max_history: 100
  theme: "default"

model: "llama-4-scout-17b-16e-instruct"
```

## 🏗️ Architecture

Cerebras CLI follows a modular architecture:

```
cerebras-cli/
├── cerebras_cli/           # New modular CLI
│   ├── cli/               # CLI interface layer
│   │   ├── main.py        # Entry point and argument parsing
│   │   ├── repl.py        # Interactive REPL implementation
│   │   └── commands.py    # Click commands (config, models, etc.)
│   ├── core/              # Core functionality
│   │   ├── config.py      # Configuration management
│   │   └── client.py      # Cerebras API client
│   ├── tools/             # Tools system
│   │   ├── base.py        # Base tool classes
│   │   ├── file_tools.py  # File manipulation tools
│   │   ├── shell_tools.py # Shell command tools
│   │   └── code_tools.py  # Code analysis tools
│   └── exceptions.py      # Custom exceptions
├── src/                   # Legacy CLI (backward compatibility)
│   └── main.py            # Original implementation
├── tests/                 # Test suite
├── docs/                  # Documentation
└── examples/              # Usage examples
```

## 🔌 Plugin Architecture (Coming in v1.1)

### Plugin System Overview

The plugin architecture will enable developers to create and distribute custom tools that integrate seamlessly with Cerebras CLI. This system is designed to be:

- **🔒 Secure**: Sandboxed execution with permission controls
- **📦 Distributable**: Install plugins via PyPI or custom registries
- **🤖 AI-Integrated**: Automatic detection works with custom tools
- **🔧 Standards-Based**: Follows established plugin patterns

### Plugin Structure

```python
# Example plugin: cerebras-cli-docker
from cerebras_cli.tools import Tool, ToolParameter, ToolResult

class DockerTool(Tool):
    @property
    def name(self) -> str:
        return "docker"
    
    @property 
    def description(self) -> str:
        return "Manage Docker containers and images"
    
    @property
    def category(self) -> str:
        return "devops"
    
    def _setup_parameters(self) -> None:
        self.add_parameter(ToolParameter(
            name="action",
            type=str,
            description="Docker action: ps, run, stop, build",
            required=True
        ))
        self.add_parameter(ToolParameter(
            name="image",
            type=str, 
            description="Docker image name",
            required=False
        ))
    
    async def execute(self, action: str, image: str = None) -> ToolResult:
        # Implementation here
        pass

# Plugin registration
def register_plugin():
    return DockerTool()
```

### Plugin Installation

```bash
# Install from PyPI
pip install cerebras-cli-docker

# Install from local directory
pip install ./my-custom-plugin

# Install from Git
pip install git+https://github.com/user/cerebras-cli-plugin.git
```

### Plugin Discovery

```bash
# List available plugins
cerebras-cli plugins list

# Search plugin marketplace  
cerebras-cli plugins search docker

# Install plugin
cerebras-cli plugins install docker

# Enable/disable plugins
cerebras-cli plugins enable docker
cerebras-cli plugins disable docker
```

### AI Integration

Plugins automatically integrate with the AI detection system:

```bash
# Natural language will auto-detect custom tools
> "start a nginx container"
🔧 Auto-detecting: Using docker tool...
✓ Tool result: Container nginx-123 started

> "build my app with docker"  
🔧 Auto-detecting: Using docker tool...
✓ Tool result: Image my-app:latest built successfully
```

### Plugin Categories

**Planned Plugin Categories:**
- **📦 DevOps**: Docker, Kubernetes, AWS, GCP, Azure
- **🔧 Development**: Lint tools, formatters, test runners
- **📊 Data**: Database clients, API clients, data processors  
- **🌐 Web**: HTTP clients, web scrapers, API testing
- **🔐 Security**: Vulnerability scanners, secret detectors
- **📈 Monitoring**: Log analyzers, metric collectors

### Security Model

- **🔒 Sandboxed Execution**: Plugins run in isolated environments
- **✅ Permission System**: Users approve tool capabilities
- **🛡️ Code Signing**: Verified plugins with digital signatures
- **📋 Audit Logging**: All plugin actions are logged
- **⚠️ Safety Checks**: Dangerous operations require confirmation

## 🧪 Development

### Development Setup

```bash
# Clone and setup
git clone https://github.com/addheputra/cerebras-chatgpt-cli.git
cd cerebras-chatgpt-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
```

### Code Quality

```bash
# Format code
black .

# Lint code  
flake8 .

# Type checking
mypy .
```

## 🔧 Troubleshooting

### Common Issues

**API Key Not Set**
```bash
# Set API key
export CEREBRAS_API_KEY="your_key_here"
```

**Import Errors**
```bash
# Install all dependencies
pip install -r requirements.txt

# Check installation
python -m cerebras_cli.cli.main doctor
```

**Output Shows Character-by-Character (Typewriter Effect)**
If you see output like this:
```
H
e
l
l
o
 
W
o
r
l
d
```

This is caused by the character delay setting. To disable it:
```bash
# Disable character delay
export CEREBRAS_CHAR_DELAY=0

# Or check your current config
python -m cerebras_cli config show
```

**Slow Response Time**
```bash
# Increase timeout
export CEREBRAS_TIMEOUT=60

# Or configure in config file
cerebras-cli config set api.timeout 60
```

## 🚦 Roadmap

### ✅ Version 1.0 (Current)
- [x] ✅ Modern CLI architecture with Click
- [x] ✅ Comprehensive tools system (7 tools across 3 categories)
- [x] ✅ Rich terminal interface with syntax highlighting
- [x] ✅ Configuration management (YAML + env variables)
- [x] ✅ Interactive REPL with slash commands
- [x] ✅ Backward compatibility with legacy CLI
- [x] ✅ Complete test suite and validation
- [x] ✅ **Automatic Tool Usage**: AI-driven tool detection and execution
  - [x] ✅ Smart tool detection from user queries
  - [x] ✅ Automatic tool orchestration and result integration
  - [x] ✅ Context-aware tool suggestions
  - [x] ✅ Multi-language support (Indonesian + English)
  - [x] ✅ Smart parameter extraction from natural language

### Version 1.1 (Next Release)
- [ ] **Plugin architecture for external tools**
  - [ ] Dynamic plugin loading from external packages
  - [ ] Plugin marketplace and discovery system
  - [ ] Standardized plugin API and SDK
  - [ ] Plugin validation and sandboxing
- [ ] Advanced file operations (search, replace, diff)
- [ ] Git integration tools
- [ ] Advanced shell command detection and execution
- [ ] Python code execution from natural language
- [ ] Token usage tracking and analytics
- [ ] Tab completion in REPL
- [ ] Conversation history persistence

### Version 1.2 (Future)
- [ ] Multi-model support with easy switching
- [ ] Web interface companion
- [ ] Team collaboration features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by [Gemini CLI](https://github.com/google-gemini/gemini-cli) by Google
- Built with [Cerebras Cloud SDK](https://github.com/Cerebras/cerebras-cloud-sdk-python)
- UI powered by [Rich](https://github.com/Textualize/rich)

## 👨‍💻 Author

**Addhe Warman Putra (Awan)**
- GitHub: [@addheputra](https://github.com/addhe)

---

⭐ Star this repo if you find it useful!
