# Tools System Documentation

The Cerebras CLI includes a comprehensive tools system that allows you to perform various operations directly from the command line interface. This system is inspired by modern AI assistants and provides a plugin-like architecture for extending functionality.

## Table of Contents

- [Overview](#overview)
- [Available Tools](#available-tools)
- [Using Tools in CLI](#using-tools-in-cli)
- [Tool Categories](#tool-categories)
- [Examples](#examples)
- [Extending with Custom Tools](#extending-with-custom-tools)

## Overview

The tools system provides:

- **File Operations**: Read, write, and list files and directories
- **Shell Commands**: Execute system commands safely
- **Code Analysis**: Analyze Python code structure and syntax
- **Code Execution**: Run Python code in a sandboxed environment
- **Extensible Architecture**: Easy to add new tools

## Available Tools

### File Tools

#### `file_read`
Read contents of a file with syntax highlighting support.

**Parameters:**
- `path` (string, required): Path to the file to read
- `encoding` (string, optional): File encoding (default: utf-8)
- `max_size` (int, optional): Maximum file size in bytes (default: 10MB)

**Example:**
```bash
/tool file_read path=config.py
/tool file_read path=data.txt encoding=latin-1
```

#### `file_write`
Write content to a file with optional backup creation.

**Parameters:**
- `path` (string, required): Path to the file to write
- `content` (string, required): Content to write to the file
- `encoding` (string, optional): File encoding (default: utf-8)
- `create_dirs` (bool, optional): Create parent directories (default: true)
- `backup` (bool, optional): Create backup if file exists (default: false)

**Example:**
```bash
/tool file_write path=hello.py content="print('Hello, World!')"
/tool file_write path=data/config.json content='{"debug": true}' create_dirs=true
```

#### `file_list`
List files and directories in a path.

**Parameters:**
- `path` (string, optional): Path to list (default: current directory)
- `recursive` (bool, optional): List recursively (default: false)
- `show_hidden` (bool, optional): Show hidden files (default: false)
- `pattern` (string, optional): Glob pattern to filter files
- `max_depth` (int, optional): Maximum recursion depth (default: 10)

**Example:**
```bash
/tool file_list path=.
/tool file_list path=src recursive=true pattern=*.py
```

### Shell Tools

#### `shell_exec`
Execute shell commands with output capture.

**Parameters:**
- `command` (string, required): Shell command to execute
- `cwd` (string, optional): Working directory for execution
- `timeout` (float, optional): Command timeout in seconds (default: 30)
- `capture_output` (bool, optional): Capture command output (default: true)
- `shell` (bool, optional): Execute through shell (default: true)

**Example:**
```bash
/tool shell_exec command="ls -la"
/tool shell_exec command="git status" cwd=/path/to/repo
```

#### `directory`
Directory operations (create, remove, change).

**Parameters:**
- `operation` (string, required): Operation: 'create', 'remove', 'change', 'current'
- `path` (string, optional): Directory path
- `recursive` (bool, optional): Recursive operation (default: true)
- `force` (bool, optional): Force operation for remove (default: false)

**Example:**
```bash
/tool directory operation=current
/tool directory operation=create path=new_folder
/tool directory operation=remove path=temp_folder force=true
```

### Code Tools

#### `code_analyze`
Analyze Python code structure and syntax.

**Parameters:**
- `code` (string, optional): Python code to analyze
- `file_path` (string, optional): Path to Python file to analyze
- `include_ast` (bool, optional): Include AST dump (default: false)
- `check_syntax` (bool, optional): Check syntax validity (default: true)

**Example:**
```bash
/tool code_analyze code="def hello(): return 'world'"
/tool code_analyze file_path=my_script.py include_ast=true
```

#### `python_exec`
Execute Python code in a controlled environment.

**Parameters:**
- `code` (string, required): Python code to execute
- `timeout` (float, optional): Execution timeout (default: 10 seconds)
- `capture_output` (bool, optional): Capture stdout/stderr (default: true)
- `globals_dict` (dict, optional): Global variables for execution

**Example:**
```bash
/tool python_exec code="print('Hello, World!')"
/tool python_exec code="x = 5; y = 10; print(f'Sum: {x + y}')"
```

## Using Tools in CLI

### Interactive Mode

Start the CLI in interactive mode:
```bash
python -m cerebras_cli
```

### Tool Commands

In the REPL, use the following commands:

#### List all tools:
```bash
/tools
```

#### Get help for a specific tool:
```bash
/tools help file_read
```

#### List tool categories:
```bash
/tools categories
```

#### Execute a tool:
```bash
/tool <tool_name> param1=value1 param2=value2
```

### Parameter Types

The CLI automatically converts parameter values:
- `true/false` → boolean
- Numbers → int/float
- Everything else → string

## Examples

### Working with Files

```bash
# Read a Python file with syntax highlighting
/tool file_read path=src/main.py

# Create a new file
/tool file_write path=hello.py content="print('Hello, Cerebras!')"

# List Python files recursively
/tool file_list path=. recursive=true pattern=*.py

# Backup and modify a file
/tool file_write path=config.py content="DEBUG = True" backup=true
```

### Shell Operations

```bash
# Check git status
/tool shell_exec command="git status"

# Create directory structure
/tool directory operation=create path=src/utils

# Run tests with timeout
/tool shell_exec command="python -m pytest" timeout=60
```

### Code Analysis

```bash
# Analyze a code snippet
/tool code_analyze code="
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"

# Check syntax of a file
/tool code_analyze file_path=my_module.py

# Execute safe code
/tool python_exec code="
import math
result = math.sqrt(16)
print(f'Square root of 16 is {result}')
"
```

### Combining Tools

You can combine tools for complex workflows:

```bash
# 1. Read a configuration file
/tool file_read path=config.json

# 2. Analyze its structure (if it's Python)
/tool code_analyze file_path=config.py

# 3. Create a backup
/tool file_write path=config.py.backup content="..." backup=true

# 4. Test the configuration
/tool python_exec code="
import json
with open('config.json') as f:
    config = json.load(f)
print('Configuration loaded successfully')
"
```

## Tool Categories

### File Category
- **Purpose**: File and directory manipulation
- **Tools**: `file_read`, `file_write`, `file_list`
- **Use Cases**: Reading code files, creating documentation, file management

### Shell Category
- **Purpose**: System command execution
- **Tools**: `shell_exec`, `directory`
- **Use Cases**: Running build commands, git operations, system administration

### Code Category
- **Purpose**: Code analysis and execution
- **Tools**: `code_analyze`, `python_exec`
- **Use Cases**: Code review, testing snippets, educational examples

## Safety Features

### Code Execution Safety
The `python_exec` tool includes several safety measures:
- **Restricted builtins**: Only safe built-in functions are available
- **Dangerous operation detection**: Blocks potentially harmful code
- **Timeout protection**: Prevents infinite loops
- **Sandboxed environment**: Isolated execution context

### File Operation Safety
- **Size limits**: Prevents reading extremely large files
- **Path validation**: Ensures valid file paths
- **Backup options**: Optional backup creation before modifications

### Shell Command Safety
- **Timeout limits**: Prevents long-running commands
- **Output capture**: Controlled output handling
- **Working directory isolation**: Explicit working directory control

## Extending with Custom Tools

The tools system is designed to be extensible. You can create custom tools by:

1. **Inheriting from Tool base class**
2. **Implementing required methods**
3. **Registering with the tool registry**

### Example Custom Tool

```python
from cerebras_cli.tools.base import Tool, ToolParameter, ToolResult

class GitStatusTool(Tool):
    @property
    def name(self) -> str:
        return "git_status"
    
    @property
    def description(self) -> str:
        return "Get Git repository status"
    
    @property
    def category(self) -> str:
        return "git"
    
    def _setup_parameters(self) -> None:
        self.add_parameter(ToolParameter(
            name="path",
            type=str,
            description="Repository path",
            required=False,
            default="."
        ))
    
    async def execute(self, path: str = ".") -> ToolResult:
        # Implementation here
        pass

# Register the tool
from cerebras_cli.tools import default_registry
default_registry.register(GitStatusTool())
```

## Error Handling

Tools provide comprehensive error handling:

- **Validation errors**: Invalid parameters or missing required values
- **Execution errors**: Runtime failures during tool execution
- **Permission errors**: File system or command permission issues
- **Timeout errors**: Operations that exceed time limits

All errors are captured and displayed in a user-friendly format with optional verbose details.

## Performance Considerations

- **File size limits**: Large files are rejected to prevent memory issues
- **Command timeouts**: Shell commands have configurable timeouts
- **Async execution**: All tools use async/await for non-blocking operation
- **Resource cleanup**: Automatic cleanup of temporary resources

## Troubleshooting

### Common Issues

1. **Tool not found**: Check tool name with `/tools`
2. **Parameter errors**: Use `/tools help <tool_name>` for parameter details
3. **Permission denied**: Check file/directory permissions
4. **Command timeout**: Increase timeout parameter for long-running commands

### Verbose Output

Enable verbose mode to see detailed error information:
```bash
python -m cerebras_cli --verbose
```

This will show:
- Full stack traces for errors
- Tool execution metadata
- Detailed timing information
