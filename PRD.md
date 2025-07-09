# Cerebras CLI - Product Requirements Document (PRD)

## Project Overview

**Project Name**: Cerebras CLI  
**Version**: 1.0.0  
**Date**: July 5, 2025  
**Author**: Addhe Warman Putra (Awan)

### Executive Summary

Cerebras CLI adalah command-line interface tool yang memungkinkan interaksi dengan Cerebras AI models melalui terminal dalam format REPL (Read-Eval-Print Loop). Tool ini terinspirasi dari Gemini CLI dan dirancang untuk memberikan pengalaman developer yang optimal dengan Python ecosystem.

## Goals & Objectives

### Primary Goals
1. **Seamless AI Integration**: Menyediakan interface yang mudah untuk berinteraksi dengan Cerebras AI models
2. **Developer Experience**: Memberikan pengalaman yang intuitif dan produktif untuk developers
3. **Extensibility**: Arsitektur yang modular dan dapat dikembangkan dengan tools tambahan
4. **Performance**: Optimized untuk response time dan resource usage

### Success Metrics
- **Usability**: User dapat mulai menggunakan tool dalam < 2 menit setelah instalasi
- **Performance**: Response time < 3 detik untuk query standar
- **Reliability**: 99%+ uptime untuk local operations
- **Extensibility**: Mudah menambah tools baru dalam < 1 jam development time

## Target Users

### Primary Users
- **Python Developers**: Yang ingin mengintegrasikan AI dalam workflow mereka
- **Data Scientists**: Untuk exploratory analysis dan prototyping
- **DevOps Engineers**: Untuk automation dan scripting tasks
- **Students & Researchers**: Untuk learning dan experimentation

### User Personas
1. **Alex (Senior Python Developer)**
   - Needs: Code generation, documentation, debugging assistance
   - Pain points: Context switching between IDE dan web interfaces
   
2. **Sarah (Data Scientist)**
   - Needs: Data analysis, visualization suggestions, code optimization
   - Pain points: Repetitive coding tasks, complex query formulation

## Core Features

### 1. Interactive REPL Mode
- **Description**: Real-time conversation interface dalam terminal
- **Features**:
  - Syntax highlighting untuk input
  - History navigation (up/down arrows)
  - Multi-line input support
  - Session persistence
- **Priority**: P0 (Must Have)

### 2. Command System
- **Slash Commands** (`/command`):
  - `/help` - Show available commands
  - `/clear` - Clear screen dan conversation history
  - `/history` - Show conversation history
  - `/save <filename>` - Save conversation to file
  - `/load <filename>` - Load conversation from file
  - `/config` - Show current configuration
  - `/models` - List available models
  - `/tokens` - Show token usage statistics
- **Priority**: P0 (Must Have)

### 3. File Operations
- **At Commands** (`@filename`):
  - `@file.py` - Include file content in context
  - `@folder/` - Include directory listing
  - `@*.py` - Include multiple files with glob patterns
- **Features**:
  - Smart content chunking untuk large files
  - Binary file detection dan handling
  - Gitignore respect untuk directory operations
- **Priority**: P1 (Should Have)

### 4. Configuration Management
- **Hierarchical Configuration**:
  1. Default values (hardcoded)
  2. Global config (`~/.cerebras-cli/config.yaml`)
  3. Project config (`.cerebras-cli/config.yaml`)
  4. Environment variables
  5. Command-line arguments
- **Configurable Settings**:
  - API key dan endpoint
  - Default model selection
  - Output formatting options
  - Token limits dan safety settings
  - Custom system prompts
- **Priority**: P0 (Must Have)

### 5. Tools System
- **🤖 Automatic Tool Detection**:
  - **Smart Pattern Recognition**: AI detects tool needs from natural language
  - **Multi-Language Support**: Indonesian and English query processing
  - **Parameter Extraction**: Auto-parses paths, patterns, and flags
  - **Context Integration**: Tool results integrated into AI responses
  - **Visual Feedback**: Clear indicators for tool execution status
- **Built-in Tools**:
  - **File System Tools**: `file_read`, `file_write`, `file_list`, `file_edit`
  - **Shell Tools**: `shell_exec`, `directory`
  - **Code Tools**: `code_analyze`, `python_exec`
- **Tool Framework**:
  - Plugin architecture untuk custom tools
  - Tool confirmation untuk destructive operations
  - Async execution support
  - Error handling dan recovery
  - Automatic tool orchestration
- **Natural Language Examples**:
  - "ada berapa file .py di folder ini?" → auto `file_list` with `*.py` pattern
  - "list files in current directory" → auto `file_list`
  - "berapa file di folder /tmp?" → auto `file_list` with `/tmp` path
  - "apa isi dari config.py?" → auto `file_read` with file content display
  - "apa isi dari file testing_file.txt di folder /tmp ?" → auto `file_read` with absolute path
  - "baca file /tmp/testing_file.txt" → auto `file_read` with full path extraction
  - "edit config.py menggunakan nano" → auto `file_edit` with nano editor
  - "ubah README.md dengan vim" → auto `file_edit` with vim editor
  - "buat file test_new.py dengan isi 'print(\"Hello World\")'" → auto `file_write` with content
  - "create file hello.txt with content hello world" → auto `file_write` with English
  - "create file test_absolute.txt in folder /tmp with content test123" → auto `file_write` with absolute path
- **Priority**: P0 (Must Have) ✅ **IMPLEMENTED**

### 6. Context Management
- **Smart Context**:
  - Automatic file discovery based on query
  - Project structure understanding
  - Git integration untuk recent changes
  - Dependency analysis
- **Memory System**:
  - Session memory untuk ongoing conversations
  - Project memory untuk long-term context
  - Semantic search dalam conversation history
- **Priority**: P1 (Should Have)

### 7. Authentication & Security
- **API Key Management**:
  - Secure storage dengan keyring integration
  - Multiple API key support
  - Automatic key rotation
- **Security Features**:
  - Sandbox mode untuk code execution
  - Permission prompts untuk file operations
  - Audit logging untuk sensitive operations
- **Priority**: P0 (Must Have)

## Technical Specifications

### Architecture

#### Core Components
1. **CLI Interface** (`cerebras_cli/cli/`)
   - Command parsing dan routing
   - REPL implementation
   - User interaction handling

2. **Core Engine** (`cerebras_cli/core/`)
   - Cerebras API integration
   - Session management
   - Configuration handling

3. **Tools System** (`cerebras_cli/tools/`)
   - Built-in tools implementation
   - Plugin loader dan manager
   - Tool execution framework
   - **🤖 Automatic Detection Engine**

4. **Utils & Helpers** (`cerebras_cli/utils/`)
   - File operations
   - Text processing
   - Formatting utilities

### 🤖 Automatic Tool Detection System

#### Pattern Recognition Engine
- **Regex-based Matching**: Detects intent from natural language queries
- **Multi-Language Processing**: Supports Indonesian and English patterns
- **Context-Aware Parsing**: Understands project structure and user context

#### Supported Detection Patterns
```python
# File operation patterns
- r'berapa.*file.*\.py'     → file_list with *.py pattern
- r'list.*file'             → file_list tool
- r'ada berapa.*file'       → file_list tool
- r'count.*file'            → file_list tool
- r'show.*file'             → file_list tool

# File reading patterns (with absolute path support)
- r'apa.*isi.*dari.*\.[\w]+' → file_read tool
- r'baca.*\.[\w]+'          → file_read tool
- r'show.*content.*\.[\w]+' → file_read tool
- r'([A-Za-z0-9_.-]+\.[A-Za-z0-9]+)\s+(?:di|in|from)\s+(?:folder\s+)?([~/]?[A-Za-z0-9_./\\-]+)'
                            → extracts "file.txt di folder /path"

# File writing patterns (NEW - July 2025)
- r'buat.*file.*\.[\w]+'    → file_write tool
- r'create.*file.*\.[\w]+'  → file_write tool
- r'write.*to.*\.[\w]+'     → file_write tool
- r'tulis.*ke.*\.[\w]+'     → file_write tool
- r'simpan.*ke.*\.[\w]+'    → file_write tool

# File editing patterns
- r'edit.*\.[\w]+'          → file_edit tool
- r'ubah.*\.[\w]+'          → file_edit tool  
- r'modify.*\.[\w]+'        → file_edit tool
- r'ganti.*isi.*\.[\w]+'    → file_edit tool

# Path extraction patterns (ENHANCED)
- r'/[\w/]+'                → automatic path parameter
- r'\.py|\.js|\.txt'        → automatic pattern parameter
- r'subfolder|recursive'    → automatic recursive flag
- r'nano|vim|code'          → automatic editor preference
- r'([~/]?[A-Za-z0-9_./\\-]+/[A-Za-z0-9_.-]+\.[A-Za-z0-9]+)'
                            → full absolute/relative paths
```

#### Parameter Extraction Logic (ENHANCED)
1. **Path Detection**: Automatically extracts paths like `/tmp`, `./src`, **absolute paths**
2. **Pattern Matching**: Detects file extensions and sets appropriate filters
3. **Flag Recognition**: Identifies recursive, hidden file options
4. **Editor Preference**: Detects editor choice (nano, vim, code, subl)
5. **File Detection**: Extracts specific filenames from natural language
6. **Content Extraction**: NEW - Extracts content for file writing operations
7. **Folder Context**: NEW - Handles "file X di folder Y" patterns
8. **Smart Defaults**: Applies sensible defaults when parameters are missing

#### Integration Flow
```
User Input → Pattern Matching → Parameter Extraction → Tool Execution → Result Integration → AI Response
```

#### Visual Feedback System
- `🔧 Auto-detecting: Using [tool_name] tool...` - Shows detection in progress
- `✓ Tool result: [summary]` - Shows successful execution
- `⚠ Tool failed: [error]` - Shows failure with graceful degradation

### Technology Stack

#### Core Dependencies
- **Python 3.9+**: Base language
- **Click**: Command-line interface framework
- **Rich**: Terminal UI dan formatting
- **Asyncio**: Asynchronous operations
- **Pydantic**: Configuration dan data validation
- **AIOHTTP**: HTTP client untuk API calls
- **PyYAML**: Configuration file parsing

#### Optional Dependencies
- **Keyring**: Secure credential storage
- **GitPython**: Git integration
- **Pygments**: Syntax highlighting
- **Prompt-toolkit**: Advanced input handling
- **Typer**: Alternative CLI framework (evaluation)

#### Development Dependencies
- **Pytest**: Testing framework
- **Black**: Code formatting
- **Flake8**: Linting
- **MyPy**: Type checking
- **Pre-commit**: Git hooks

### API Integration

#### Cerebras API
- **Authentication**: API key based
- **Models Support**: 
  - llama-4-scout-17b-16e-instruct (default)
  - Custom model selection
- **Features**:
  - Streaming responses
  - Token usage tracking
  - Error handling dan retries
  - Rate limiting respect

#### Future API Support
- **OpenAI API**: Compatibility layer
- **Local Models**: Ollama integration
- **Custom Endpoints**: Generic API support

## User Experience Design

### Installation Experience
```bash
# Simple pip install
pip install cerebras-cli

# First-time setup
cerebras-cli setup

# Immediate usage
cerebras-cli
```

### Daily Usage Flow
```bash
# Start interactive session
$ cerebras-cli
🧠 Cerebras CLI v1.0.0
Type /help for commands, Ctrl+C to exit

> @myproject.py
[Including myproject.py in context...]

> Explain this code and suggest improvements

[AI Response with syntax highlighting...]

> /save code-review.md
[Conversation saved to code-review.md]

> exit
```

### Command-line Usage
```bash
# Non-interactive mode
cerebras-cli -p "Explain this error" @error.log

# Pipe integration
cat myfile.py | cerebras-cli -p "Review this code"

# Configuration
cerebras-cli config set model llama-4-scout-17b
cerebras-cli config get api-key
```

## Implementation Phases

### Phase 1: Core Foundation (Weeks 1-2)
- [x] Basic CLI structure dengan Click
- [x] Cerebras API integration
- [x] Simple REPL implementation
- [ ] Configuration system
- [ ] Basic error handling
- [ ] Unit tests foundation

### Phase 2: Enhanced Features (Weeks 3-4)
- [ ] Command system implementation
- [ ] File operations (@filename support)
- [ ] History management
- [ ] Rich terminal UI integration
- [ ] Comprehensive testing

### Phase 3: Tools & Advanced Features (Weeks 5-6)
- [ ] Tools framework implementation
- [ ] Built-in tools development
- [ ] Context management system
- [ ] Plugin architecture
- [ ] Performance optimization

### Phase 4: Polish & Documentation (Week 7)
- [ ] Documentation writing
- [ ] User experience refinement
- [ ] Security audit
- [ ] Release preparation
- [ ] CI/CD pipeline

## Success Criteria

### Functional Requirements
- ✅ **F1**: User dapat memulai conversation dengan AI model
- ⏳ **F2**: User dapat menggunakan slash commands
- ⏳ **F3**: User dapat include files dalam context
- ⏳ **F4**: User dapat save/load conversations
- ⏳ **F5**: User dapat configure settings
- ⏳ **F6**: User dapat menggunakan built-in tools

### Non-Functional Requirements
- ⏳ **NF1**: Startup time < 2 seconds
- ⏳ **NF2**: Memory usage < 100MB untuk normal usage
- ⏳ **NF3**: Support untuk files up to 10MB
- ⏳ **NF4**: Cross-platform compatibility (Windows, macOS, Linux)
- ⏳ **NF5**: Graceful error handling dan recovery

## Risk Assessment

### Technical Risks
1. **API Rate Limits**: 
   - Risk: High usage hitting Cerebras API limits
   - Mitigation: Implement client-side rate limiting
   
2. **Large File Handling**: 
   - Risk: Memory issues dengan large codebases
   - Mitigation: Streaming dan chunking strategies
   
3. **Security Vulnerabilities**: 
   - Risk: Code execution dalam tools
   - Mitigation: Sandbox mode dan permission system

### Business Risks
1. **API Cost**: 
   - Risk: High token usage costs
   - Mitigation: Token tracking dan usage warnings
   
2. **Competition**: 
   - Risk: Similar tools dengan better features
   - Mitigation: Focus pada unique value propositions

## Implementation Status ✅

### ✅ Version 1.0 (COMPLETED - July 2025)
- [x] ✅ Interactive REPL Mode with Rich terminal UI
- [x] ✅ Configuration Management (YAML + environment variables)
- [x] ✅ File Operations with @filename syntax
- [x] ✅ Command System with comprehensive slash commands
- [x] ✅ Tools System with 8 built-in tools (file, shell, code categories)
  - [x] ✅ File Operations: read, write, list, **edit** with external editors
  - [x] ✅ Shell Operations: command execution, directory management  
  - [x] ✅ Code Operations: analysis, Python execution
- [x] ✅ **🤖 Automatic Tool Detection** - Revolutionary AI-powered feature
  - [x] ✅ Smart pattern recognition from natural language
  - [x] ✅ Multi-language support (Indonesian + English)
  - [x] ✅ Automatic parameter extraction with **absolute path support**
  - [x] ✅ Tool result integration into AI responses
  - [x] ✅ Visual feedback and status indicators
- [x] ✅ Authentication & Security with API key management
- [x] ✅ Error Handling with graceful recovery
- [x] ✅ Async Architecture for high performance
- [x] ✅ Backward compatibility with legacy CLI
- [x] ✅ Complete test suite and validation

## Future Roadmap

### Version 1.1 (Next Release - 2-3 months)
- Advanced shell command detection and execution
- Python code execution from natural language
- Plugin architecture for external tools
- Advanced file operations (search, replace, diff)
- Git integration tools
- Token usage tracking and analytics
- Tab completion in REPL
- Conversation history persistence

### Version 1.2 (6 months)
- Multi-model support (OpenAI, Claude, etc.)
- Web interface companion
- Team collaboration features
- Advanced code analysis and generation
- Integration dengan popular IDEs

### Version 2.0 (12 months)
- Local model support
- Advanced AI agents
- Custom training integration
- Marketplace untuk community tools

## Conclusion

Cerebras CLI akan menjadi tool yang powerful untuk developers yang ingin mengintegrasikan AI dalam daily workflow mereka. Dengan fokus pada developer experience, extensibility, dan performance, tool ini akan menyediakan foundation yang solid untuk AI-assisted development.

The modular architecture akan memungkinkan rapid iteration dan community contributions, sementara robust configuration system akan memastikan flexibility untuk berbagai use cases.
