"""Tests for CLI integration with tools."""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch

from cerebras_cli.cli.repl import REPL, get_lexer_for_file
from cerebras_cli.core.config import Config, APIConfig, CLIConfig
from cerebras_cli.core.client import CerebrasClient


class TestREPLToolIntegration:
    """Test REPL integration with tools system."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock config."""
        config = Mock(spec=Config)
        config.api = Mock(spec=APIConfig)
        config.cli = Mock(spec=CLIConfig)
        config.cli.max_history = 100
        config.cli.char_delay = 0
        config.cli.theme = "dark"
        config.api.timeout = 30
        config.api.max_retries = 3
        config.api_key = "test_key"
        return config
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock client."""
        client = Mock(spec=CerebrasClient)
        client.generate_completion = AsyncMock()
        return client
    
    @pytest.fixture
    def repl(self, mock_client, mock_config):
        """Create a REPL instance."""
        return REPL(mock_client, mock_config)
    
    def test_lexer_detection(self):
        """Test lexer detection for different file types."""
        assert get_lexer_for_file("test.py") == "python"
        assert get_lexer_for_file("test.js") == "javascript"
        assert get_lexer_for_file("test.html") == "html"
        assert get_lexer_for_file("test.unknown") == "text"
    
    @pytest.mark.asyncio
    async def test_tools_command(self, repl):
        """Test /tools command."""
        with patch.object(repl, 'show_tools') as mock_show:
            await repl.handle_command("/tools")
            mock_show.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tool_execution_with_args(self, repl):
        """Test tool execution with arguments."""
        # Mock the tools registry
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = "test output"
        mock_result.metadata = {}
        mock_result.error = None
        
        with patch.object(repl.tools_registry, 'execute_tool', return_value=mock_result) as mock_exec:
            await repl.execute_tool("test_tool", ["arg1=value1", "arg2=true"])
            
            mock_exec.assert_called_once_with("test_tool", arg1="value1", arg2=True)
    
    @pytest.mark.asyncio
    async def test_tool_execution_error(self, repl):
        """Test tool execution with error."""
        mock_result = Mock()
        mock_result.success = False
        mock_result.error = "Test error"
        
        with patch.object(repl.tools_registry, 'execute_tool', return_value=mock_result):
            with patch.object(repl.console, 'print') as mock_print:
                await repl.execute_tool("test_tool", [])
                
                # Check that error was printed
                error_printed = any("failed" in str(call) for call in mock_print.call_args_list)
                assert error_printed
    
    @pytest.mark.asyncio
    async def test_file_tool_integration(self, repl):
        """Test file tool integration with syntax highlighting."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('Hello, World!')")
            temp_path = f.name
        
        try:
            # Test file read with tool
            with patch.object(repl.console, 'print') as mock_print:
                await repl.execute_tool("file_read", [f"path={temp_path}"])
                
                # Should have printed the file content
                assert mock_print.called
        finally:
            os.unlink(temp_path)


class TestCLICommands:
    """Test CLI command integration."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock config."""
        config = Mock(spec=Config)
        config.api = Mock(spec=APIConfig)
        config.cli = Mock(spec=CLIConfig)
        config.cli.max_history = 100
        return config
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock client."""
        return Mock(spec=CerebrasClient)
    
    @pytest.fixture
    def repl(self, mock_client, mock_config):
        """Create a REPL instance."""
        return REPL(mock_client, mock_config)
    
    @pytest.mark.asyncio
    async def test_help_command(self, repl):
        """Test help command shows tool information."""
        with patch.object(repl, 'show_help') as mock_show:
            await repl.handle_command("/help")
            mock_show.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_clear_command(self, repl):
        """Test clear command."""
        # Add some history
        repl.history.add_message("user", "test message")
        assert len(repl.history.messages) == 1
        
        with patch.object(repl.console, 'clear'), patch.object(repl.console, 'print'):
            await repl.handle_command("/clear")
            assert len(repl.history.messages) == 0
    
    @pytest.mark.asyncio
    async def test_exit_command(self, repl):
        """Test exit command."""
        assert repl.running is True
        
        with patch.object(repl.console, 'print'):
            await repl.handle_command("/exit")
            assert repl.running is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
