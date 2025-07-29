import unittest
from unittest.mock import patch, MagicMock
import time
from typing import Any, List, Dict, Optional
import os
import sys

from cerebras.cloud.sdk import Cerebras

import src.main as main_module
from config import MODEL_ID, SYSTEM_MESSAGE, API_KEY, CHAR_DELAY
from src.main import check_new_cli_available

class TestMainModule(unittest.TestCase):

    def setUp(self):
        # Reset the cerebras_client before each test
        main_module.cerebras_client = None

    @patch('src.main.Cerebras')
    @patch('src.main.cerebras_client', None)
    def test_setup_cerebras_client(self, mock_cerebras: MagicMock) -> None:
        """Test that setup_cerebras_client returns the client correctly."""
        # First call should create the client
        client1 = main_module.setup_cerebras_client()
        mock_cerebras.assert_called_once_with(api_key=API_KEY)
        self.assertIs(client1, main_module.cerebras_client)
        
        # Reset mock for second call verification
        mock_cerebras.reset_mock()
        
        # Second call should return the same client
        client2 = main_module.setup_cerebras_client()
        self.assertIs(client2, client1)
        mock_cerebras.assert_not_called()  # Should not create new client


    @patch('builtins.print')
    @patch('time.sleep')
    def test_print_response(self, mock_sleep: MagicMock, mock_print: MagicMock):
        """Test that print_response prints the response with a delay."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="This is a test response."))]
        mock_response.usage = MagicMock(total_tokens=20)
        mock_response.time_info = MagicMock(total_time=0.5)

        main_module.print_response(mock_response)
        self.assertEqual(mock_print.call_count, 26)
        self.assertEqual(mock_sleep.call_count, 24)

    @patch('src.main.setup_cerebras_client')
    def test_generate_response(self, mock_setup: MagicMock) -> None:
        """Test that generate_response interacts with the Cerebras client correctly."""
        mock_client = MagicMock()
        mock_setup.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Generated text"))]
        mock_client.chat.completions.create.return_value = mock_response

        prompt = "This is a test prompt."
        chat_history = [SYSTEM_MESSAGE]
        response = main_module.generate_response(mock_client, prompt, chat_history)

        mock_client.chat.completions.create.assert_called_once_with(
            messages=chat_history,
            model=MODEL_ID,
        )
        self.assertEqual(response, mock_response)


    def test_get_welcoming_text(self):
        """Test that get_welcome_text returns the expected text."""
        expected_text = """\n🧠 Welcome to Cerebras CLI v1.0.0
╭─────────────────────────────────────────────────╮
│ AI-powered command-line interface              │
│ Model: {MODEL_ID:<38} │
│ Enhanced CLI: {new_cli_status:<30} │
╰─────────────────────────────────────────────────╯

💡 Available modes:
   • Interactive mode (current)
   • Enhanced CLI (run: python -m cerebras_cli.cli.main)
   
🎯 Commands:
   • Type 'exit()' to quit
   • Type '/help' for enhanced features (if available)
   • Type '@filename' to include file content
   
👨‍💻 Made by Addhe Warman Putra (Awan)
""".format(MODEL_ID=MODEL_ID, new_cli_status="✅ Available" if check_new_cli_available() else "❌ Not installed")
        self.assertEqual(main_module.get_welcome_text(), expected_text)

if __name__ == '__main__':
    unittest.main()
