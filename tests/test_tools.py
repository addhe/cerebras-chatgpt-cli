"""Tests for the tools system."""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from cerebras_cli.tools import (
    Tool, ToolRegistry, ToolError, ToolParameter, ToolResult,
    FileReadTool, FileWriteTool, FileListTool,
    ShellCommandTool, DirectoryTool,
    CodeAnalysisTool, PythonExecuteTool
)


class TestToolParameter:
    """Test ToolParameter class."""
    
    def test_required_parameter_validation(self):
        """Test required parameter validation."""
        param = ToolParameter("test_param", str, "Test parameter", required=True)
        
        # Should raise error for None
        with pytest.raises(Exception):
            param.validate(None)
        
        # Should convert valid values
        assert param.validate("test") == "test"
        assert param.validate(123) == "123"
    
    def test_optional_parameter_validation(self):
        """Test optional parameter validation."""
        param = ToolParameter("test_param", str, "Test parameter", required=False, default="default")
        
        # Should return default for None
        assert param.validate(None) == "default"
        
        # Should convert valid values
        assert param.validate("test") == "test"


class TestToolResult:
    """Test ToolResult class."""
    
    def test_successful_result(self):
        """Test successful result creation."""
        result = ToolResult(success=True, data="test data")
        
        assert result.success is True
        assert result.data == "test data"
        assert result.error is None
        
        result_dict = result.to_dict()
        assert result_dict['success'] is True
        assert result_dict['data'] == "test data"
    
    def test_failed_result(self):
        """Test failed result creation."""
        result = ToolResult(success=False, error="test error")
        
        assert result.success is False
        assert result.error == "test error"
        assert result.data is None


class TestToolRegistry:
    """Test ToolRegistry class."""
    
    @pytest.fixture
    def registry(self):
        """Create a test registry."""
        return ToolRegistry()
    
    @pytest.fixture
    def mock_tool(self):
        """Create a mock tool."""
        tool = Mock(spec=Tool)
        tool.name = "test_tool"
        tool.category = "test"
        tool.description = "Test tool"
        tool.validate_parameters.return_value = {}
        return tool
    
    def test_register_tool(self, registry, mock_tool):
        """Test tool registration."""
        registry.register(mock_tool)
        
        assert registry.get_tool("test_tool") == mock_tool
        assert "test_tool" in registry.list_tools()
        assert "test" in registry.list_categories()
    
    def test_unregister_tool(self, registry, mock_tool):
        """Test tool unregistration."""
        registry.register(mock_tool)
        assert registry.unregister("test_tool") is True
        assert registry.get_tool("test_tool") is None
        assert registry.unregister("nonexistent") is False
    
    @pytest.mark.asyncio
    async def test_execute_tool(self, registry, mock_tool):
        """Test tool execution through registry."""
        mock_result = ToolResult(success=True, data="test")
        mock_tool.execute.return_value = mock_result
        
        registry.register(mock_tool)
        result = await registry.execute_tool("test_tool", param1="value1")
        
        assert result == mock_result
        mock_tool.validate_parameters.assert_called_once_with({"param1": "value1"})
        mock_tool.execute.assert_called_once()


class TestFileTools:
    """Test file manipulation tools."""
    
    @pytest.mark.asyncio
    async def test_file_read_tool(self):
        """Test file reading tool."""
        from pathlib import Path
        tool = FileReadTool()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test content\nLine 2")
            temp_path = f.name
        
        try:
            resolved_path = Path(temp_path).resolve()
            result = await tool.execute(path=temp_path)
            assert result.success is True
            assert "Test content\nLine 2" in result.data
            assert result.metadata['path'] == str(resolved_path)
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_file_read_nonexistent(self):
        """Test reading nonexistent file."""
        tool = FileReadTool()
        result = await tool.execute(path="/nonexistent/file.txt")
        
        assert result.success is False
        assert "not found" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_file_write_tool(self):
        """Test file writing tool."""
        tool = FileWriteTool()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.txt")
            content = "Test content\nLine 2"
            
            result = await tool.execute(path=file_path, content=content)
            assert result.success is True
            
            # Verify file was written
            with open(file_path, 'r') as f:
                assert f.read() == content
    
    @pytest.mark.asyncio
    async def test_file_list_tool(self):
        """Test directory listing tool."""
        tool = FileListTool()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            (Path(temp_dir) / "file1.txt").write_text("content1")
            (Path(temp_dir) / "file2.py").write_text("print('hello')")
            (Path(temp_dir) / "subdir").mkdir()
            
            result = await tool.execute(path=temp_dir)
            assert result.success is True
            assert len(result.data) == 3
            
            file_names = [item['name'] for item in result.data]
            assert "file1.txt" in file_names
            assert "file2.py" in file_names
            assert "subdir" in file_names


class TestShellTools:
    """Test shell command tools."""
    
    @pytest.mark.asyncio
    async def test_shell_command_tool(self):
        """Test shell command execution."""
        tool = ShellCommandTool()
        
        # Test simple command
        result = await tool.execute(command="echo 'Hello World'")
        assert result.success is True
        assert "Hello World" in result.data['stdout']
        assert result.data['returncode'] == 0
    
    @pytest.mark.asyncio
    async def test_shell_command_error(self):
        """Test shell command with error."""
        tool = ShellCommandTool()
        
        # Test command that should fail
        result = await tool.execute(command="false")  # Command that returns 1
        assert result.success is False
        assert result.data['returncode'] == 1
    
    @pytest.mark.asyncio
    async def test_directory_tool_operations(self):
        """Test directory operations."""
        tool = DirectoryTool()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = os.path.join(temp_dir, "test_subdir")
            
            # Test create
            result = await tool.execute(operation="create", path=test_dir)
            assert result.success is True
            assert os.path.exists(test_dir)
            
            # Test current directory
            result = await tool.execute(operation="current")
            assert result.success is True
            assert isinstance(result.data, str)
            
            # Test remove
            result = await tool.execute(operation="remove", path=test_dir)
            assert result.success is True
            assert not os.path.exists(test_dir)


class TestCodeTools:
    """Test code analysis and execution tools."""
    
    @pytest.mark.asyncio
    async def test_code_analysis_tool(self):
        """Test code analysis."""
        tool = CodeAnalysisTool()
        
        test_code = '''
def hello_world(name="World"):
    """Say hello to someone."""
    return f"Hello, {name}!"

class TestClass:
    """A test class."""
    
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        return self.value

import os
from pathlib import Path
'''
        
        result = await tool.execute(code=test_code)
        assert result.success is True
        
        analysis = result.data
        assert analysis['syntax_valid'] is True
        assert len(analysis['functions']) >= 1
        assert len(analysis['classes']) >= 1
        assert len(analysis['imports']) >= 2
        
        # Check function details
        hello_func = next((f for f in analysis['functions'] if f['name'] == 'hello_world'), None)
        assert hello_func is not None
        assert 'name' in hello_func['args']
    
    @pytest.mark.asyncio
    async def test_code_analysis_syntax_error(self):
        """Test code analysis with syntax error."""
        tool = CodeAnalysisTool()
        
        invalid_code = "def broken_function(\n    pass"  # Missing closing parenthesis
        
        result = await tool.execute(code=invalid_code)
        assert result.success is True  # Analysis completes even with syntax errors
        
        analysis = result.data
        assert analysis['syntax_valid'] is False
        assert len(analysis['syntax_errors']) > 0
    
    @pytest.mark.asyncio
    async def test_python_execute_tool(self):
        """Test Python code execution."""
        tool = PythonExecuteTool()
        
        test_code = '''
x = 10
y = 20
result = x + y
print(f"Result: {result}")
'''
        
        result = await tool.execute(code=test_code)
        assert result.success is True
        assert "Result: 30" in result.data['stdout']
        assert result.data['locals']['result'] == 30
    
    @pytest.mark.asyncio
    async def test_python_execute_error(self):
        """Test Python execution with error."""
        tool = PythonExecuteTool()
        
        error_code = "undefined_variable + 1"
        
        result = await tool.execute(code=error_code)
        assert result.success is False
        assert "NameError" in result.error
    
    @pytest.mark.asyncio
    async def test_python_execute_dangerous_code(self):
        """Test Python execution blocks dangerous code."""
        tool = PythonExecuteTool()
        
        dangerous_code = "import os; os.system('rm -rf /')"
        
        result = await tool.execute(code=dangerous_code)
        assert result.success is False
        assert "dangerous" in result.error.lower()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
