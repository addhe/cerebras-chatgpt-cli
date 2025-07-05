"""Custom exceptions for Cerebras CLI."""


class CerebrasCliError(Exception):
    """Base exception for Cerebras CLI."""
    
    def __init__(self, message: str, details: str = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


# Alias for backward compatibility and consistency
CerebrasError = CerebrasCliError


class APIError(CerebrasCliError):
    """API related errors."""
    
    def __init__(self, message: str, status_code: int = None, details: str = None) -> None:
        super().__init__(message, details)
        self.status_code = status_code


class ConfigurationError(CerebrasCliError):
    """Configuration related errors."""
    pass


class ValidationError(CerebrasCliError):
    """Input validation errors."""
    pass


class AuthenticationError(CerebrasCliError):
    """Authentication related errors."""
    pass


class ToolExecutionError(CerebrasCliError):
    """Tool execution errors."""
    
    def __init__(self, message: str, tool_name: str = None, details: str = None) -> None:
        super().__init__(message, details)
        self.tool_name = tool_name


class FileOperationError(CerebrasCliError):
    """File operation errors."""
    
    def __init__(self, message: str, file_path: str = None, details: str = None) -> None:
        super().__init__(message, details)
        self.file_path = file_path
