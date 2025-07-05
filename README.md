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
- **Tools System**: Extensible framework for custom tools
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

### Version 1.1 (Next Release)
- [ ] **Automatic Tool Usage**: AI-driven tool detection and execution
  - [ ] Smart tool detection from user queries
  - [ ] Automatic tool orchestration and result integration
  - [ ] Context-aware tool suggestions
- [ ] Plugin architecture for external tools
- [ ] Advanced file operations (search, replace, diff)
- [ ] Git integration tools
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
- GitHub: [@addheputra](https://github.com/addheputra)

---

⭐ Star this repo if you find it useful!
