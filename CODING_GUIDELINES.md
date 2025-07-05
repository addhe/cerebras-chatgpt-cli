# Cerebras CLI - Coding Style Guidelines

## Overview

This document outlines the coding standards and conventions for the Cerebras CLI project. These guidelines ensure code consistency, readability, and maintainability across the entire codebase.

## General Principles

### 1. Code Quality
- **Clarity over cleverness**: Write code that is easy to understand
- **Consistency**: Follow established patterns throughout the codebase
- **Simplicity**: Prefer simple solutions over complex ones
- **Documentation**: Code should be self-documenting, with comments for complex logic

### 2. Python Version
- **Target**: Python 3.9+ (for better type hints and asyncio features)
- **Compatibility**: Maintain backward compatibility where possible
- **Future**: Prepare for Python 3.12+ features

## Code Formatting

### 1. Code Formatter: Black
```bash
# Install black
pip install black

# Format code
black .

# Check formatting
black --check .
```

**Configuration** (`.black` or `pyproject.toml`):
```toml
[tool.black]
line-length = 88
target-version = ['py39']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.mypy_cache
  | \.pytest_cache
  | \.venv
  | build
  | dist
)/
'''
```

### 2. Import Organization
Use **isort** for consistent import ordering:

```python
# Standard library imports
import os
import sys
from typing import Dict, List, Optional

# Third-party imports
import click
import yaml
from rich.console import Console

# Local application imports
from cerebras_cli.core import Client
from cerebras_cli.utils import helpers
```

**Configuration** (`.isort.cfg` or `pyproject.toml`):
```toml
[tool.isort]
profile = "black"
line_length = 88
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
```

## Code Style Guidelines

### 1. Naming Conventions

#### Variables and Functions
```python
# Good: snake_case
user_input = "hello"
def generate_response(prompt: str) -> str:
    pass

# Bad: camelCase or other styles
userInput = "hello"  # Avoid
def generateResponse(prompt: str) -> str:  # Avoid
    pass
```

#### Classes
```python
# Good: PascalCase
class CerebrasClient:
    pass

class APIConfiguration:
    pass

# Bad: snake_case
class cerebras_client:  # Avoid
    pass
```

#### Constants
```python
# Good: UPPER_SNAKE_CASE
DEFAULT_MODEL = "llama-4-scout-17b-16e-instruct"
MAX_TOKEN_LIMIT = 4096
API_BASE_URL = "https://api.cerebras.ai"

# Module-level constants in a separate section
```

#### Files and Directories
```python
# Good: snake_case for modules
cerebras_cli/
├── core/
│   ├── client.py
│   ├── session_manager.py
│   └── config_loader.py
├── tools/
│   ├── file_tools.py
│   ├── shell_tools.py
│   └── code_tools.py
└── utils/
    ├── formatters.py
    └── validators.py
```

### 2. Type Hints

**Always use type hints** for better code documentation and IDE support:

```python
from typing import Dict, List, Optional, Union, Any, Callable
from pathlib import Path

# Function signatures
def process_file(
    file_path: Path, 
    encoding: str = "utf-8"
) -> Optional[str]:
    """Process a file and return its content."""
    pass

# Class attributes
class Config:
    api_key: str
    model_name: str
    max_tokens: int = 4096
    temperature: float = 0.7

# Complex types
ResponseHandler = Callable[[str], None]
ConfigDict = Dict[str, Union[str, int, bool]]
```

### 3. Function and Method Structure

#### Function Length
- **Ideal**: 20-30 lines
- **Maximum**: 50 lines
- **Split longer functions** into smaller, focused functions

#### Function Documentation
```python
def generate_response(
    client: CerebrasClient,
    prompt: str,
    history: List[Dict[str, str]],
    stream: bool = False
) -> Optional[str]:
    """Generate AI response using Cerebras API.
    
    Args:
        client: Initialized Cerebras client
        prompt: User input prompt
        history: Conversation history
        stream: Whether to stream the response
        
    Returns:
        Generated response text or None if failed
        
    Raises:
        APIError: If API request fails
        ValidationError: If prompt validation fails
        
    Example:
        >>> client = CerebrasClient(api_key="...")
        >>> response = generate_response(client, "Hello", [])
        >>> print(response)
        "Hello! How can I help you today?"
    """
    pass
```

### 4. Class Structure

```python
class CerebrasClient:
    """Client for interacting with Cerebras API.
    
    Attributes:
        api_key: API authentication key
        base_url: Base API URL
        timeout: Request timeout in seconds
    """
    
    def __init__(
        self, 
        api_key: str, 
        base_url: str = DEFAULT_API_URL,
        timeout: int = 30
    ) -> None:
        """Initialize client with configuration."""
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self) -> "CerebrasClient":
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
    
    # Public methods first
    async def generate_completion(self, prompt: str) -> str:
        """Generate completion for given prompt."""
        pass
    
    async def stream_completion(self, prompt: str) -> AsyncIterator[str]:
        """Stream completion for given prompt."""
        pass
    
    # Private methods last
    async def _make_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to API."""
        pass
    
    def _validate_prompt(self, prompt: str) -> bool:
        """Validate prompt before sending."""
        pass
```

## Error Handling

### 1. Exception Hierarchy
```python
class CerebrasCliError(Exception):
    """Base exception for Cerebras CLI."""
    pass

class APIError(CerebrasCliError):
    """API related errors."""
    pass

class ConfigurationError(CerebrasCliError):
    """Configuration related errors."""
    pass

class ValidationError(CerebrasCliError):
    """Input validation errors."""
    pass
```

### 2. Error Handling Patterns
```python
# Good: Specific exception handling
try:
    response = await client.generate_completion(prompt)
except APIError as e:
    logger.error(f"API error: {e}")
    return None
except ValidationError as e:
    logger.warning(f"Invalid input: {e}")
    raise
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise CerebrasCliError(f"Operation failed: {e}") from e

# Good: Early returns for error cases
def process_input(text: str) -> Optional[str]:
    if not text:
        return None
    
    if len(text) > MAX_LENGTH:
        raise ValidationError(f"Text too long: {len(text)} > {MAX_LENGTH}")
    
    return text.strip()
```

## Async/Await Guidelines

### 1. Async Function Naming
```python
# Good: Clear async operations
async def fetch_completion(prompt: str) -> str:
    pass

async def save_conversation_async(data: Dict[str, Any]) -> None:
    pass

# Avoid: Sync-looking names for async functions
async def get_response(prompt: str) -> str:  # Could be confusing
    pass
```

### 2. Async Patterns
```python
# Good: Proper async context management
async def process_multiple_prompts(prompts: List[str]) -> List[str]:
    async with CerebrasClient(api_key) as client:
        tasks = [client.generate_completion(p) for p in prompts]
        return await asyncio.gather(*tasks)

# Good: Async iteration
async def stream_responses(prompts: List[str]) -> AsyncIterator[str]:
    async with CerebrasClient(api_key) as client:
        for prompt in prompts:
            async for chunk in client.stream_completion(prompt):
                yield chunk
```

## Configuration and Constants

### 1. Configuration Structure
```python
# config/defaults.py
from dataclasses import dataclass
from typing import Optional

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
    char_delay: float = 0.02
    max_history: int = 100
    auto_save: bool = True
    theme: str = "default"

@dataclass
class Config:
    """Main configuration container."""
    api: APIConfig
    cli: CLIConfig
    api_key: Optional[str] = None
    model: str = "llama-4-scout-17b-16e-instruct"
```

### 2. Environment Variables
```python
# config/env.py
import os
from typing import Optional

def get_api_key() -> Optional[str]:
    """Get API key from environment."""
    return os.getenv("CEREBRAS_API_KEY")

def get_model() -> str:
    """Get model name from environment."""
    return os.getenv("CEREBRAS_MODEL", "llama-4-scout-17b-16e-instruct")

def get_config_dir() -> Path:
    """Get configuration directory."""
    default_dir = Path.home() / ".cerebras-cli"
    return Path(os.getenv("CEREBRAS_CLI_CONFIG_DIR", default_dir))
```

## Testing Guidelines

### 1. Test Structure
```python
# tests/test_client.py
import pytest
from unittest.mock import AsyncMock, patch

from cerebras_cli.core.client import CerebrasClient
from cerebras_cli.exceptions import APIError

class TestCerebrasClient:
    """Test cases for CerebrasClient."""
    
    @pytest.fixture
    def client(self) -> CerebrasClient:
        """Create test client."""
        return CerebrasClient(api_key="test-key")
    
    @pytest.mark.asyncio
    async def test_generate_completion_success(self, client):
        """Test successful completion generation."""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {"response": "Hello!"}
            
            result = await client.generate_completion("Hi")
            
            assert result == "Hello!"
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_completion_api_error(self, client):
        """Test API error handling."""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.side_effect = APIError("API failed")
            
            with pytest.raises(APIError):
                await client.generate_completion("Hi")
```

### 2. Test Naming
- **Test files**: `test_*.py`
- **Test classes**: `Test<ClassName>`
- **Test methods**: `test_<functionality>_<condition>`

## Documentation

### 1. Docstring Style (Google Style)
```python
def complex_function(
    param1: str,
    param2: int,
    param3: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Brief description of what the function does.
    
    Longer description with more details about the function's
    behavior, algorithms used, or important implementation notes.
    
    Args:
        param1: Description of param1
        param2: Description of param2  
        param3: Optional description of param3. Defaults to None.
        
    Returns:
        Description of return value and its structure.
        
    Raises:
        ValueError: When param2 is negative
        APIError: When API request fails
        
    Example:
        >>> result = complex_function("test", 42)
        >>> print(result["status"])
        "success"
    """
    pass
```

### 2. Inline Comments
```python
# Good: Explain why, not what
def calculate_tokens(text: str) -> int:
    # Use GPT-4 tokenizer for consistent estimation across models
    # This helps predict costs before making API calls
    return len(text.split()) * 1.3  # Rough approximation factor

# Bad: Explain obvious things  
def calculate_tokens(text: str) -> int:
    words = text.split()  # Split text into words
    return len(words) * 1.3  # Multiply by 1.3
```

## Project Structure

```
cerebras-cli/
├── cerebras_cli/
│   ├── __init__.py
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py          # CLI entry point
│   │   ├── commands.py      # Command definitions
│   │   └── repl.py          # REPL implementation
│   ├── core/
│   │   ├── __init__.py
│   │   ├── client.py        # Cerebras API client
│   │   ├── session.py       # Session management
│   │   ├── config.py        # Configuration handling
│   │   └── context.py       # Context management
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py          # Tool base classes
│   │   ├── file_tools.py    # File operations
│   │   ├── shell_tools.py   # Shell commands
│   │   └── code_tools.py    # Code analysis
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── formatters.py    # Output formatting
│   │   ├── validators.py    # Input validation
│   │   └── helpers.py       # Utility functions
│   └── exceptions.py        # Custom exceptions
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Pytest configuration
│   ├── test_cli/
│   ├── test_core/
│   ├── test_tools/
│   └── test_utils/
├── docs/
│   ├── index.md
│   ├── installation.md
│   ├── usage.md
│   └── api.md
├── scripts/
│   ├── setup.py           # Setup script
│   └── release.py         # Release automation
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── release.yml
├── pyproject.toml         # Project configuration
├── requirements.txt       # Dependencies
├── requirements-dev.txt   # Development dependencies
├── README.md
├── CHANGELOG.md
└── LICENSE
```

## Git Workflow

### 1. Commit Messages
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(cli): add /save command for conversation persistence

fix(client): handle timeout errors gracefully

docs(readme): update installation instructions

test(tools): add unit tests for file operations
```

### 2. Branch Naming
- `feature/description-of-feature`
- `fix/description-of-fix`
- `docs/description-of-docs`
- `refactor/description-of-refactor`

## Performance Guidelines

### 1. Memory Management
```python
# Good: Use generators for large datasets
def process_large_file(file_path: Path) -> Iterator[str]:
    with open(file_path, 'r') as f:
        for line in f:
            yield process_line(line)

# Good: Context managers for resources
async def download_data(url: str) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.read()
```

### 2. Async Best Practices
```python
# Good: Batch operations
async def process_multiple_files(file_paths: List[Path]) -> List[str]:
    async with CerebrasClient() as client:
        # Process in batches to avoid overwhelming the API
        batch_size = 5
        results = []
        
        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i:i + batch_size]
            batch_results = await asyncio.gather(*[
                process_file(client, path) for path in batch
            ])
            results.extend(batch_results)
            
        return results
```

## Security Guidelines

### 1. API Key Handling
```python
# Good: Secure credential storage
import keyring

def store_api_key(api_key: str) -> None:
    """Store API key securely."""
    keyring.set_password("cerebras-cli", "api_key", api_key)

def get_api_key() -> Optional[str]:
    """Retrieve API key securely."""
    return keyring.get_password("cerebras-cli", "api_key")

# Good: Environment variable fallback
def get_api_key_with_fallback() -> Optional[str]:
    """Get API key from keyring or environment."""
    # Try keyring first
    api_key = get_api_key()
    if api_key:
        return api_key
    
    # Fallback to environment variable
    return os.getenv("CEREBRAS_API_KEY")
```

### 2. Input Validation
```python
from pathlib import Path

def validate_file_path(file_path: str) -> Path:
    """Validate and sanitize file path."""
    path = Path(file_path).resolve()
    
    # Prevent directory traversal
    if ".." in path.parts:
        raise ValidationError("Path traversal not allowed")
    
    # Check if file exists and is readable
    if not path.exists():
        raise ValidationError(f"File not found: {path}")
    
    if not path.is_file():
        raise ValidationError(f"Not a file: {path}")
        
    return path
```

## Conclusion

These guidelines ensure that the Cerebras CLI codebase remains maintainable, readable, and consistent. All contributors should follow these standards to maintain code quality and facilitate collaboration.

For questions about these guidelines or suggestions for improvements, please open an issue or discussion in the project repository.
